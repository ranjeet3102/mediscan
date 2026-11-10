import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel

from app.services.normalizer import biomarker_normalizer
from app.services.confidence_verifier import confidence_engine

logger = logging.getLogger("medical_ocr.parser")

# ==========================================
# Known Medical Units Lexicon
# ==========================================
COMMON_UNITS = [
    # Blood / Cell counts
    "/µL", "/uL", "µL", "uL", "/mcL", "cells/mcL", "cells/cumm", "/cumm", "cumm", "lakhs/cumm", "thou/cumm",
    "×10³/µL", "x10³/µL", "×10^3/µL", "x10^3/uL", "10^3/uL", "10³/µL", "10^3/mcL", "x10^3/mcL",
    "10^6/uL", "10^6/mcL", "x10⁶/µL", "×10⁶/µL", "mill/cumm",
    # Concentrations & general
    "g/dL", "gm/dL", "mg/dL", "mg/L", "g/L", "ug/dL", "mcg/dL", "µg/dL", "ug/mL", "mcg/mL", "µg/mL", "ng/dL", "ng/mL", "pg/mL",
    # Hormones & Enzymes
    "mIU/L", "uIU/mL", "µIU/mL", "mIU/mL", "uIU/L", "µIU/L", "IU/L", "U/L", "IU/mL", "AU/mL",
    # Molar
    "mmol/L", "pmol/L", "nmol/L", "umol/L", "µmol/L", "mEq/L",
    # Indices & percentages
    "%", "fL", "fl", "pg", "mm/hr", "ratio", "/hpf", "index", "sec", "seconds"
]

# Known diagnostic flags in reports
FLAG_TOKENS = {
    "LOW": "LOW",
    "HIGH": "HIGH",
    "CRITICAL": "CRITICAL",
    "NORMAL": "NORMAL",
    "ABNORMAL": "HIGH",
    "—": "NORMAL",
    "-": "NORMAL",
    "--": "NORMAL",
    "NIL": "NORMAL",
    "NEGATIVE": "NORMAL",
    "POSITIVE": "HIGH",
    "NON-REACTIVE": "NORMAL",
    "REACTIVE": "HIGH",
}

def normalize_unit_str(s: str) -> str:
    """Normalizes Unicode characters in unit strings for robust comparison."""
    return (
        s.replace("µ", "u")
        .replace("×", "x")
        .replace("³", "^3")
        .replace("⁶", "^6")
        .replace(" ", "")
        .strip()
        .lower()
    )

def parse_number_token(token: str) -> Optional[float]:
    """
    Parses a string into a float, properly distinguishing thousands separators
    (e.g. '7,800' -> 7800.0, '4,000' -> 4000.0) from European decimals (e.g. '12,1' -> 12.1).
    """
    clean = token.strip("<>≤≥").strip()
    if not clean:
        return None
    # Standard thousands comma: 7,800 or 150,000 or 1,250.5
    if re.match(r"^\d{1,3}(?:,\d{3})+(?:\.\d+)?$", clean):
        clean = clean.replace(",", "")
    elif re.match(r"^\d+,\d{1,2}$", clean):
        # European decimal comma: 12,1 -> 12.1
        clean = clean.replace(",", ".")
    else:
        # Strip stray commas
        clean = clean.replace(",", "")
    try:
        return float(clean)
    except ValueError:
        return None

# Regex pattern for unit matching
UNIT_REGEX_STR = r"(?:" + "|".join([re.escape(u) for u in COMMON_UNITS]) + r")"

@dataclass
class ParsedReferenceRange:
    raw: str
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None

@dataclass
class ExtractedTestResult:
    raw_test_name: str
    normalized_name: str
    category: str = "General Diagnostic"
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    reference_range_raw: Optional[str] = None
    ref_min: Optional[float] = None
    ref_max: Optional[float] = None
    flag: str = "NORMAL"  # NORMAL, LOW, HIGH, CRITICAL, UNCERTAIN
    ocr_confidence: float = 95.0
    composite_confidence: float = 95.0
    verification_status: str = "verified"
    verification_reason: str = "Verified"
    is_outlier: bool = False

class MedicalReportParser:
    """
    Regex & layout-aware parser for clinical diagnostic laboratory reports.
    Extracts structured parameters across diverse panels:
    - Complete Blood Counts (CBC)
    - Lipid Profiles
    - Thyroid Profiles (T3, T4, TSH)
    - Liver Function Tests (LFT)
    - Kidney Function Tests (KFT / RFT)
    - Diabetes & Glycemic Panels (HbA1c, FBS, PPBS)
    - Metabolic & Electrolytes
    """

    def __init__(self):
        # Multi-pattern regex extractors supporting comma-separated numbers (e.g. 4,000 - 11,000)
        num_re = r"(?:\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)"
        self.range_pattern_between = re.compile(
            rf"({num_re})\s*(?:-|–|—|to)\s*({num_re})", re.IGNORECASE
        )
        self.range_pattern_less_than = re.compile(
            rf"(?:<|≤|less\s+than|upto|up\s+to|below)\s*({num_re})", re.IGNORECASE
        )
        self.range_pattern_greater_than = re.compile(
            rf"(?:>|≥|greater\s+than|above)\s*({num_re})", re.IGNORECASE
        )

        self.tabular_regex = re.compile(
            r"^\s*([A-Za-z0-9\s\(\)/_\-\.,]+?)\s{2,}"                # Test Name
            rf"([<>≤≥]?\s*{num_re}|[A-Za-z]+)\s*"                    # Numeric or text value
            r"(" + UNIT_REGEX_STR + r")?\s*"                        # Optional Unit
            rf"((?:[<>≤≥]?\s*{num_re}\s*(?:-|–|—|to)?\s*{num_re}?|" # Range
            r"(?:Negative|Positive|Non-Reactive|Normal|Nil))?)",
            re.IGNORECASE | re.MULTILINE
        )

    def parse_reference_range(self, raw_range: str) -> ParsedReferenceRange:
        """
        Parses reference range string into numeric min and max bounds.
        Cleans trailing flag words/dashes (e.g. "13.0 - 17.0 LOW" -> "13.0 - 17.0").
        Supports:
        - "12.0 - 16.0"      -> min=12.0, max=16.0
        - "4,000 - 11,000"   -> min=4000.0, max=11000.0
        - "< 200"            -> max=200.0
        - "> 60"             -> min=60.0
        - "70-99"            -> min=70.0, max=99.0
        """
        if not raw_range:
            return ParsedReferenceRange(raw="")

        clean = raw_range.strip()
        # Strip trailing flag or dash characters
        clean = re.sub(r"[\s\-—–]+$", "", clean)
        clean = re.sub(r"\s*(?:LOW|HIGH|NORMAL|CRITICAL|ABNORMAL|UNCERTAIN|NIL|NEG|POS)\s*$", "", clean, flags=re.I).strip()
        # Normalize any dash/en-dash/em-dash between numbers to clean spaced hyphen
        clean = re.sub(r"\s*[–—\-]\s*", " - ", clean)

        # Check "min - max"
        m_between = self.range_pattern_between.search(clean)
        if m_between:
            vmin = parse_number_token(m_between.group(1))
            vmax = parse_number_token(m_between.group(2))
            if vmin is not None or vmax is not None:
                return ParsedReferenceRange(raw=clean, ref_min=vmin, ref_max=vmax)

        # Check "< max"
        m_lt = self.range_pattern_less_than.search(clean)
        if m_lt:
            vmax = parse_number_token(m_lt.group(1))
            if vmax is not None:
                return ParsedReferenceRange(raw=clean, ref_max=vmax)

        # Check "> min"
        m_gt = self.range_pattern_greater_than.search(clean)
        if m_gt:
            vmin = parse_number_token(m_gt.group(1))
            if vmin is not None:
                return ParsedReferenceRange(raw=clean, ref_min=vmin)

        return ParsedReferenceRange(raw=clean)

    def determine_flag(
        self,
        value_numeric: Optional[float],
        value_text: Optional[str],
        ref_min: Optional[float],
        ref_max: Optional[float]
    ) -> str:
        """
        Calculates diagnostic status flag: NORMAL, LOW, HIGH, CRITICAL, or UNCERTAIN.
        """
        if value_numeric is not None:
            if ref_min is not None and value_numeric < ref_min:
                if ref_min > 0 and value_numeric < (ref_min * 0.5):
                    return "CRITICAL"
                return "LOW"
            elif ref_max is not None and value_numeric > ref_max:
                if ref_max > 0 and value_numeric > (ref_max * 2.0):
                    return "CRITICAL"
                return "HIGH"
            elif ref_min is not None or ref_max is not None:
                return "NORMAL"

        if value_text:
            text_upper = value_text.upper()
            if any(w in text_upper for w in ["POSITIVE", "REACTIVE", "HIGH", "ABNORMAL"]):
                return "HIGH"
            elif any(w in text_upper for w in ["NEGATIVE", "NON-REACTIVE", "NORMAL", "NIL"]):
                return "NORMAL"

        return "NORMAL"

    def parse_line_flexible(self, line: str, ocr_confidence: float = 95.0) -> Optional[ExtractedTestResult]:
        """
        Flexible line parser for clinical lab report lines.
        Handles:
        - Multi-space tabular: "Haemoglobin (Hb)    12.1    g/dL    12.0 - 16.0"
        - Single-space dense:  "Haemoglobin 12.1 g/dL 13.0–17.0 LOW"
        - Large count values:  "WBC Count 7,800 /µL 4,000–11,000 —"
        - Trailing flags:      "Fasting Glucose 112 mg/dL 70–99 HIGH"
        """
        clean_line = line.strip()
        if not clean_line or len(clean_line) < 3:
            return None

        # Ignore obvious header / metadata lines
        ignore_keywords = [
            "DIAGNOSTIC", "LABORATORY", "PATIENT NAME", "AGE", "SEX", "GENDER",
            "REFERRED BY", "SAMPLE DATE", "REPORT DATE", "PAGE", "TEST NAME",
            "INVESTIGATION", "RESULT", "REFERENCE RANGE", "BIOCHEMISTRY", "HAEMATOLOGY",
            "PATHOLOGY", "DOCTOR", "HOSPITAL", "CLINIC", "PHONE", "ADDRESS",
            "--- PAGE BREAK ---", "SYNTHETIC", "TEST-DATA", "COMPARISON TEST"
        ]
        if any(clean_line.upper().startswith(kw) for kw in ignore_keywords):
            return None

        # Normalize colons in "Name: Value" format
        clean_line = re.sub(r':\s+', '  ', clean_line)

        # Tokenize by whitespace
        tokens = clean_line.split()
        if len(tokens) < 2:
            return None

        # --- Find the FIRST reliably numeric value token ---
        num_idx = -1
        numeric_val: Optional[float] = None
        qual_val: Optional[str] = None

        for idx, t in enumerate(tokens):
            if idx == 0:
                continue

            # Check qualitative result keywords
            if t.upper() in ["NEGATIVE", "POSITIVE", "NON-REACTIVE", "REACTIVE", "NORMAL", "NIL", "ABSENT", "PRESENT"]:
                name_part = " ".join(tokens[:idx])
                if re.search(r'[A-Za-z]{2,}', name_part):
                    qual_val = t
                    num_idx = idx
                    break

            # Parse numeric value using comma-aware parser
            val = parse_number_token(t)
            if val is not None:
                name_part = " ".join(tokens[:idx])
                if re.search(r'[A-Za-z]{2,}', name_part):
                    numeric_val = val
                    num_idx = idx
                    break

        if num_idx == -1:
            return None

        # Build test name from all tokens before the value
        test_name = " ".join(tokens[:num_idx]).strip(" :.-,")
        test_name = re.sub(r'\s*\(\s*$', '', test_name).strip()
        if not test_name or len(test_name) < 2:
            return None

        remaining_tokens = tokens[num_idx + 1:]
        explicit_flag: Optional[str] = None

        # Check if the last remaining token is a report Flag (e.g. LOW, HIGH, NORMAL, —, -)
        if remaining_tokens:
            last_tok = remaining_tokens[-1]
            if last_tok.upper() in FLAG_TOKENS or last_tok in ["—", "-", "--"]:
                explicit_flag = FLAG_TOKENS.get(last_tok.upper(), FLAG_TOKENS.get(last_tok))
                remaining_tokens = remaining_tokens[:-1]

        unit: Optional[str] = None
        range_str = ""

        if remaining_tokens:
            first_rem = remaining_tokens[0]
            norm_first = normalize_unit_str(first_rem)
            
            # Check unit against known lexicon with unicode normalization
            for u in COMMON_UNITS:
                norm_u = normalize_unit_str(u)
                if norm_first == norm_u or norm_first == norm_u.replace('/', ''):
                    unit = u
                    remaining_tokens = remaining_tokens[1:]
                    break

            # Prefix match fallback
            if unit is None:
                for u in COMMON_UNITS:
                    norm_u = normalize_unit_str(u)
                    if len(norm_u) >= 3 and norm_first.startswith(norm_u[:3]):
                        unit = u
                        remaining_tokens = remaining_tokens[1:]
                        break

            if remaining_tokens:
                range_str = " ".join(remaining_tokens)

        # Parse reference bounds
        parsed_range = self.parse_reference_range(range_str)

        # Normalize test name to canonical taxonomy
        norm_res = biomarker_normalizer.normalize(test_name)
        normalized_name = norm_res.normalized_name
        category = norm_res.category

        # Use report's reference range; fall back to canonical defaults if missing
        ref_min = parsed_range.ref_min
        ref_max = parsed_range.ref_max
        if ref_min is None and ref_max is None and norm_res.canonical_info:
            ref_min = norm_res.canonical_info.default_ref_min
            ref_max = norm_res.canonical_info.default_ref_max

        # Determine diagnostic flag
        calculated_flag = self.determine_flag(numeric_val, qual_val, ref_min, ref_max)
        if explicit_flag and explicit_flag in ["LOW", "HIGH", "CRITICAL"]:
            flag = explicit_flag
        elif calculated_flag in ["LOW", "HIGH", "CRITICAL"]:
            flag = calculated_flag
        else:
            flag = explicit_flag or calculated_flag

        # Run Confidence Verification & Physiological Sanity Engine
        verif_res = confidence_engine.verify(
            raw_test_name=test_name,
            value_numeric=numeric_val,
            value_text=qual_val or (str(numeric_val) if numeric_val is not None else None),
            unit=unit,
            reference_range_raw=parsed_range.raw or None,
            ocr_confidence=ocr_confidence,
        )

        return ExtractedTestResult(
            raw_test_name=test_name,
            normalized_name=normalized_name,
            category=category,
            value_numeric=numeric_val,
            value_text=qual_val or (str(numeric_val) if numeric_val is not None else None),
            unit=unit,
            reference_range_raw=parsed_range.raw or None,
            ref_min=ref_min,
            ref_max=ref_max,
            flag=flag,
            ocr_confidence=ocr_confidence,
            composite_confidence=verif_res.composite_confidence,
            verification_status=verif_res.verification_status,
            verification_reason=verif_res.verification_reason,
            is_outlier=verif_res.is_outlier,
        )

    def parse_text(self, raw_text: str, default_confidence: float = 95.0) -> List[ExtractedTestResult]:
        """
        Parses full raw OCR text document into structured list of medical test results.
        """
        results: List[ExtractedTestResult] = []
        seen_names = set()

        lines = raw_text.split("\n")
        for line in lines:
            parsed = self.parse_line_flexible(line, ocr_confidence=default_confidence)
            if parsed and parsed.raw_test_name.lower() not in seen_names:
                seen_names.add(parsed.raw_test_name.lower())
                results.append(parsed)

        logger.info(f"Parsed {len(results)} structured clinical test values from OCR text")
        return results

medical_parser = MedicalReportParser()
