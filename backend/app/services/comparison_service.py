import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from app.models.schemas import (
    BiomarkerDataPoint,
    BiomarkerTrendSeries,
    BiomarkerComparisonItem,
    ReportComparisonResponse,
)
from app.services.glossary_service import medical_glossary_service
from app.services.ollama_service import ollama_service, DEFAULT_OLLAMA_MODEL
from app.core.supabase_client import get_supabase_client, is_supabase_configured

logger = logging.getLogger("medical_ocr.comparison_service")

class ComparisonService:
    """
    Longitudinal Health Biomarker Visualizer & Multi-Report Comparative Diff Engine.
    Aggregates historical lab results into chronological time-series trajectories
    and computes precision delta (Δ) metrics and category shifts between reports.
    """

    def _get_user_records(self, user_id: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Retrieves all reports and structured test results for a given user.
        """
        reports: List[Dict[str, Any]] = []
        test_results: List[Dict[str, Any]] = []

        if is_supabase_configured():
            try:
                supabase = get_supabase_client()
                # 1. Fetch reports
                rep_res = supabase.table("reports").select("*").eq("user_id", user_id).order("report_date", desc=False).execute()
                reports = rep_res.data or []

                # 2. Fetch test results
                tr_res = supabase.table("test_results").select("*").eq("user_id", user_id).execute()
                test_results = tr_res.data or []
            except Exception as e:
                logger.error(f"Error fetching longitudinal records from Supabase: {e}")

        # Fallback to in-memory dev store if Supabase has no records for this user
        import app.api.v1.reports as rep_mod
        dev_reps = [r for r in rep_mod._DEV_REPORTS_DB if r.get("user_id") == user_id]
        dev_trs = [t for t in rep_mod._DEV_TEST_RESULTS_DB if t.get("user_id") == user_id]

        if not reports and dev_reps:
            reports = dev_reps
        if not test_results and dev_trs:
            test_results = dev_trs

        return reports, test_results

    def get_available_biomarkers(self, user_id: str) -> List[str]:
        """
        Returns a sorted, unique list of all normalized biomarker names
        tested across all reports for the user.
        """
        _, test_results = self._get_user_records(user_id)
        names = set()
        for t in test_results:
            name = t.get("normalized_name") or t.get("raw_test_name")
            if name and name.strip():
                names.add(name.strip())
        return sorted(list(names))

    def get_biomarker_trends(
        self,
        user_id: str,
        biomarker_name: Optional[str] = None
    ) -> List[BiomarkerTrendSeries]:
        """
        Aggregates all historical test results for the user into chronological
        time-series trajectory models with range bands and delta calculations.
        """
        reports, test_results = self._get_user_records(user_id)
        report_map = {r["id"]: r for r in reports}

        # Group test results by normalized biomarker name
        grouped: Dict[str, List[BiomarkerDataPoint]] = {}
        unit_map: Dict[str, str] = {}
        ref_min_map: Dict[str, Optional[float]] = {}
        ref_max_map: Dict[str, Optional[float]] = {}

        for it in test_results:
            rep_id = it.get("report_id")
            rep = report_map.get(rep_id, {})
            name = it.get("normalized_name") or it.get("raw_test_name") or "Unknown Biomarker"

            if biomarker_name and name.lower() != biomarker_name.lower():
                continue

            val_num = it.get("value_numeric")
            if val_num is not None:
                try:
                    val_num = float(val_num)
                except (ValueError, TypeError):
                    val_num = None

            unit = it.get("unit")
            ref_min = it.get("ref_min")
            ref_max = it.get("ref_max")
            if ref_min is not None:
                try:
                    ref_min = float(ref_min)
                except (ValueError, TypeError):
                    ref_min = None
            if ref_max is not None:
                try:
                    ref_max = float(ref_max)
                except (ValueError, TypeError):
                    ref_max = None

            # Track unit and reference boundaries
            if unit and name not in unit_map:
                unit_map[name] = unit
            if ref_min is not None and name not in ref_min_map:
                ref_min_map[name] = ref_min
            if ref_max is not None and name not in ref_max_map:
                ref_max_map[name] = ref_max

            data_point = BiomarkerDataPoint(
                report_id=rep_id,
                report_title=rep.get("title", "Lab Report"),
                report_date=rep.get("report_date") or rep.get("created_at", "")[:10],
                value_numeric=val_num,
                value_text=str(it.get("value_text", "")) if it.get("value_text") is not None else None,
                unit=unit,
                reference_range_raw=it.get("reference_range_raw"),
                ref_min=ref_min,
                ref_max=ref_max,
                flag=it.get("flag", "NORMAL"),
            )

            if name not in grouped:
                grouped[name] = []
            grouped[name].append(data_point)

        # Build trajectory series
        series_list: List[BiomarkerTrendSeries] = []

        for name, points in grouped.items():
            # Sort chronologically by date
            points.sort(key=lambda p: (p.report_date or "1970-01-01"))

            # Calculate metrics
            numeric_points = [p for p in points if p.value_numeric is not None]
            latest_val = numeric_points[-1].value_numeric if numeric_points else None
            earliest_val = numeric_points[0].value_numeric if numeric_points else None
            latest_flag = points[-1].flag if points else "NORMAL"
            earliest_flag = points[0].flag if points else "NORMAL"

            delta = None
            delta_pct = None
            trend_dir = "stable"

            if latest_val is not None and earliest_val is not None:
                delta = round(latest_val - earliest_val, 2)
                if abs(earliest_val) > 1e-6:
                    delta_pct = round(((latest_val - earliest_val) / abs(earliest_val)) * 100, 1)

                if latest_flag == "NORMAL" and earliest_flag in ["HIGH", "LOW", "CRITICAL"]:
                    trend_dir = "improving"
                elif latest_flag in ["HIGH", "LOW", "CRITICAL"] and earliest_flag == "NORMAL":
                    trend_dir = "concerning"
                elif abs(delta) < 0.05:
                    trend_dir = "stable"
                elif delta > 0:
                    trend_dir = "elevated"
                else:
                    trend_dir = "declining"

            series = BiomarkerTrendSeries(
                normalized_name=name,
                unit=unit_map.get(name),
                ref_min=ref_min_map.get(name),
                ref_max=ref_max_map.get(name),
                data_points=points,
                latest_value=latest_val,
                latest_flag=latest_flag,
                earliest_value=earliest_val,
                overall_change=delta,
                overall_change_pct=delta_pct,
                trend_direction=trend_dir,
            )
            series_list.append(series)

        # Sort series by biomarker name
        series_list.sort(key=lambda s: s.normalized_name)
        return series_list

    def compare_two_reports(
        self,
        report_a_id: str,
        report_b_id: str,
        user_id: str,
        language: str = "en",
        preferred_model: Optional[str] = None,
    ) -> ReportComparisonResponse:
        """
        Executes precision side-by-side comparative analysis between Report A (Baseline)
        and Report B (Follow-up), computing deltas, status transitions, and AI insights.
        """
        reports, all_test_results = self._get_user_records(user_id)
        report_map = {r["id"]: r for r in reports}

        rep_a = report_map.get(report_a_id)
        rep_b = report_map.get(report_b_id)

        title_a = rep_a.get("title", "Baseline Report") if rep_a else "Report A"
        date_a = rep_a.get("report_date") if rep_a else None
        title_b = rep_b.get("title", "Follow-up Report") if rep_b else "Report B"
        date_b = rep_b.get("report_date") if rep_b else None

        results_a = [t for t in all_test_results if t.get("report_id") == report_a_id]
        results_b = [t for t in all_test_results if t.get("report_id") == report_b_id]

        map_a = { (t.get("normalized_name") or t.get("raw_test_name")): t for t in results_a }
        map_b = { (t.get("normalized_name") or t.get("raw_test_name")): t for t in results_b }

        all_names = sorted(list(set(list(map_a.keys()) + list(map_b.keys()))))

        comparison_items: List[BiomarkerComparisonItem] = []
        improved_cnt = 0
        deteriorated_cnt = 0
        stable_cnt = 0

        for name in all_names:
            item_a = map_a.get(name)
            item_b = map_b.get(name)

            val_a = item_a.get("value_numeric") if item_a else None
            txt_a = item_a.get("value_text") if item_a else None
            flag_a = item_a.get("flag", "NORMAL") if item_a else None

            val_b = item_b.get("value_numeric") if item_b else None
            txt_b = item_b.get("value_text") if item_b else None
            flag_b = item_b.get("flag", "NORMAL") if item_b else None

            unit = (item_b or item_a or {}).get("unit")
            ref_raw = (item_b or item_a or {}).get("reference_range_raw")
            ref_min = (item_b or item_a or {}).get("ref_min")
            ref_max = (item_b or item_a or {}).get("ref_max")

            delta_num = None
            delta_pct = None
            status_shift = "STABLE_NORMAL"
            clinical_interp = ""

            if val_a is not None and val_b is not None:
                delta_num = round(float(val_b) - float(val_a), 2)
                if abs(float(val_a)) > 1e-6:
                    delta_pct = round(((float(val_b) - float(val_a)) / abs(float(val_a))) * 100, 1)

            # Classify status transitions
            if item_a and not item_b:
                status_shift = "NOT_IN_FOLLOWUP"
                clinical_interp = "Tested in baseline report but not included in this follow-up panel."
                stable_cnt += 1
            elif item_b and not item_a:
                status_shift = "NEW_IN_FOLLOWUP"
                clinical_interp = f"New diagnostic marker added in follow-up ({flag_b})."
                if flag_b in ["HIGH", "LOW", "CRITICAL"]:
                    deteriorated_cnt += 1
                else:
                    stable_cnt += 1
            elif flag_a in ["HIGH", "LOW", "CRITICAL"] and flag_b == "NORMAL":
                status_shift = "IMPROVED_TO_NORMAL"
                clinical_interp = f"Improved into normal reference limits ({val_a} -> {val_b} {unit or ''})."
                improved_cnt += 1
            elif flag_a == "NORMAL" and flag_b in ["HIGH", "LOW", "CRITICAL"]:
                status_shift = "DETERIORATED_TO_ABNORMAL"
                clinical_interp = f"Shifted outside reference interval to {flag_b} ({val_a} -> {val_b} {unit or ''})."
                deteriorated_cnt += 1
            elif flag_a in ["HIGH", "LOW", "CRITICAL"] and flag_b in ["HIGH", "LOW", "CRITICAL"]:
                if flag_a != flag_b:
                    status_shift = "INVERTED_ABNORMAL"
                    clinical_interp = f"Polarity inverted from {flag_a} to {flag_b}."
                    deteriorated_cnt += 1
                else:
                    status_shift = "STABLE_ABNORMAL"
                    clinical_interp = f"Remains {flag_b} (Net change: {delta_num or 0} {unit or ''})."
                    stable_cnt += 1
            else:
                status_shift = "STABLE_NORMAL"
                clinical_interp = f"Remains within normal physiological bounds ({val_a} -> {val_b} {unit or ''})."
                stable_cnt += 1

            comparison_items.append(
                BiomarkerComparisonItem(
                    normalized_name=name,
                    unit=unit,
                    ref_min=ref_min,
                    ref_max=ref_max,
                    reference_range_raw=ref_raw,
                    report_a_value=val_a,
                    report_a_text=txt_a,
                    report_a_flag=flag_a,
                    report_b_value=val_b,
                    report_b_text=txt_b,
                    report_b_flag=flag_b,
                    delta_numeric=delta_num,
                    delta_pct=delta_pct,
                    status_shift=status_shift,
                    clinical_interpretation=clinical_interp,
                )
            )

        # Generate AI Comparative Summary
        ai_summary, model_used, is_mock = self._generate_ai_comparison_summary(
            title_a=title_a,
            date_a=date_a,
            title_b=title_b,
            date_b=date_b,
            items=comparison_items,
            improved_cnt=improved_cnt,
            deteriorated_cnt=deteriorated_cnt,
            stable_cnt=stable_cnt,
            language=language,
            preferred_model=preferred_model,
        )

        return ReportComparisonResponse(
            report_a_id=report_a_id,
            report_a_title=title_a,
            report_a_date=date_a,
            report_b_id=report_b_id,
            report_b_title=title_b,
            report_b_date=date_b,
            total_compared=len(comparison_items),
            improved_count=improved_cnt,
            deteriorated_count=deteriorated_cnt,
            stable_count=stable_cnt,
            items=comparison_items,
            ai_summary=ai_summary,
            model_used=model_used,
            is_mock_fallback=is_mock,
        )

    def _generate_ai_comparison_summary(
        self,
        title_a: str,
        date_a: Optional[str],
        title_b: str,
        date_b: Optional[str],
        items: List[BiomarkerComparisonItem],
        improved_cnt: int,
        deteriorated_cnt: int,
        stable_cnt: int,
        language: str = "en",
        preferred_model: Optional[str] = None,
    ) -> Tuple[str, str, bool]:
        """
        Generates grounded comparative AI summary between baseline and follow-up reports.
        """
        # Format delta table for prompt
        table_text = ""
        for it in items:
            table_text += (
                f"- {it.normalized_name}: Baseline={it.report_a_value} ({it.report_a_flag}) -> "
                f"Follow-up={it.report_b_value} ({it.report_b_flag}) | "
                f"Δ={it.delta_numeric} {it.unit or ''} ({it.delta_pct or 0}%) | "
                f"Shift={it.status_shift}\n"
            )

        system_prompt = (
            "You are a Senior Clinical Data Communicator. Explain the changes between a patient's baseline "
            "and follow-up laboratory reports in clear, empathetic, non-diagnostic terms.\n\n"
            "RULES:\n"
            "1. Ground every claim in the provided delta table.\n"
            "2. Highlight biomarkers that improved into normal range.\n"
            "3. Highlight biomarkers that deteriorated or remain elevated with exact delta numbers.\n"
            "4. Provide 3 thoughtful questions for the patient's next clinical review."
        )

        user_prompt = (
            f"BASELINE REPORT: {title_a} ({date_a or 'Baseline'})\n"
            f"FOLLOW-UP REPORT: {title_b} ({date_b or 'Follow-up'})\n\n"
            f"MEASURED DELTA TABLE:\n{table_text}\n"
            "Please generate a 3-part summary:\n"
            "1. Overview of Trajectory\n"
            "2. Positive Progress & Areas of Vigilance\n"
            "3. Questions for Doctor Consultation"
        )

        ollama_available, models = ollama_service.check_availability()
        if ollama_available:
            model_to_use = preferred_model or (models[0] if models else DEFAULT_OLLAMA_MODEL)
            try:
                res = ollama_service.generate(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    model=model_to_use,
                    temperature=0.2,
                )
                if res and res.strip():
                    return res.strip(), model_to_use, False
            except Exception as e:
                logger.warning(f"Ollama comparison generation failed ({e}); using fallback.")

        # Fallback deterministic comparative summary
        improved_items = [it for it in items if it.status_shift == "IMPROVED_TO_NORMAL"]
        deteriorated_items = [it for it in items if it.status_shift == "DETERIORATED_TO_ABNORMAL" or it.status_shift == "INVERTED_ABNORMAL"]
        notable_changes = [it for it in items if it.delta_pct is not None and abs(it.delta_pct) >= 15.0]

        overview = (
            f"Comparative analysis between '{title_a}' and '{title_b}' covers {len(items)} diagnostic biomarker(s). "
            f"Overall, {improved_cnt} biomarker(s) showed positive normalization, {deteriorated_cnt} biomarker(s) showed new or worsening deviations, "
            f"and {stable_cnt} remained stable."
        )

        improved_str = ""
        if improved_items:
            improved_str = "### Positive Improvements:\n" + "\n".join([
                f"- **{it.normalized_name}**: Normalized from {it.report_a_value} ({it.report_a_flag}) to **{it.report_b_value} {it.unit or ''}** (Normal)."
                for it in improved_items
            ]) + "\n\n"

        deteriorated_str = ""
        if deteriorated_items:
            deteriorated_str = "### Areas Requiring Attention:\n" + "\n".join([
                f"- **{it.normalized_name}**: Shifted from {it.report_a_value} to **{it.report_b_value} {it.unit or ''}** (Flagged as **{it.report_b_flag}** | Δ: {it.delta_numeric} {it.unit or ''})."
                for it in deteriorated_items
            ]) + "\n\n"

        notable_str = ""
        if notable_changes:
            notable_str = "### Significant Percentage Shifts (≥15% Change):\n" + "\n".join([
                f"- **{it.normalized_name}**: Net change of **{it.delta_pct}%** ({it.report_a_value} -> {it.report_b_value} {it.unit or ''})."
                for it in notable_changes[:4]
            ]) + "\n\n"

        doc_questions = (
            "### Recommended Doctor Discussion Points:\n"
            "1. *'What factors contributed most to the changes observed between these two reports?'*\n"
            "2. *'Should we adjust any current therapies, lifestyle habits, or medications?'*\n"
            "3. *'When would you like to schedule our next follow-up panel?'*"
        )

        full_summary = f"{overview}\n\n{improved_str}{deteriorated_str}{notable_str}{doc_questions}"
        return full_summary, "deterministic-clinical-comparison-fallback", True

# Global singleton comparison service
comparison_service = ComparisonService()
