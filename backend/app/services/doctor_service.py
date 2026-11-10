import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

from app.models.schemas import (
    DoctorQuestion,
    DoctorSummaryResponse,
)
from app.services.glossary_service import medical_glossary_service
from app.services.comparison_service import comparison_service
from app.services.ollama_service import ollama_service, DEFAULT_OLLAMA_MODEL

logger = logging.getLogger("medical_ocr.doctor_service")

class DoctorService:
    """
    Doctor Support Suite & Multilingual Consultation Generator (Phase 12).
    Synthesizes complex laboratory reports into a concise, print-ready 1-page clinical brief
    and generates prioritized, grounded doctor consultation questions for patient empowerment.
    """

    def generate_doctor_summary(
        self,
        report_id: str,
        user_id: str,
        report_title: str,
        report_date: Optional[str],
        test_results: List[Dict[str, Any]],
        patient_email: Optional[str] = None,
        language: str = "en",
        preferred_model: Optional[str] = None,
    ) -> DoctorSummaryResponse:
        """
        Generates a comprehensive 1-page Doctor Visit Summary and prioritized consultation questions.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        if not test_results:
            return DoctorSummaryResponse(
                report_id=report_id,
                report_title=report_title,
                report_date=report_date,
                patient_email=patient_email,
                language=language,
                executive_clinical_summary="No structured clinical test results are currently associated with this document. Please complete OCR and clinical extraction.",
                abnormal_findings_count=0,
                total_findings_count=0,
                key_abnormalities=[],
                key_normal_findings=[],
                longitudinal_shifts=[],
                doctor_questions=[
                    DoctorQuestion(
                        category="Diagnostic Review",
                        question="Please review the original physical laboratory report document.",
                        context="No structured parameters parsed.",
                        priority="general",
                    )
                ],
                clinical_notes_for_physician="Physical report review required.",
                model_used="none",
                is_mock_fallback=True,
                generated_at=now_iso,
            )

        # 1. Categorize findings
        abnormal_items: List[Dict[str, Any]] = []
        normal_items: List[Dict[str, Any]] = []

        for it in test_results:
            name = it.get("normalized_name") or it.get("raw_test_name") or "Biomarker"
            val = str(it.get("value_numeric", it.get("value_text", "N/A")))
            unit = it.get("unit") or ""
            ref = it.get("reference_range_raw") or (
                f"{it.get('ref_min')} - {it.get('ref_max')}"
                if it.get("ref_min") is not None and it.get("ref_max") is not None
                else "N/A"
            )
            flag = it.get("flag", "NORMAL")

            g_entry = medical_glossary_service.get_by_name(name)
            meaning = g_entry.patient_friendly_summary if g_entry else "Diagnostic biomarker."
            organs = g_entry.organs_involved if g_entry else "General Physiology"

            item_dict = {
                "name": name,
                "value": val,
                "unit": unit,
                "reference_range": ref,
                "flag": flag,
                "organs": organs,
                "clinical_note": meaning,
            }

            if flag in ["HIGH", "LOW", "CRITICAL"]:
                abnormal_items.append(item_dict)
            else:
                normal_items.append(item_dict)

        # 2. Check longitudinal trajectory context
        longitudinal_shifts: List[Dict[str, Any]] = []
        try:
            trends = comparison_service.get_biomarker_trends(user_id=user_id)
            for t in trends:
                if len(t.data_points) >= 2 and t.overall_change is not None:
                    longitudinal_shifts.append({
                        "biomarker": t.normalized_name,
                        "earliest": t.earliest_value,
                        "latest": t.latest_value,
                        "unit": t.unit or "",
                        "delta": t.overall_change,
                        "delta_pct": t.overall_change_pct,
                        "direction": t.trend_direction,
                    })
        except Exception as e:
            logger.warning(f"Could not retrieve longitudinal trends for doctor summary: {e}")

        # 3. Generate Prioritized Doctor Questions
        doctor_questions = self._generate_doctor_questions(
            report_title=report_title,
            abnormal_items=abnormal_items,
            longitudinal_shifts=longitudinal_shifts,
            language=language,
        )

        # 4. Generate Clinical Summary Text (LLM or Deterministic Fallback)
        executive_summary, physician_notes, model_used, is_mock = self._generate_clinical_text(
            report_title=report_title,
            report_date=report_date,
            abnormal_items=abnormal_items,
            normal_items=normal_items,
            longitudinal_shifts=longitudinal_shifts,
            language=language,
            preferred_model=preferred_model,
        )

        return DoctorSummaryResponse(
            report_id=report_id,
            report_title=report_title,
            report_date=report_date,
            patient_email=patient_email,
            language=language,
            executive_clinical_summary=executive_summary,
            abnormal_findings_count=len(abnormal_items),
            total_findings_count=len(test_results),
            key_abnormalities=abnormal_items,
            key_normal_findings=normal_items[:8],
            longitudinal_shifts=longitudinal_shifts[:5],
            doctor_questions=doctor_questions,
            clinical_notes_for_physician=physician_notes,
            model_used=model_used,
            is_mock_fallback=is_mock,
            generated_at=now_iso,
        )

    def _generate_doctor_questions(
        self,
        report_title: str,
        abnormal_items: List[Dict[str, Any]],
        longitudinal_shifts: List[Dict[str, Any]],
        language: str = "en"
    ) -> List[DoctorQuestion]:
        """
        Generates 4-6 prioritized, patient-empowering questions tailored to their specific findings.
        """
        questions: List[DoctorQuestion] = []

        # High priority: Out-of-range findings
        if abnormal_items:
            for it in abnormal_items[:3]:
                if language == "ta":
                    q = f"எனது {it['name']} அளவு {it['value']} {it['unit']} ஆக உள்ளது (சாதாரண அளவு: {it['reference_range']}). இதற்கு என்ன காரணம்?"
                    ctx = f"{it['name']} ஆனது {it['flag']} நிலையில் உள்ளது."
                elif language == "hi":
                    q = f"मेरी {it['name']} का स्तर {it['value']} {it['unit']} दर्ज किया गया है (सामान्य सीमा: {it['reference_range']})। इसका क्या कारण हो सकता है?"
                    ctx = f"{it['name']} का स्तर {it['flag']} दर्ज है।"
                else:
                    q = f"My {it['name']} was measured at {it['value']} {it['unit']} (standard range: {it['reference_range']}). What factors could be contributing to this level?"
                    ctx = f"{it['name']} is flagged as {it['flag']}."

                questions.append(
                    DoctorQuestion(
                        category="Out-of-Range Follow-up",
                        question=q,
                        context=ctx,
                        priority="high",
                    )
                )

        # Medium priority: Longitudinal Shifts
        if longitudinal_shifts:
            top_shift = longitudinal_shifts[0]
            if language == "ta":
                q = f"முந்தைய அறிக்கையுடன் ஒப்பிடும்போது எனது {top_shift['biomarker']} அளவு {top_shift['delta']} {top_shift['unit']} மாறியுள்ளது. இந்த மாற்றத்திற்கு என்ன காரணம்?"
                ctx = f"நீண்டகால போக்கு: {top_shift['direction']}"
            elif language == "hi":
                q = f"पिछली रिपोर्ट की तुलना में मेरी {top_shift['biomarker']} में {top_shift['delta']} {top_shift['unit']} का बदलाव देखा गया है। क्या यह सामान्य है?"
                ctx = f"दीर्घकालिक बदलाव: {top_shift['direction']}"
            else:
                q = f"Compared to my previous test, my {top_shift['biomarker']} changed by {top_shift['delta']} {top_shift['unit']} ({top_shift['delta_pct']}%). Is this shift clinically significant?"
                ctx = f"Historical trend trajectory: {top_shift['direction']}."

            questions.append(
                DoctorQuestion(
                    category="Longitudinal Trajectory",
                    question=q,
                    context=ctx,
                    priority="medium",
                )
            )

        # General / Therapy & Retesting
        if language == "ta":
            questions.append(
                DoctorQuestion(
                    category="Lifestyle & Diet",
                    question="இந்த முடிவுகளின் அடிப்படையில் எனது உணவுமுறை அல்லது உடற்பயிற்சியில் ஏதேனும் மாற்றங்களை பரிந்துரைக்கிறீர்களா?",
                    context="ஆரோக்கிய வாழ்க்கை முறை வழிகாட்டுதல்.",
                    priority="general",
                )
            )
            questions.append(
                DoctorQuestion(
                    category="Retesting Timeline",
                    question="இந்த அளவுருக்களை மீண்டும் எப்போது பரிசோதிக்க வேண்டும்?",
                    context="தொடர் மருத்துவ கண்காணிப்பு.",
                    priority="general",
                )
            )
        elif language == "hi":
            questions.append(
                DoctorQuestion(
                    category="Lifestyle & Diet",
                    question="इन परिणामों के आधार पर क्या आप मेरे खान-पान या जीवनशैली में किसी बदलाव की सलाह देंगे?",
                    context="जीवनशैली और पोषण संबंधी मार्गदर्शन।",
                    priority="general",
                )
            )
            questions.append(
                DoctorQuestion(
                    category="Retesting Timeline",
                    question="मुझे इन परीक्षणों को दोबारा कब दोहराना चाहिए?",
                    context="अनुवर्ती जांच योजना।",
                    priority="general",
                )
            )
        else:
            questions.append(
                DoctorQuestion(
                    category="Lifestyle & Diet",
                    question="Are there specific dietary or lifestyle modifications you would recommend based on these findings?",
                    context="Evidence-based nutritional and activity guidance.",
                    priority="general",
                )
            )
            questions.append(
                DoctorQuestion(
                    category="Retesting Timeline",
                    question="When would you recommend scheduling a follow-up test to monitor these parameters?",
                    context="Follow-up care and re-evaluation timeline.",
                    priority="general",
                )
            )

        return questions

    def _generate_clinical_text(
        self,
        report_title: str,
        report_date: Optional[str],
        abnormal_items: List[Dict[str, Any]],
        normal_items: List[Dict[str, Any]],
        longitudinal_shifts: List[Dict[str, Any]],
        language: str = "en",
        preferred_model: Optional[str] = None,
    ) -> Tuple[str, str, str, bool]:
        """
        Generates grounded clinical executive summary and physician consultation notes.
        """
        total = len(abnormal_items) + len(normal_items)

        # Check local Ollama daemon
        ollama_available, models = ollama_service.check_availability()
        if ollama_available:
            chosen_model = preferred_model or (models[0] if models else DEFAULT_OLLAMA_MODEL)
            prompt = (
                f"REPORT: {report_title} ({report_date or 'Recent'})\n"
                f"TOTAL BIOMARKERS: {total}\n"
                f"ABNORMAL FINDINGS: {[f'{it['name']}={it['value']} {it['unit']} (Ref: {it['reference_range']})' for it in abnormal_items]}\n"
                f"NORMAL FINDINGS: {[f'{it['name']}={it['value']} {it['unit']}' for it in normal_items[:5]]}\n\n"
                "Please generate a concise, 2-paragraph Clinical Brief for a doctor consultation in plain English."
            )
            try:
                res = ollama_service.generate(
                    prompt=prompt,
                    system_prompt="You are a clinical communications assistant. Summarize lab findings concisely.",
                    model=chosen_model,
                    temperature=0.2,
                )
                if res and res.strip():
                    return res.strip(), "Review above diagnostic findings with patient history.", chosen_model, False
            except Exception as e:
                logger.warning(f"Ollama doctor summary generation failed: {e}")

        # Deterministic multilingual fallback
        if language == "ta":
            if abnormal_items:
                abn_names = ", ".join([f"{it['name']} ({it['value']} {it['unit']})" for it in abnormal_items[:3]])
                exec_summary = (
                    f"மருத்துவ அறிக்கை '{report_title}' ({report_date or 'சமீபத்திய'}) ஆய்வில் மொத்தம் {total} சோதனைகள் மதிப்பாய்வு செய்யப்பட்டன. "
                    f"இதில் {len(abnormal_items)} சோதனைகள் சாதாரண வரம்பிற்கு வெளியே உள்ளன: {abn_names}. "
                    f"மீதமுள்ள {len(normal_items)} சோதனைகள் ஆரோக்கியமான வரம்பிற்குள் உள்ளன."
                )
            else:
                exec_summary = (
                    f"மருத்துவ அறிக்கை '{report_title}' ({report_date or 'சமீபத்திய'}) ஆய்வில் உள்ள அனைத்து {total} சோதனைகளும் "
                    "சாதாரண வரம்பிற்குள் உள்ளன. நிலையான உடலியல் செயல்பாட்டை பிரதிபலிக்கிறது."
                )
            physician_notes = "மருத்துவ வரலாற்றுடன் முடிவுகளை மதிப்பாய்வு செய்து ஆலோசனை வழங்கவும்."

        elif language == "hi":
            if abnormal_items:
                abn_names = ", ".join([f"{it['name']} ({it['value']} {it['unit']})" for it in abnormal_items[:3]])
                exec_summary = (
                    f"मेडिकल रिपोर्ट '{report_title}' ({report_date or 'हालिया'}) में कुल {total} परीक्षणों का मूल्यांकन किया गया। "
                    f"इनमें से {len(abnormal_items)} परीक्षण सामान्य सीमा से बाहर हैं: {abn_names}। "
                    f"शेष {len(normal_items)} परीक्षण पूरी तरह से सामान्य सीमा के भीतर हैं।"
                )
            else:
                exec_summary = (
                    f"मेडिकल रिपोर्ट '{report_title}' ({report_date or 'हालिया'}) में सभी {total} परीक्षण "
                    "सामान्य संदर्भ सीमा के भीतर हैं।"
                )
            physician_notes = "रोगी के नैदानिक इतिहास और लक्षणों के साथ परिणामों की समीक्षा करें।"

        else:
            if abnormal_items:
                abn_names = ", ".join([f"{it['name']} ({it['value']} {it['unit']})" for it in abnormal_items[:4]])
                exec_summary = (
                    f"Clinical overview for '{report_title}' ({report_date or 'Recent Panel'}): Out of {total} evaluated diagnostic biomarkers, "
                    f"{len(abnormal_items)} parameter(s) showed deviations outside standard reference bounds ({abn_names}). "
                    f"{len(normal_items)} parameter(s) remain firmly within healthy physiological limits."
                )
            else:
                exec_summary = (
                    f"Clinical overview for '{report_title}' ({report_date or 'Recent Panel'}): All {total} evaluated biomarkers "
                    "are currently within standard reference intervals, reflecting stable physiological baseline function."
                )
            physician_notes = "Cross-reference identified deviations with patient clinical history, medication regimen, and symptoms."

        return exec_summary, physician_notes, "deterministic-clinical-doctor-brief", True

# Global singleton doctor service
doctor_service = DoctorService()
