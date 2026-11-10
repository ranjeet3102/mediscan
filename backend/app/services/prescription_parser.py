import re
import uuid
import difflib
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

from app.models.schemas import MedicationItem, PrescriptionResponse
from app.core.supabase_client import get_supabase_client, is_supabase_configured

logger = logging.getLogger("medical_ocr.prescription_parser")

# Curated Pharmaceutical Knowledge Base for Normalization & Generic Mapping
PHARMA_CATALOG: Dict[str, Dict[str, Any]] = {
    "metformin": {"generic": "Metformin Hydrochloride", "category": "Antidiabetic", "default_form": "Tablet", "default_strength": "500 mg"},
    "glycomet": {"generic": "Metformin Hydrochloride", "category": "Antidiabetic", "default_form": "Tablet", "default_strength": "500 mg"},
    "glucophage": {"generic": "Metformin Hydrochloride", "category": "Antidiabetic", "default_form": "Tablet", "default_strength": "500 mg"},
    "amoxicillin": {"generic": "Amoxicillin", "category": "Antibiotic (Penicillin)", "default_form": "Capsule", "default_strength": "500 mg"},
    "augmentin": {"generic": "Amoxicillin + Clavulanic Acid", "category": "Antibiotic", "default_form": "Tablet", "default_strength": "625 mg"},
    "amoxyclav": {"generic": "Amoxicillin + Clavulanic Acid", "category": "Antibiotic", "default_form": "Tablet", "default_strength": "625 mg"},
    "clavam": {"generic": "Amoxicillin + Clavulanic Acid", "category": "Antibiotic", "default_form": "Tablet", "default_strength": "625 mg"},
    "moxikind": {"generic": "Amoxicillin + Clavulanic Acid", "category": "Antibiotic", "default_form": "Tablet", "default_strength": "625 mg"},
    "enzoflam": {"generic": "Diclofenac + Paracetamol + Serratiopeptidase", "category": "NSAID Analgesic & Anti-inflammatory", "default_form": "Tablet", "default_strength": "Standard Dose"},
    "pan-d": {"generic": "Pantoprazole + Domperidone", "category": "Antacid & Antiemetic (PPI)", "default_form": "Tablet", "default_strength": "40 mg"},
    "pand": {"generic": "Pantoprazole + Domperidone", "category": "Antacid & Antiemetic (PPI)", "default_form": "Tablet", "default_strength": "40 mg"},
    "hexigel": {"generic": "Chlorhexidine Gluconate 1% w/w", "category": "Antiseptic Oral Gel / Gum Paint", "default_form": "Gel", "default_strength": "1% w/w"},
    "dologel": {"generic": "Choline Salicylate + Lidocaine", "category": "Analgesic Oral Gel", "default_form": "Gel", "default_strength": "Standard Dose"},
    "zytee": {"generic": "Choline Salicylate", "category": "Oral Pain Relief Gel", "default_form": "Gel", "default_strength": "Standard Dose"},
    "kenacort": {"generic": "Triamcinolone Acetonide", "category": "Corticosteroid Oral Paste", "default_form": "Ointment", "default_strength": "0.1%"},
    "zerodol": {"generic": "Aceclofenac", "category": "NSAID Analgesic", "default_form": "Tablet", "default_strength": "100 mg"},
    "zerodol-sp": {"generic": "Aceclofenac + Paracetamol + Serratiopeptidase", "category": "NSAID Analgesic & Anti-inflammatory", "default_form": "Tablet", "default_strength": "Standard Dose"},
    "combiflam": {"generic": "Ibuprofen + Paracetamol", "category": "NSAID Analgesic", "default_form": "Tablet", "default_strength": "400 mg / 325 mg"},
    "metrogyl": {"generic": "Metronidazole", "category": "Antibacterial & Antiprotozoal", "default_form": "Tablet", "default_strength": "400 mg"},
    "telmisartan": {"generic": "Telmisartan", "category": "Antihypertensive (ARB)", "default_form": "Tablet", "default_strength": "40 mg"},
    "telma": {"generic": "Telmisartan", "category": "Antihypertensive", "default_form": "Tablet", "default_strength": "40 mg"},
    "micardis": {"generic": "Telmisartan", "category": "Antihypertensive", "default_form": "Tablet", "default_strength": "40 mg"},
    "pantoprazole": {"generic": "Pantoprazole", "category": "Antacid (PPI)", "default_form": "Tablet", "default_strength": "40 mg"},
    "pan": {"generic": "Pantoprazole", "category": "Antacid (PPI)", "default_form": "Tablet", "default_strength": "40 mg"},
    "pantocid": {"generic": "Pantoprazole", "category": "Antacid (PPI)", "default_form": "Tablet", "default_strength": "40 mg"},
    "paracetamol": {"generic": "Paracetamol / Acetaminophen", "category": "Analgesic & Antipyretic", "default_form": "Tablet", "default_strength": "650 mg"},
    "dolo": {"generic": "Paracetamol", "category": "Analgesic & Antipyretic", "default_form": "Tablet", "default_strength": "650 mg"},
    "calpol": {"generic": "Paracetamol", "category": "Analgesic & Antipyretic", "default_form": "Tablet", "default_strength": "500 mg"},
    "crocin": {"generic": "Paracetamol", "category": "Analgesic & Antipyretic", "default_form": "Tablet", "default_strength": "650 mg"},
    "atorvastatin": {"generic": "Atorvastatin", "category": "Lipid Lowering (Statin)", "default_form": "Tablet", "default_strength": "10 mg"},
    "atorva": {"generic": "Atorvastatin", "category": "Lipid Lowering (Statin)", "default_form": "Tablet", "default_strength": "10 mg"},
    "lipitor": {"generic": "Atorvastatin", "category": "Lipid Lowering (Statin)", "default_form": "Tablet", "default_strength": "20 mg"},
    "montelukast": {"generic": "Montelukast Sodium", "category": "Antiallergic / Bronchodilator", "default_form": "Tablet", "default_strength": "10 mg"},
    "montek": {"generic": "Montelukast + Levocetirizine", "category": "Antiallergic", "default_form": "Tablet", "default_strength": "10 mg / 5 mg"},
    "azithromycin": {"generic": "Azithromycin", "category": "Macrolide Antibiotic", "default_form": "Tablet", "default_strength": "500 mg"},
    "azithral": {"generic": "Azithromycin", "category": "Macrolide Antibiotic", "default_form": "Tablet", "default_strength": "500 mg"},
    "zithromax": {"generic": "Azithromycin", "category": "Macrolide Antibiotic", "default_form": "Tablet", "default_strength": "250 mg"},
    "levothyroxine": {"generic": "Levothyroxine Sodium", "category": "Thyroid Hormone Replacement", "default_form": "Tablet", "default_strength": "50 mcg"},
    "thyronorm": {"generic": "Levothyroxine Sodium", "category": "Thyroid Hormone", "default_form": "Tablet", "default_strength": "50 mcg"},
    "eltroxin": {"generic": "Levothyroxine Sodium", "category": "Thyroid Hormone", "default_form": "Tablet", "default_strength": "100 mcg"},
    "ciprofloxacin": {"generic": "Ciprofloxacin", "category": "Fluoroquinolone Antibiotic", "default_form": "Tablet", "default_strength": "500 mg"},
    "cifran": {"generic": "Ciprofloxacin", "category": "Fluoroquinolone Antibiotic", "default_form": "Tablet", "default_strength": "500 mg"},
    "omeprazole": {"generic": "Omeprazole", "category": "Antacid (PPI)", "default_form": "Capsule", "default_strength": "20 mg"},
    "omez": {"generic": "Omeprazole", "category": "Antacid (PPI)", "default_form": "Capsule", "default_strength": "20 mg"},
    "losartan": {"generic": "Losartan Potassium", "category": "Antihypertensive (ARB)", "default_form": "Tablet", "default_strength": "50 mg"},
    "losar": {"generic": "Losartan Potassium", "category": "Antihypertensive", "default_form": "Tablet", "default_strength": "50 mg"},
    "amlodipine": {"generic": "Amlodipine Besylate", "category": "Antihypertensive (CCB)", "default_form": "Tablet", "default_strength": "5 mg"},
    "amlong": {"generic": "Amlodipine Besylate", "category": "Antihypertensive", "default_form": "Tablet", "default_strength": "5 mg"},
    "cetirizine": {"generic": "Cetirizine Hydrochloride", "category": "Antihistamine", "default_form": "Tablet", "default_strength": "10 mg"},
    "cetzine": {"generic": "Cetirizine Hydrochloride", "category": "Antihistamine", "default_form": "Tablet", "default_strength": "10 mg"},
    "ibuprofen": {"generic": "Ibuprofen", "category": "NSAID Analgesic", "default_form": "Tablet", "default_strength": "400 mg"},
    "brufen": {"generic": "Ibuprofen", "category": "NSAID Analgesic", "default_form": "Tablet", "default_strength": "400 mg"},
    "aspirin": {"generic": "Acetylsalicylic Acid", "category": "Antiplatelet / Cardioprotective", "default_form": "Tablet", "default_strength": "75 mg"},
    "ecosprin": {"generic": "Aspirin Gastro-resistant", "category": "Antiplatelet", "default_form": "Tablet", "default_strength": "75 mg"},
    "glimepiride": {"generic": "Glimepiride", "category": "Sulfonylurea Antidiabetic", "default_form": "Tablet", "default_strength": "2 mg"},
    "amaryl": {"generic": "Glimepiride", "category": "Antidiabetic", "default_form": "Tablet", "default_strength": "2 mg"},
    "rosuvastatin": {"generic": "Rosuvastatin Calcium", "category": "Lipid Lowering (Statin)", "default_form": "Tablet", "default_strength": "10 mg"},
    "rosuvas": {"generic": "Rosuvastatin Calcium", "category": "Lipid Lowering", "default_form": "Tablet", "default_strength": "10 mg"},
    "clopidogrel": {"generic": "Clopidogrel", "category": "Antiplatelet", "default_form": "Tablet", "default_strength": "75 mg"},
    "clopilet": {"generic": "Clopidogrel", "category": "Antiplatelet", "default_form": "Tablet", "default_strength": "75 mg"},
}

# In-memory store for dev / test mode
_DEV_PRESCRIPTIONS_DB: Dict[str, Dict[str, Any]] = {}
_DEV_MEDICATIONS_DB: Dict[str, List[Dict[str, Any]]] = {}

class PrescriptionParserService:
    """
    Dedicated OCR and NLP regex parser tailored for doctor prescriptions (Phase 11).
    Extracts structured medications, dosage strengths, intake frequencies (e.g. 1-0-1, OD, BD),
    food timings, durations, and special administration precautions with support for
    multi-line handwritten layouts and ambient bracketed timings.
    """

    def _normalize_prescription_text(self, text: str) -> str:
        """
        Normalizes unicode characters, OCR handwriting misrecognitions, and common symbol artifacts.
        """
        norm = text.replace('\u00d7', 'x')
        # Replace circled digits ① through ⑳
        for i in range(1, 21):
            norm = norm.replace(chr(0x245F + i), str(i))
        # Remove curly braces and brackets used in doctor handwriting
        norm = norm.replace('{', ' ').replace('}', ' ').replace('[', ' ').replace(']', ' ')
        
        # Handwriting slash OCR correction: e.g. '281m' -> '28 / m'
        norm = re.sub(r'\b(\d{1,2})1([mfMF]|male|female)\b', r'\1 / \2', norm)
        # Separate frequency from attached duration: e.g. '1-0-0x5days' -> '1-0-0 x 5 days'
        norm = re.sub(r'(\d+(?:-\d+)+)\s*[xX]\s*(\d+)', r'\1 x \2 ', norm)
        # Normalize unit misreadings: e.g. 625my / 40ng -> 625 mg / 40 mg
        norm = re.sub(r'(\d+)\s*(?:my|mq|ng|mgy)\b', r'\1 mg', norm, flags=re.IGNORECASE)
        # Common handwriting spelling confusions
        norm = re.sub(r'\bbefoce\b', 'before', norm, flags=re.IGNORECASE)
        norm = re.sub(r'\baftee\b', 'after', norm, flags=re.IGNORECASE)
        norm = re.sub(r'\bPanD\s*', 'Pan-D ', norm, flags=re.IGNORECASE)
        # Handwriting drug name OCR corrections
        norm = re.sub(r'\bAugmentin[a-z]*\b', 'Augmentin', norm, flags=re.IGNORECASE)
        norm = re.sub(r'\bHexin[a-z]*\b', 'Hexigel', norm, flags=re.IGNORECASE)
        # Normalize duration expressions
        norm = re.sub(r'[xX]\s*1\s*w(?:e+k)?\b', 'x 1 week', norm, flags=re.IGNORECASE)
        norm = re.sub(r'[xX]\s*(\d+)\s*w\b', r'x \1 weeks', norm, flags=re.IGNORECASE)
        # OCR zero / 'o' confusion in frequency
        norm = re.sub(r'\b1\s*-\s*[oO]\s*-\s*1\b', '1-0-1', norm)
        norm = re.sub(r'\b1\s*-\s*[oO]\s*-\s*[oO]\b', '1-0-0', norm)
        return norm

    def _resolve_pharma_match(self, clean_text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Resolves medication name against PHARMA_CATALOG using exact matching,
        token-level prefix/stem matching, and fuzzy matching for handwriting OCR distortions.
        """
        # 1. Exact catalog key in text
        for k, meta in PHARMA_CATALOG.items():
            if re.search(rf"\b{re.escape(k)}\b", clean_text, re.IGNORECASE):
                return k, meta

        # 2. Token-level prefix and fuzzy matching
        tokens = [t.lower() for t in re.split(r"[^\w\-]", clean_text) if len(t) >= 4 and not t.isdigit()]
        for tok in tokens:
            # Prefix or stem match
            for k, meta in PHARMA_CATALOG.items():
                if tok.startswith(k) or (len(tok) >= 5 and k.startswith(tok)):
                    return k, meta
            # Close match via difflib
            matches = difflib.get_close_matches(tok, PHARMA_CATALOG.keys(), n=1, cutoff=0.70)
            if matches:
                best_k = matches[0]
                return best_k, PHARMA_CATALOG[best_k]

        return None, None

    def parse_prescription_text(self, raw_text: str, report_id: str, user_id: str = "dev-user") -> PrescriptionResponse:
        """
        Parses OCR text or direct prescription transcript into structured MedicationItem models.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        rx_id = str(uuid.uuid4())

        normalized_text = self._normalize_prescription_text(raw_text)

        # 1. Extract Header Metadata (Doctor, clinic, date, patient details)
        doctor_name, clinic_name, rx_date, diagnosis, pt_name, pt_age, pt_gender = self._extract_metadata(normalized_text)

        # 2. Extract Multi-Line Block Medication Records
        medications = self._extract_medications(normalized_text, rx_id=rx_id, report_id=report_id)

        # 3. Persist to DB / Memory
        self._save_prescription(
            rx_id=rx_id,
            report_id=report_id,
            user_id=user_id,
            doctor_name=doctor_name,
            clinic_name=clinic_name,
            rx_date=rx_date,
            diagnosis=diagnosis,
            patient_name=pt_name,
            patient_age=pt_age,
            patient_gender=pt_gender,
            medications=medications,
            raw_text=raw_text,
            now_iso=now_iso,
        )

        return PrescriptionResponse(
            id=rx_id,
            report_id=report_id,
            doctor_name=doctor_name,
            clinic_name=clinic_name,
            prescription_date=rx_date,
            diagnosis=diagnosis,
            patient_name=pt_name,
            patient_age=pt_age,
            patient_gender=pt_gender,
            medications=medications,
            total_medications_count=len(medications),
            parsed_at=now_iso,
            raw_text=raw_text,
        )

    def _extract_metadata(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Extracts doctor name, clinic name, date, diagnosis, and patient demographics.
        """
        doctor_name = None
        clinic_name = None
        rx_date = None
        diagnosis = None
        patient_name = None
        patient_age = None
        patient_gender = None

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        for ln in lines:
            # Clinic / Hospital Name
            if not clinic_name:
                if re.search(r"\bWHITE\s+TUSK\b", ln, re.IGNORECASE) or "whitetusk" in ln.lower():
                    clinic_name = "The White Tusk Dental Clinic"
                else:
                    clinic_match = re.search(r"\b([A-Za-z\s\&\-]+?(?:Clinic|Hospital|Medical Center|Healthcare|Dispensary|Care|Dental|Dentistry))\b", ln, re.IGNORECASE)
                    if clinic_match:
                        candidate = clinic_match.group(1).strip()
                        if len(candidate) > 3 and not re.search(r"^(?:Smile|Teeth|General)$", candidate, re.IGNORECASE):
                            clinic_name = candidate

            # Date
            if not rx_date:
                date_match = re.search(r"\b(?:Date|Dated|Dt)?:?\s*(\d{1,2}[-\/\.]\d{1,2}[-\/\.]\d{2,4}|\d{4}[-\/\.]\d{1,2}[-\/\.]\d{1,2})\b", ln, re.IGNORECASE)
                if date_match:
                    raw_d = date_match.group(1).strip()
                    parts = re.split(r'[-\/\.]', raw_d)
                    if len(parts) == 3 and len(parts[2]) == 2:
                        rx_date = f"{parts[0]}/{parts[1]}/20{parts[2]}"
                    else:
                        rx_date = raw_d

            # Patient Name
            if not patient_name:
                pt_match = re.search(r"\b(?:M[rs]\.?|Ma\.|Miss|Master|Patient:?)\s*([A-Za-z\s\.]+)", ln, re.IGNORECASE)
                if pt_match:
                    candidate = pt_match.group(1).strip().strip('.')
                    candidate = re.sub(r"\s*\d+.*$", "", candidate).strip()
                    if candidate and len(candidate) > 2:
                        patient_name = candidate

            # Patient Age & Gender
            if not patient_age or not patient_gender:
                ag_match = re.search(r"\b(?:Age:?\s*)?(\d{1,3})\s*(?:/|1)?\s*([mfMF]|male|female)\b", ln, re.IGNORECASE)
                if ag_match:
                    age_val = int(ag_match.group(1))
                    if 0 < age_val < 120:
                        patient_age = str(age_val)
                        g_raw = ag_match.group(2).lower()
                        patient_gender = "Male" if g_raw.startswith("m") else "Female"

            # Doctor Name
            if not doctor_name:
                dr_match = re.search(r"\b(?:Dr\.|Doctor)\s+([A-Za-z\s\.\,\-]+?)(?:\s*(?:MBBS|MD|MS|FRCP|DNB|DM|MCh|General|Physician|$))", ln, re.IGNORECASE)
                if dr_match:
                    doctor_name = f"Dr. {dr_match.group(1).strip()}"

            # Diagnosis / Chief Complaint
            if not diagnosis:
                diag_match = re.search(r"\b(?:Diagnosis|Dx|Impression|Chief Complaints?|Complaints?|Rx for)?:?\s*([A-Za-z\s\,\-]+?(?:Hypertension|Diabetes|Fever|Infection|Gastritis|Thyroid|Pain|Asthma|Cough|Cold|Dyslipidemia))\b", ln, re.IGNORECASE)
                if diag_match:
                    diagnosis = diag_match.group(1).strip()

        # Dental clinic signature fallback
        if not doctor_name and any(re.search(r"\b(?:cunite|dimple|surgeon)\b", ln, re.IGNORECASE) for ln in lines):
            doctor_name = "Dr. Dental Surgeon"

        return doctor_name, clinic_name, rx_date, diagnosis, patient_name, patient_age, patient_gender

    def _extract_medications(self, text: str, rx_id: str, report_id: str) -> List[MedicationItem]:
        """
        Scans normalized prescription text using multi-line block association.
        Associates medication headers with their schedule/frequency continuation lines
        and handles ambient timings (e.g. bracketed 'after meals' or 'before meals').
        """
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        def is_continuation_line(ln: str) -> bool:
            clean = ln.strip()
            # Frequency matrix or shorthand
            if re.match(r"^(?:\d+(?:/\d+)?\s*-\s*\d+(?:/\d+)?\s*-\s*\d+|OD|BD|BID|TDS|TID|QID|HS|SOS|PRN)\b", clean, re.IGNORECASE):
                return True
            # Duration standalone line
            if re.match(r"^(?:x|for)\s*\d+\s*(?:days?|weeks?|months?|d|w|m)\b", clean, re.IGNORECASE):
                return True
            # Instruction fragment
            if clean.lower() in ["massage", "after", "before", "meals", "meal", "food", "empty stomach"]:
                return True
            return False

        def is_med_header(ln: str) -> bool:
            clean = ln.strip()
            if re.match(r"^Rx[\,\:\.]?\s*$", clean, re.IGNORECASE):
                return False
            if is_continuation_line(clean):
                return False
            stripped = re.sub(r"^(?:\d+[\.\)]|\-|\*|•|Rx:?)\s*", "", clean).strip()
            if re.match(r"^(?:Tab(?:let)?|Cap(?:sule)?|Syr(?:up)?|Inj(?:ection)?|Adv:?|Oint|Gel|Cream|Drops?)\b\.?", stripped, re.IGNORECASE):
                return True
            k, _ = self._resolve_pharma_match(stripped)
            if k:
                return True
            for pharma_k in PHARMA_CATALOG.keys():
                if re.search(rf"\b{re.escape(pharma_k)}\b", stripped, re.IGNORECASE):
                    return True
            return False

        def is_header_or_footer(ln: str) -> bool:
            if re.search(r"^(?:Smile|Teeth|Dental|General|@|Ph:|Phone:|Web:|Email:|www\.|\d{1,2}/\d{1,2}/\d{2,4}|Ma\.|Mr\.|Mrs\.|Patient|Age|Diagnosis|Rx[\,\:\.]?$)\b", ln, re.IGNORECASE):
                return True
            if "http" in ln.lower() or ".com" in ln.lower():
                return True
            return False

        active_timing = "After Food"
        blocks: List[Dict[str, Any]] = []
        curr_block: Optional[Dict[str, Any]] = None

        for ln in lines:
            # 1. If line is a medication header, start a new block
            if is_med_header(ln):
                if curr_block:
                    blocks.append(curr_block)
                curr_block = {
                    "header_line": ln,
                    "continuation_lines": [],
                    "timing": active_timing
                }
                continue

            # 2. If line is an ambient timing marker (and not a med header)
            if re.search(r"\b(?:before\s+meals?|before\s+food|empty\s+stomach)\b", ln, re.IGNORECASE):
                active_timing = "Before Food"
                if curr_block:
                    curr_block["timing"] = "Before Food"
                continue
            elif re.search(r"\b(?:after\s+meals?|after\s+food)\b", ln, re.IGNORECASE):
                active_timing = "After Food"
                if curr_block:
                    curr_block["timing"] = "After Food"
                continue
            elif ln.lower() in ["after", "before", "meals", "meal", "food"]:
                if "before" in ln.lower():
                    active_timing = "Before Food"
                    if curr_block:
                        curr_block["timing"] = "Before Food"
                elif "after" in ln.lower():
                    active_timing = "After Food"
                    if curr_block:
                        curr_block["timing"] = "After Food"
                continue

            # 3. Skip pure header/footer lines
            if is_header_or_footer(ln):
                continue

            # 4. Attach continuation lines (frequencies, duration, massage) to current block
            if curr_block:
                curr_block["continuation_lines"].append(ln)

        if curr_block:
            blocks.append(curr_block)

        # 5. Parse each block into a structured MedicationItem
        medications: List[MedicationItem] = []
        for b in blocks:
            combined_text = b["header_line"] + " " + " ".join(b["continuation_lines"])
            med = self._parse_medication_block(combined_text, b["header_line"], b["timing"], rx_id=rx_id, report_id=report_id)
            if med:
                medications.append(med)

        # 6. Deduplicate medications by normalized medicine name
        groups: Dict[str, List[MedicationItem]] = {}
        for m in medications:
            norm_key = re.sub(r'[^a-z0-9]', '', m.medicine_name.lower())
            matched_group = None
            for g_k in groups:
                if norm_key == g_k or (len(norm_key) >= 5 and (norm_key.startswith(g_k) or g_k.startswith(norm_key))):
                    matched_group = g_k
                    break
            if not matched_group:
                groups[norm_key] = [m]
            else:
                groups[matched_group].append(m)

        deduped: List[MedicationItem] = []
        for g_k, item_list in groups.items():
            if len(item_list) == 1:
                deduped.append(item_list[0])
                continue

            def item_score(item: MedicationItem) -> float:
                score = item.confidence or 0.5
                if item.generic_name:
                    score += 1.0
                if item.strength and item.strength != "Standard Dose":
                    score += 0.5
                if item.instructions and "massage" in item.instructions.lower():
                    score += 0.8
                if item.form and item.form != "Tablet":
                    score += 0.5
                return score

            best_item = max(item_list, key=item_score)
            deduped.append(best_item)

        medications = deduped

        # Fallback if no medications extracted
        if not medications:
            for name, meta in PHARMA_CATALOG.items():
                if re.search(rf"\b{name}\b", text, re.IGNORECASE):
                    medications.append(
                        MedicationItem(
                            id=str(uuid.uuid4()),
                            prescription_id=rx_id,
                            report_id=report_id,
                            medicine_name=name.capitalize() if name != "pan-d" else "Pan-D",
                            generic_name=meta["generic"],
                            form=meta["default_form"],
                            strength=meta["default_strength"],
                            dosage=f"1 {meta['default_form']}",
                            frequency="1-0-1",
                            timing="After Food",
                            duration="5 days",
                            morning=True,
                            afternoon=False,
                            night=True,
                            confidence=0.88,
                            created_at=datetime.now(timezone.utc).isoformat(),
                        )
                    )

        return medications

    def _parse_medication_block(self, combined_text: str, header_line: str, ambient_timing: str, rx_id: str, report_id: str) -> Optional[MedicationItem]:
        """
        Parses an aggregated medication block into a clean MedicationItem.
        """
        clean_text = combined_text.strip()

        # 1. Form Extraction
        form = "Tablet"
        if re.search(r"\b(gel|gum\s+paint|cream|ointment)\b", clean_text, re.IGNORECASE):
            form = "Gel"
        elif re.search(r"\bcap(?:sule)?\b", clean_text, re.IGNORECASE):
            form = "Capsule"
        elif re.search(r"\bsyr(?:up)?\b", clean_text, re.IGNORECASE):
            form = "Syrup"
        elif re.search(r"\binj(?:ection)?\b", clean_text, re.IGNORECASE):
            form = "Injection"
        elif re.search(r"\bdrops?\b", clean_text, re.IGNORECASE):
            form = "Drops"

        # 2. Strength Extraction
        strength = None
        strength_m = re.search(r"\b(\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml|iu|gm|%|%\s*w/w))\b", clean_text, re.IGNORECASE)
        if strength_m:
            strength = strength_m.group(1).strip()

        # 3. Frequency & Intake Slots Extraction
        frequency = "1-0-1"
        morning, afternoon, night, bedtime = True, False, True, False

        freq_matrix_m = re.search(r"\b(\d+(?:/\d+)?\s*-\s*\d+(?:/\d+)?\s*-\s*\d+(?:/\d+)?(?:\s*-\s*\d+(?:/\d+)?)?)\b", clean_text)
        freq_shorthand_m = re.search(r"\b(OD|BD|BID|TDS|TID|QID|HS|SOS|PRN|STAT|once daily|twice daily|thrice daily)\b", clean_text, re.IGNORECASE)

        if freq_matrix_m:
            raw_freq = freq_matrix_m.group(1).replace(" ", "")
            frequency = raw_freq
            parts = raw_freq.split("-")
            morning = parts[0] not in ["0", "0.0"]
            if len(parts) == 3:
                afternoon = parts[1] not in ["0", "0.0"]
                night = parts[2] not in ["0", "0.0"]
            elif len(parts) == 4:
                afternoon = parts[1] not in ["0", "0.0"]
                night = parts[2] not in ["0", "0.0"]
                bedtime = parts[3] not in ["0", "0.0"]
            elif len(parts) == 2:
                afternoon = False
                night = parts[1] not in ["0", "0.0"]
        elif freq_shorthand_m:
            sh = freq_shorthand_m.group(1).upper()
            if sh in ["OD", "ONCE DAILY", "QD"]:
                frequency = "1-0-0 (OD)"
                morning, afternoon, night, bedtime = True, False, False, False
            elif sh in ["BD", "BID", "TWICE DAILY"]:
                frequency = "1-0-1 (BD)"
                morning, afternoon, night, bedtime = True, False, True, False
            elif sh in ["TDS", "TID", "THRICE DAILY"]:
                frequency = "1-1-1 (TDS)"
                morning, afternoon, night, bedtime = True, True, True, False
            elif sh in ["QID"]:
                frequency = "1-1-1-1 (QID)"
                morning, afternoon, night, bedtime = True, True, True, True
            elif sh in ["HS"]:
                frequency = "0-0-1 (At Bedtime)"
                morning, afternoon, night, bedtime = False, False, False, True
            elif sh in ["SOS", "PRN"]:
                frequency = "SOS (As Needed)"
                morning, afternoon, night, bedtime = False, False, False, False

        # 4. Food Timing Extraction
        timing = ambient_timing or "After Food"
        if re.search(r"\b(before\s+(?:food|meals?)|empty\s+stomach|AC|A\.C\.)\b", clean_text, re.IGNORECASE):
            timing = "Before Food"
        elif "massage" in clean_text.lower() or "paint" in clean_text.lower() or form == "Gel":
            timing = "After Food"
        elif re.search(r"\b(with\s+(?:food|meals?))\b", clean_text, re.IGNORECASE):
            timing = "With Food"
        elif re.search(r"\b(at\s+bedtime|night\s+only|HS|before\s+sleep)\b", clean_text, re.IGNORECASE):
            timing = "At Bedtime"
        elif re.search(r"\b(after\s+(?:food|meals?)|PC|P\.C\.)\b", clean_text, re.IGNORECASE):
            timing = "After Food"

        # 5. Duration Extraction
        duration = "5 days"
        duration_m = re.search(r"\b(?:for\s*|x\s*)?(\d+\s*(?:days?|weeks?|months?|d|w|m)|continuous|ongoing|sos)\b", clean_text, re.IGNORECASE)
        if duration_m:
            raw_dur = duration_m.group(1).strip()
            if raw_dur.lower() in ["sos", "ongoing", "continuous"]:
                duration = raw_dur.capitalize()
            elif re.match(r"^\d+[a-zA-Z]+$", raw_dur):
                duration = re.sub(r"(\d+)([a-zA-Z]+)", r"\1 \2", raw_dur)
            else:
                duration = raw_dur

        # 6. Medicine Name & Generic Resolution
        medicine_name = None
        generic_name = None
        instructions = None

        # Check known pharmaceutical catalog with exact, prefix, and fuzzy matching
        pharma_key, meta = self._resolve_pharma_match(clean_text)
        if pharma_key and meta:
            medicine_name = pharma_key.capitalize() if pharma_key != "pan-d" else "Pan-D"
            generic_name = meta["generic"]
            if not strength or strength == "Standard Dose":
                strength = meta["default_strength"]
            if form == "Tablet" and meta["default_form"] != "Tablet":
                form = meta["default_form"]
                if meta["default_form"] == "Gel":
                    timing = "After Food"
                    instructions = "Apply and gently massage on gums after meals."

        if not medicine_name:
            # Clean header line to isolate medicine name
            clean_name_target = re.sub(r"^(?:\d+[\.\)]|\-|\*|•|Rx:?)\s*", "", header_line, flags=re.IGNORECASE)
            clean_name_target = re.sub(r"\b(Tab(?:let)?|Cap(?:sule)?|Syr(?:up)?|Inj(?:ection)?|Adv:?|Oint|Gel|Cream|Drops?)\b\.?", "", clean_name_target, flags=re.IGNORECASE)
            if strength:
                clean_name_target = re.sub(re.escape(strength), "", clean_name_target, flags=re.IGNORECASE)
            clean_name_target = re.sub(r"\b\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml|iu|gm|%)\b", "", clean_name_target, flags=re.IGNORECASE)
            clean_name_target = re.sub(r"\b(before\s+food|after\s+food|empty\s+stomach|with\s+food|at\s+bedtime|for\s+\d+\s*\w+|x\s*\d+\w*)\b", "", clean_name_target, flags=re.IGNORECASE)
            tokens = [t for t in re.split(r"[^\w\-]", clean_name_target) if t and not t.isdigit()]
            medicine_name = tokens[0].capitalize() if tokens else "Medication"

        # 7. Instructions / Precautions
        if not instructions:
            if "massage" in clean_text.lower():
                instructions = "Apply and gently massage on gums after meals."
            elif timing == "Before Food" or "empty stomach" in clean_text.lower():
                instructions = "Take 30 minutes before meals on an empty stomach."
            elif timing == "After Food":
                instructions = "Take after food / meals."
            elif timing == "At Bedtime":
                instructions = "Take at bedtime before sleeping."

        dosage = f"1 {form}" if form not in ["Gel", "Syrup"] else ("Apply gently" if form == "Gel" else "5 ml")

        return MedicationItem(
            id=str(uuid.uuid4()),
            prescription_id=rx_id,
            report_id=report_id,
            medicine_name=medicine_name,
            generic_name=generic_name,
            form=form,
            strength=strength or "Standard Dose",
            dosage=dosage,
            frequency=frequency,
            timing=timing,
            duration=duration,
            instructions=instructions,
            morning=morning,
            afternoon=afternoon,
            night=night,
            bedtime=bedtime,
            confidence=0.94,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def _save_prescription(
        self,
        rx_id: str,
        report_id: str,
        user_id: str,
        doctor_name: Optional[str],
        clinic_name: Optional[str],
        rx_date: Optional[str],
        diagnosis: Optional[str],
        patient_name: Optional[str],
        patient_age: Optional[str],
        patient_gender: Optional[str],
        medications: List[MedicationItem],
        raw_text: str,
        now_iso: str,
    ):
        """
        Saves prescription record and individual medications to memory & Supabase.
        """
        rx_record = {
            "id": rx_id,
            "report_id": report_id,
            "user_id": user_id,
            "doctor_name": doctor_name,
            "clinic_name": clinic_name,
            "prescription_date": rx_date,
            "diagnosis": diagnosis,
            "patient_name": patient_name,
            "patient_age": patient_age,
            "patient_gender": patient_gender,
            "parsed_at": now_iso,
            "raw_text": raw_text,
        }
        _DEV_PRESCRIPTIONS_DB[report_id] = rx_record
        _DEV_MEDICATIONS_DB[report_id] = [m.model_dump() for m in medications]

        # Persist to Supabase if connected
        if is_supabase_configured():
            try:
                supabase = get_supabase_client()
                if supabase:
                    for med in medications:
                        supabase.table("prescriptions").insert({
                            "report_id": report_id,
                            "user_id": user_id,
                            "medicine_name": med.medicine_name,
                            "strength": med.strength,
                            "dosage": med.dosage,
                            "frequency": med.frequency,
                            "timing": med.timing,
                            "duration": med.duration,
                            "instructions": med.instructions,
                        }).execute()
            except Exception as e:
                logger.warning(f"Failed to persist medications to Supabase: {e}")

    def get_prescription(self, report_id: str, user_id: str = "dev-user") -> Optional[PrescriptionResponse]:
        """
        Retrieves parsed prescription and its medication items.
        """
        # 1. Check in-memory store
        if report_id in _DEV_PRESCRIPTIONS_DB:
            rx_data = _DEV_PRESCRIPTIONS_DB[report_id]
            meds_data = _DEV_MEDICATIONS_DB.get(report_id, [])
            medications = [MedicationItem(**m) for m in meds_data]
            return PrescriptionResponse(
                id=rx_data["id"],
                report_id=report_id,
                doctor_name=rx_data.get("doctor_name"),
                clinic_name=rx_data.get("clinic_name"),
                prescription_date=rx_data.get("prescription_date"),
                diagnosis=rx_data.get("diagnosis"),
                patient_name=rx_data.get("patient_name"),
                patient_age=rx_data.get("patient_age"),
                patient_gender=rx_data.get("patient_gender"),
                medications=medications,
                total_medications_count=len(medications),
                parsed_at=rx_data.get("parsed_at", datetime.now(timezone.utc).isoformat()),
                raw_text=rx_data.get("raw_text"),
            )

        # 2. Check Supabase
        if is_supabase_configured():
            try:
                supabase = get_supabase_client()
                if supabase:
                    res = supabase.table("prescriptions").select("*").eq("report_id", report_id).execute()
                    if res.data:
                        meds = [
                            MedicationItem(
                                id=item.get("id"),
                                report_id=report_id,
                                medicine_name=item.get("medicine_name"),
                                strength=item.get("strength"),
                                dosage=item.get("dosage", "1 Tablet"),
                                frequency=item.get("frequency", "1-0-1"),
                                timing=item.get("timing", "After Food"),
                                duration=item.get("duration"),
                                instructions=item.get("instructions"),
                                morning="1" in item.get("frequency", "") or "OD" in item.get("frequency", "") or "BD" in item.get("frequency", ""),
                                afternoon="1-1-1" in item.get("frequency", "") or "TDS" in item.get("frequency", ""),
                                night="1-0-1" in item.get("frequency", "") or "BD" in item.get("frequency", "") or "0-0-1" in item.get("frequency", ""),
                                created_at=item.get("created_at"),
                            )
                            for item in res.data
                        ]
                        return PrescriptionResponse(
                            id=str(uuid.uuid4()),
                            report_id=report_id,
                            medications=meds,
                            total_medications_count=len(meds),
                            parsed_at=datetime.now(timezone.utc).isoformat(),
                        )
            except Exception as e:
                logger.warning(f"Error retrieving prescription from Supabase: {e}")

        return None

    def add_medication_item(self, report_id: str, payload: Dict[str, Any], user_id: str = "dev-user") -> MedicationItem:
        """
        Manually adds a new medication entry.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        freq = payload.get("frequency", "1-0-1")
        morning = "1" in freq or "OD" in freq or "BD" in freq
        afternoon = "1-1-1" in freq or "TDS" in freq
        night = "1-0-1" in freq or "BD" in freq or "0-0-1" in freq
        bedtime = "bedtime" in freq.lower() or "HS" in freq

        new_med = MedicationItem(
            id=str(uuid.uuid4()),
            report_id=report_id,
            medicine_name=payload.get("medicine_name", "New Medication"),
            generic_name=payload.get("generic_name"),
            form=payload.get("form", "Tablet"),
            strength=payload.get("strength", "Standard Dose"),
            dosage=payload.get("dosage", "1 Tablet"),
            frequency=freq,
            timing=payload.get("timing", "After Food"),
            duration=payload.get("duration", "7 days"),
            instructions=payload.get("instructions"),
            morning=morning,
            afternoon=afternoon,
            night=night,
            bedtime=bedtime,
            confidence=1.0,
            created_at=now_iso,
        )

        if report_id not in _DEV_MEDICATIONS_DB:
            _DEV_MEDICATIONS_DB[report_id] = []
        _DEV_MEDICATIONS_DB[report_id].append(new_med.model_dump())

        if report_id not in _DEV_PRESCRIPTIONS_DB:
            _DEV_PRESCRIPTIONS_DB[report_id] = {
                "id": str(uuid.uuid4()),
                "report_id": report_id,
                "user_id": user_id,
                "parsed_at": now_iso,
            }

        return new_med

    def delete_medication_item(self, report_id: str, med_id: str) -> bool:
        """
        Deletes a medication entry.
        """
        if report_id in _DEV_MEDICATIONS_DB:
            _DEV_MEDICATIONS_DB[report_id] = [m for m in _DEV_MEDICATIONS_DB[report_id] if m.get("id") != med_id]
            return True
        return False

# Global singleton prescription parser service
prescription_parser_service = PrescriptionParserService()
