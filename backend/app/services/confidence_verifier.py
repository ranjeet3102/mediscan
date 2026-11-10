import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from app.services.normalizer import (
    CanonicalBiomarker,
    NormalizationResult,
    biomarker_normalizer,
)

logger = logging.getLogger("medical_ocr.confidence_verifier")

@dataclass
class VerificationResult:
    composite_confidence: float  # 0.0 to 100.0
    ocr_confidence: float
    name_match_confidence: float
    unit_confidence: float
    sanity_confidence: float
    verification_status: str  # "verified", "needs_review", "flagged_outlier", "user_corrected"
    is_outlier: bool
    verification_reason: str

class ConfidenceVerificationEngine:
    """
    Confidence & Sanity Verification Engine for Clinical Diagnostics.
    Computes a multi-factor composite verification score combining:
    1. Base OCR character confidence
    2. Taxonomy normalization & alias match score
    3. Unit concordance with medical lexicons
    4. Biological and physiological range plausibility
    """

    def __init__(
        self,
        weight_ocr: float = 0.35,
        weight_name: float = 0.25,
        weight_unit: float = 0.20,
        weight_sanity: float = 0.20,
    ):
        self.w_ocr = weight_ocr
        self.w_name = weight_name
        self.w_unit = weight_unit
        self.w_sanity = weight_sanity

    def evaluate_unit_concordance(
        self,
        unit: Optional[str],
        canonical_info: Optional[CanonicalBiomarker]
    ) -> Tuple[float, str]:
        """
        Evaluates whether the extracted measurement unit is compatible with the biomarker.
        """
        if not unit:
            if canonical_info and canonical_info.standard_units:
                return 60.0, "Unit missing in report line"
            return 75.0, "Unit omitted or not applicable"

        if not canonical_info or not canonical_info.standard_units:
            return 80.0, f"Unregistered test unit: {unit}"

        def norm_u(u_str: str) -> str:
            return (
                u_str.replace("µ", "u")
                .replace("×", "x")
                .replace("³", "^3")
                .replace("⁶", "^6")
                .replace(" ", "")
                .strip()
                .lower()
            )

        clean_unit = norm_u(unit)
        std_units_clean = [norm_u(u) for u in canonical_info.standard_units]

        if clean_unit in std_units_clean:
            return 100.0, f"Standard unit confirmed: {unit}"

        # Check partial prefix / casing matches
        for su in std_units_clean:
            if clean_unit in su or su in clean_unit:
                return 95.0, f"Compatible unit variant: {unit}"

        # Unit mismatch with known standard
        return 30.0, f"Unit '{unit}' differs from typical expected units ({', '.join(canonical_info.standard_units)})"

    def evaluate_physiological_sanity(
        self,
        value_numeric: Optional[float],
        value_text: Optional[str],
        canonical_info: Optional[CanonicalBiomarker]
    ) -> Tuple[float, bool, str]:
        """
        Checks whether the numerical reading is physiologically plausible in living humans.
        Detects OCR mis-segmentation artifacts (e.g. missing decimal point: 13.5 -> 135).
        """
        if value_numeric is None:
            # Qualitative or text-based result
            if value_text:
                return 90.0, False, "Qualitative test result"
            return 60.0, False, "No numerical reading detected"

        # Check negative value (almost all blood lab biomarkers cannot be negative)
        if value_numeric < 0:
            return 0.0, True, f"Negative value ({value_numeric}) is physiologically impossible."

        if not canonical_info:
            return 85.0, False, "Value plausible (generic test bounds)"

        p_min = canonical_info.plausible_min
        p_max = canonical_info.plausible_max

        # Adaptive sanity check for multi-scale biomarkers (Platelets and WBC)
        c_name = canonical_info.canonical_name.lower()
        if "platelet" in c_name:
            # If in thousands format (150-450) or lakhs (1.5-4.5) or whole cells (150000-450000)
            if value_numeric <= 2000.0:
                p_min = 2.0
                p_max = 2000.0
            else:
                p_min = 2000.0
                p_max = 2500000.0
        elif "wbc" in c_name or "leucocyte" in c_name or "leukocyte" in c_name:
            if value_numeric <= 150.0:
                p_min = 0.5
                p_max = 150.0
            else:
                p_min = 200.0
                p_max = 200000.0

        # Check physiological bounds
        if value_numeric < p_min:
            # Below absolute minimum possible
            if value_numeric == 0 and p_min > 0:
                return 10.0, True, f"Zero value is implausible for {canonical_info.canonical_name} (min plausible: {p_min})."
            return 20.0, True, f"Value {value_numeric} is below human physiological lower bound ({p_min}). Check OCR decimal point."

        if value_numeric > p_max:
            # Exceeds maximum plausible for human survival
            return 0.0, True, f"Value {value_numeric} exceeds physiological limit ({p_max}) for {canonical_info.canonical_name}. Likely OCR misread or decimal shift."

        # Inside physiological bounds
        return 100.0, False, "Within valid human physiological bounds."

    def verify(
        self,
        raw_test_name: str,
        value_numeric: Optional[float] = None,
        value_text: Optional[str] = None,
        unit: Optional[str] = None,
        reference_range_raw: Optional[str] = None,
        ocr_confidence: float = 95.0,
        current_status: Optional[str] = None,
    ) -> VerificationResult:
        """
        Calculates composite verification score and assigns verification status.
        """
        # If user has explicitly manually corrected this value, preserve user_corrected
        if current_status == "user_corrected":
            return VerificationResult(
                composite_confidence=100.0,
                ocr_confidence=ocr_confidence,
                name_match_confidence=100.0,
                unit_confidence=100.0,
                sanity_confidence=100.0,
                verification_status="user_corrected",
                is_outlier=False,
                verification_reason="Manually reviewed and verified by user.",
            )

        # 1. Normalize test name
        norm_result = biomarker_normalizer.normalize(raw_test_name)
        name_conf = norm_result.confidence_score
        canonical_info = norm_result.canonical_info

        # 2. Evaluate Unit
        unit_conf, unit_reason = self.evaluate_unit_concordance(unit, canonical_info)

        # 3. Evaluate Sanity & Outlier bounds
        sanity_conf, is_outlier, sanity_reason = self.evaluate_physiological_sanity(
            value_numeric, value_text, canonical_info
        )

        # 4. Compute Weighted Composite Score
        composite = (
            (self.w_ocr * ocr_confidence)
            + (self.w_name * name_conf)
            + (self.w_unit * unit_conf)
            + (self.w_sanity * sanity_conf)
        )
        composite = round(max(0.0, min(100.0, composite)), 1)

        # 5. Determine Final Verification Status
        reasons = []
        if is_outlier:
            verification_status = "needs_review"
            reasons.append(sanity_reason)
        elif composite >= 80.0:
            verification_status = "verified"
            reasons.append("High multi-factor confidence across OCR, test terminology, and physiological bounds.")
        else:
            verification_status = "needs_review"
            if ocr_confidence < 80:
                reasons.append(f"Low OCR confidence ({ocr_confidence:.1f}%).")
            if name_conf < 80:
                reasons.append(f"Non-standard test name match ({name_conf:.1f}%).")
            if unit_conf < 70:
                reasons.append(unit_reason)
            if sanity_conf < 70:
                reasons.append(sanity_reason)

        final_reason = " ".join(reasons) if reasons else "Verified."

        return VerificationResult(
            composite_confidence=composite,
            ocr_confidence=ocr_confidence,
            name_match_confidence=name_conf,
            unit_confidence=unit_conf,
            sanity_confidence=sanity_conf,
            verification_status=verification_status,
            is_outlier=is_outlier,
            verification_reason=final_reason,
        )

# Global singleton verification engine
confidence_engine = ConfidenceVerificationEngine()
