import re
import difflib
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

logger = logging.getLogger("medical_ocr.normalizer")

@dataclass
class CanonicalBiomarker:
    canonical_name: str
    category: str
    aliases: List[str]
    standard_units: List[str]
    plausible_min: float
    plausible_max: float
    default_ref_min: Optional[float] = None
    default_ref_max: Optional[float] = None

@dataclass
class NormalizationResult:
    raw_name: str
    normalized_name: str
    category: str
    match_type: str  # EXACT, ALIAS, FUZZY, UNRECOGNIZED
    confidence_score: float  # 0.0 to 100.0
    canonical_info: Optional[CanonicalBiomarker] = None

# ==============================================================================
# Comprehensive Standard Clinical Biomarker Taxonomy & Reference Bounds
# ==============================================================================
BIOMARKER_TAXONOMY: List[CanonicalBiomarker] = [
    # ---------------- Complete Blood Count (CBC) ----------------
    CanonicalBiomarker(
        canonical_name="Haemoglobin",
        category="Complete Blood Count (CBC)",
        aliases=["hb", "hgb", "hemoglobin", "haemoglobin", "heamoglobin", "total haemoglobin", "total hemoglobin", "hgb/hb", "haemoglob1n"],
        standard_units=["g/dL", "gm/dL", "g/l", "gm%"],
        plausible_min=1.0,
        plausible_max=30.0,
        default_ref_min=12.0,
        default_ref_max=17.5,
    ),
    CanonicalBiomarker(
        canonical_name="RBC Count",
        category="Complete Blood Count (CBC)",
        aliases=["rbc", "red blood cell count", "erythrocyte count", "total rbc", "rbc count", "red blood cells", "rbcs"],
        standard_units=["10^6/uL", "mill/cumm", "mil/cumm", "cells/mcL", "10^6/mcL"],
        plausible_min=0.5,
        plausible_max=12.0,
        default_ref_min=3.8,
        default_ref_max=5.8,
    ),
    CanonicalBiomarker(
        canonical_name="Total Leucocyte Count (WBC)",
        category="Complete Blood Count (CBC)",
        aliases=["wbc", "tlc", "total wbc", "white blood cells", "total leucocyte count", "total leukocyte count", "wbc count", "leukocytes", "leucocytes"],
        standard_units=["/µL", "/uL", "cells/mcL", "/cumm", "cells/cumm", "10^3/uL", "10^3/mcL", "thou/uL"],
        plausible_min=0.5,
        plausible_max=200000.0,
        default_ref_min=4000.0,
        default_ref_max=11000.0,
    ),
    CanonicalBiomarker(
        canonical_name="Platelet Count",
        category="Complete Blood Count (CBC)",
        aliases=["platelets", "platelet", "plt", "thrombocyte count", "total platelet count", "platelet count", "platlets", "platlet count"],
        standard_units=["×10³/µL", "x10³/µL", "×10^3/µL", "x10^3/uL", "10^3/uL", "10³/µL", "/µL", "/uL", "cells/cumm", "lakhs/cumm", "/cumm", "10^5/mcL", "thou/cumm"],
        plausible_min=2.0,
        plausible_max=2500000.0,
        default_ref_min=150.0,
        default_ref_max=450.0,
    ),
    CanonicalBiomarker(
        canonical_name="Packed Cell Volume (PCV)",
        category="Complete Blood Count (CBC)",
        aliases=["pcv", "hematocrit", "hct", "packed cell volume", "haematocrit"],
        standard_units=["%", "ratio"],
        plausible_min=5.0,
        plausible_max=85.0,
        default_ref_min=36.0,
        default_ref_max=50.0,
    ),
    CanonicalBiomarker(
        canonical_name="Mean Corpuscular Volume (MCV)",
        category="Complete Blood Count (CBC)",
        aliases=["mcv", "mean corpuscular volume"],
        standard_units=["fL", "fl", "u3"],
        plausible_min=30.0,
        plausible_max=160.0,
        default_ref_min=80.0,
        default_ref_max=100.0,
    ),
    CanonicalBiomarker(
        canonical_name="Mean Corpuscular Hemoglobin (MCH)",
        category="Complete Blood Count (CBC)",
        aliases=["mch", "mean corpuscular hemoglobin", "mean corpuscular haemoglobin"],
        standard_units=["pg", "uug"],
        plausible_min=10.0,
        plausible_max=60.0,
        default_ref_min=27.0,
        default_ref_max=33.0,
    ),
    CanonicalBiomarker(
        canonical_name="MCHC",
        category="Complete Blood Count (CBC)",
        aliases=["mchc", "mean corpuscular hemoglobin concentration", "mean corpuscular haemoglobin concentration"],
        standard_units=["g/dL", "gm/dL", "%"],
        plausible_min=15.0,
        plausible_max=50.0,
        default_ref_min=31.5,
        default_ref_max=36.0,
    ),
    CanonicalBiomarker(
        canonical_name="Red Cell Distribution Width (RDW)",
        category="Complete Blood Count (CBC)",
        aliases=["rdw", "rdw-cv", "rdw-sd", "red cell distribution width"],
        standard_units=["%", "fL"],
        plausible_min=5.0,
        plausible_max=40.0,
        default_ref_min=11.5,
        default_ref_max=15.0,
    ),
    CanonicalBiomarker(
        canonical_name="Neutrophils",
        category="Differential Leucocyte Count (DLC)",
        aliases=["neutrophils", "polymorphs", "neutrophil", "segs", "segmented neutrophils", "neutro"],
        standard_units=["%", "cells/cumm"],
        plausible_min=0.0,
        plausible_max=100.0,
        default_ref_min=40.0,
        default_ref_max=75.0,
    ),
    CanonicalBiomarker(
        canonical_name="Lymphocytes",
        category="Differential Leucocyte Count (DLC)",
        aliases=["lymphocytes", "lymphocyte", "lymphs", "lymph"],
        standard_units=["%", "cells/cumm"],
        plausible_min=0.0,
        plausible_max=100.0,
        default_ref_min=20.0,
        default_ref_max=45.0,
    ),
    CanonicalBiomarker(
        canonical_name="Monocytes",
        category="Differential Leucocyte Count (DLC)",
        aliases=["monocytes", "monocyte", "mono"],
        standard_units=["%", "cells/cumm"],
        plausible_min=0.0,
        plausible_max=50.0,
        default_ref_min=2.0,
        default_ref_max=10.0,
    ),
    CanonicalBiomarker(
        canonical_name="Eosinophils",
        category="Differential Leucocyte Count (DLC)",
        aliases=["eosinophils", "eosinophil", "eos", "eosino"],
        standard_units=["%", "cells/cumm"],
        plausible_min=0.0,
        plausible_max=60.0,
        default_ref_min=1.0,
        default_ref_max=6.0,
    ),
    CanonicalBiomarker(
        canonical_name="Basophils",
        category="Differential Leucocyte Count (DLC)",
        aliases=["basophils", "basophil", "baso"],
        standard_units=["%", "cells/cumm"],
        plausible_min=0.0,
        plausible_max=20.0,
        default_ref_min=0.0,
        default_ref_max=2.0,
    ),
    CanonicalBiomarker(
        canonical_name="Erythrocyte Sedimentation Rate (ESR)",
        category="Inflammatory Markers",
        aliases=["esr", "westergren esr", "erythrocyte sedimentation rate", "esr (westergren)"],
        standard_units=["mm/hr", "mm/1st hr", "mm"],
        plausible_min=0.0,
        plausible_max=200.0,
        default_ref_min=0.0,
        default_ref_max=20.0,
    ),

    # ---------------- Diabetes & Glycemic Panel ----------------
    CanonicalBiomarker(
        canonical_name="Fasting Blood Glucose",
        category="Diabetes & Glycemic Panel",
        aliases=["fbs", "fasting glucose", "glucose fasting", "fasting blood sugar", "blood sugar fasting", "fasting plasma glucose", "fpg", "b.s. fasting", "gluc0se fasting"],
        standard_units=["mg/dL", "mmol/L", "mg%"],
        plausible_min=10.0,
        plausible_max=1500.0,
        default_ref_min=70.0,
        default_ref_max=99.0,
    ),
    CanonicalBiomarker(
        canonical_name="Post Prandial Blood Glucose",
        category="Diabetes & Glycemic Panel",
        aliases=["ppbs", "post prandial glucose", "glucose pp", "postprandial glucose", "blood sugar pp", "post prandial blood sugar", "ppbg", "b.s. pp", "2hr post prandial glucose"],
        standard_units=["mg/dL", "mmol/L", "mg%"],
        plausible_min=10.0,
        plausible_max=1500.0,
        default_ref_min=70.0,
        default_ref_max=140.0,
    ),
    CanonicalBiomarker(
        canonical_name="Random Blood Glucose",
        category="Diabetes & Glycemic Panel",
        aliases=["rbs", "random glucose", "blood sugar random", "random blood sugar", "grbs", "glucose random"],
        standard_units=["mg/dL", "mmol/L", "mg%"],
        plausible_min=10.0,
        plausible_max=1500.0,
        default_ref_min=70.0,
        default_ref_max=140.0,
    ),
    CanonicalBiomarker(
        canonical_name="Glycated Hemoglobin (HbA1c)",
        category="Diabetes & Glycemic Panel",
        aliases=["hba1c", "glycated hemoglobin", "glycohemoglobin", "a1c", "glycosylated hemoglobin", "hemoglobin a1c", "hba1c - glycated hemoglobin"],
        standard_units=["%", "mmol/mol"],
        plausible_min=2.0,
        plausible_max=25.0,
        default_ref_min=4.0,
        default_ref_max=5.6,
    ),

    # ---------------- Lipid Profile ----------------
    CanonicalBiomarker(
        canonical_name="Total Cholesterol",
        category="Lipid Profile",
        aliases=["cholesterol", "total cholesterol", "serum cholesterol", "cholesterol total", "s. cholesterol", "cholester0l", "t. cholesterol"],
        standard_units=["mg/dL", "mmol/L", "mg%"],
        plausible_min=20.0,
        plausible_max=1500.0,
        default_ref_min=120.0,
        default_ref_max=200.0,
    ),
    CanonicalBiomarker(
        canonical_name="Triglycerides",
        category="Lipid Profile",
        aliases=["triglycerides", "serum triglycerides", "tg", "tgl", "triglyceride", "s. triglycerides"],
        standard_units=["mg/dL", "mmol/L", "mg%"],
        plausible_min=10.0,
        plausible_max=3000.0,
        default_ref_min=50.0,
        default_ref_max=150.0,
    ),
    CanonicalBiomarker(
        canonical_name="HDL Cholesterol",
        category="Lipid Profile",
        aliases=["hdl", "hdl cholesterol", "high density lipoprotein", "serum hdl", "hdl-c", "good cholesterol", "hdl - cholesterol"],
        standard_units=["mg/dL", "mmol/L", "mg%"],
        plausible_min=5.0,
        plausible_max=200.0,
        default_ref_min=40.0,
        default_ref_max=60.0,
    ),
    CanonicalBiomarker(
        canonical_name="LDL Cholesterol",
        category="Lipid Profile",
        aliases=["ldl", "ldl cholesterol", "low density lipoprotein", "serum ldl", "ldl-c", "direct ldl", "bad cholesterol", "ldl - cholesterol"],
        standard_units=["mg/dL", "mmol/L", "mg%"],
        plausible_min=5.0,
        plausible_max=600.0,
        default_ref_min=50.0,
        default_ref_max=100.0,
    ),
    CanonicalBiomarker(
        canonical_name="VLDL Cholesterol",
        category="Lipid Profile",
        aliases=["vldl", "vldl cholesterol", "very low density lipoprotein", "vldl-c", "serum vldl"],
        standard_units=["mg/dL", "mmol/L", "mg%"],
        plausible_min=1.0,
        plausible_max=300.0,
        default_ref_min=5.0,
        default_ref_max=30.0,
    ),
    CanonicalBiomarker(
        canonical_name="Total Cholesterol / HDL Ratio",
        category="Lipid Profile",
        aliases=["cholesterol / hdl ratio", "total cholesterol/hdl ratio", "tc/hdl ratio", "chol/hdl", "cholesterol/hdl ratio"],
        standard_units=["ratio", ""],
        plausible_min=0.5,
        plausible_max=30.0,
        default_ref_min=2.0,
        default_ref_max=5.0,
    ),

    # ---------------- Kidney Function Tests (KFT / RFT) ----------------
    CanonicalBiomarker(
        canonical_name="Serum Creatinine",
        category="Kidney Function Tests (KFT)",
        aliases=["creatinine", "serum creatinine", "s. creatinine", "sr. creatinine", "blood creatinine", "creatin1ne", "cre@tinine"],
        standard_units=["mg/dL", "umol/L", "mg%"],
        plausible_min=0.1,
        plausible_max=30.0,
        default_ref_min=0.6,
        default_ref_max=1.2,
    ),
    CanonicalBiomarker(
        canonical_name="Blood Urea",
        category="Kidney Function Tests (KFT)",
        aliases=["urea", "blood urea", "serum urea", "s. urea", "bl00d urea"],
        standard_units=["mg/dL", "mmol/L", "mg%"],
        plausible_min=2.0,
        plausible_max=500.0,
        default_ref_min=15.0,
        default_ref_max=45.0,
    ),
    CanonicalBiomarker(
        canonical_name="Blood Urea Nitrogen (BUN)",
        category="Kidney Function Tests (KFT)",
        aliases=["bun", "blood urea nitrogen", "s. bun"],
        standard_units=["mg/dL", "mmol/L"],
        plausible_min=1.0,
        plausible_max=250.0,
        default_ref_min=7.0,
        default_ref_max=20.0,
    ),
    CanonicalBiomarker(
        canonical_name="Serum Uric Acid",
        category="Kidney Function Tests (KFT)",
        aliases=["uric acid", "serum uric acid", "s. uric acid", "blood uric acid"],
        standard_units=["mg/dL", "umol/L"],
        plausible_min=0.5,
        plausible_max=30.0,
        default_ref_min=3.5,
        default_ref_max=7.2,
    ),
    CanonicalBiomarker(
        canonical_name="Serum Sodium",
        category="Electrolytes",
        aliases=["sodium", "serum sodium", "na+", "na", "s. sodium"],
        standard_units=["mEq/L", "mmol/L"],
        plausible_min=80.0,
        plausible_max=200.0,
        default_ref_min=135.0,
        default_ref_max=145.0,
    ),
    CanonicalBiomarker(
        canonical_name="Serum Potassium",
        category="Electrolytes",
        aliases=["potassium", "serum potassium", "k+", "k", "s. potassium"],
        standard_units=["mEq/L", "mmol/L"],
        plausible_min=1.0,
        plausible_max=12.0,
        default_ref_min=3.5,
        default_ref_max=5.1,
    ),
    CanonicalBiomarker(
        canonical_name="Serum Chloride",
        category="Electrolytes",
        aliases=["chloride", "serum chloride", "cl-", "cl", "s. chloride"],
        standard_units=["mEq/L", "mmol/L"],
        plausible_min=50.0,
        plausible_max=160.0,
        default_ref_min=96.0,
        default_ref_max=106.0,
    ),
    CanonicalBiomarker(
        canonical_name="Serum Calcium",
        category="Minerals & Bone Metabolism",
        aliases=["calcium", "serum calcium", "total calcium", "ca++", "s. calcium", "ca"],
        standard_units=["mg/dL", "mmol/L"],
        plausible_min=2.0,
        plausible_max=25.0,
        default_ref_min=8.5,
        default_ref_max=10.5,
    ),

    # ---------------- Liver Function Tests (LFT) ----------------
    CanonicalBiomarker(
        canonical_name="Total Bilirubin",
        category="Liver Function Tests (LFT)",
        aliases=["bilirubin total", "total bilirubin", "serum bilirubin", "s. bilirubin total", "t. bilirubin", "b1lirubin total"],
        standard_units=["mg/dL", "umol/L"],
        plausible_min=0.05,
        plausible_max=50.0,
        default_ref_min=0.2,
        default_ref_max=1.2,
    ),
    CanonicalBiomarker(
        canonical_name="Direct Bilirubin",
        category="Liver Function Tests (LFT)",
        aliases=["bilirubin direct", "direct bilirubin", "conjugated bilirubin", "d. bilirubin", "s. bilirubin direct"],
        standard_units=["mg/dL", "umol/L"],
        plausible_min=0.0,
        plausible_max=40.0,
        default_ref_min=0.0,
        default_ref_max=0.3,
    ),
    CanonicalBiomarker(
        canonical_name="Indirect Bilirubin",
        category="Liver Function Tests (LFT)",
        aliases=["bilirubin indirect", "indirect bilirubin", "unconjugated bilirubin", "s. bilirubin indirect"],
        standard_units=["mg/dL", "umol/L"],
        plausible_min=0.0,
        plausible_max=40.0,
        default_ref_min=0.2,
        default_ref_max=0.8,
    ),
    CanonicalBiomarker(
        canonical_name="SGOT / AST",
        category="Liver Function Tests (LFT)",
        aliases=["sgot", "ast", "aspartate aminotransferase", "sgot/ast", "aspartate transaminase", "sgot (ast)", "s.g.o.t."],
        standard_units=["U/L", "IU/L"],
        plausible_min=1.0,
        plausible_max=5000.0,
        default_ref_min=5.0,
        default_ref_max=40.0,
    ),
    CanonicalBiomarker(
        canonical_name="SGPT / ALT",
        category="Liver Function Tests (LFT)",
        aliases=["sgpt", "alt", "alanine aminotransferase", "sgpt/alt", "alanine transaminase", "sgpt (alt)", "s.g.p.t."],
        standard_units=["U/L", "IU/L"],
        plausible_min=1.0,
        plausible_max=5000.0,
        default_ref_min=5.0,
        default_ref_max=45.0,
    ),
    CanonicalBiomarker(
        canonical_name="Alkaline Phosphatase (ALP)",
        category="Liver Function Tests (LFT)",
        aliases=["alkaline phosphatase", "alp", "alk phos", "serum alkaline phosphatase", "s. alp"],
        standard_units=["U/L", "IU/L"],
        plausible_min=5.0,
        plausible_max=2500.0,
        default_ref_min=30.0,
        default_ref_max=120.0,
    ),
    CanonicalBiomarker(
        canonical_name="Total Protein",
        category="Liver Function Tests (LFT)",
        aliases=["total protein", "serum total protein", "protein total", "s. protein", "s. total protein"],
        standard_units=["g/dL", "gm/dL", "g/L"],
        plausible_min=1.0,
        plausible_max=20.0,
        default_ref_min=6.0,
        default_ref_max=8.3,
    ),
    CanonicalBiomarker(
        canonical_name="Serum Albumin",
        category="Liver Function Tests (LFT)",
        aliases=["albumin", "serum albumin", "s. albumin"],
        standard_units=["g/dL", "gm/dL", "g/L"],
        plausible_min=0.5,
        plausible_max=10.0,
        default_ref_min=3.5,
        default_ref_max=5.2,
    ),
    CanonicalBiomarker(
        canonical_name="Serum Globulin",
        category="Liver Function Tests (LFT)",
        aliases=["globulin", "serum globulin", "s. globulin"],
        standard_units=["g/dL", "gm/dL", "g/L"],
        plausible_min=0.5,
        plausible_max=10.0,
        default_ref_min=2.0,
        default_ref_max=3.5,
    ),
    CanonicalBiomarker(
        canonical_name="Albumin / Globulin Ratio (A/G Ratio)",
        category="Liver Function Tests (LFT)",
        aliases=["a/g ratio", "ag ratio", "albumin globulin ratio", "alb/glob ratio", "a : g ratio"],
        standard_units=["ratio", ""],
        plausible_min=0.1,
        plausible_max=10.0,
        default_ref_min=1.0,
        default_ref_max=2.2,
    ),

    # ---------------- Thyroid Profile ----------------
    CanonicalBiomarker(
        canonical_name="Thyroid Stimulating Hormone (TSH)",
        category="Thyroid Profile",
        aliases=["tsh", "thyroid stimulating hormone", "s. tsh", "ultrasensitive tsh", "tsh - thyroid stimulating hormone", "thyr0id stimulating hormone"],
        standard_units=["uIU/mL", "mIU/L", "uIU/L", "uU/mL"],
        plausible_min=0.001,
        plausible_max=250.0,
        default_ref_min=0.35,
        default_ref_max=4.5,
    ),
    CanonicalBiomarker(
        canonical_name="Total Triiodothyronine (Total T3)",
        category="Thyroid Profile",
        aliases=["total t3", "t3", "triiodothyronine", "total triiodothyronine", "s. t3"],
        standard_units=["ng/dL", "nmol/L", "ng/mL"],
        plausible_min=10.0,
        plausible_max=1000.0,
        default_ref_min=80.0,
        default_ref_max=200.0,
    ),
    CanonicalBiomarker(
        canonical_name="Total Thyroxine (Total T4)",
        category="Thyroid Profile",
        aliases=["total t4", "t4", "thyroxine", "total thyroxine", "s. t4"],
        standard_units=["ug/dL", "mcg/dL", "nmol/L"],
        plausible_min=0.1,
        plausible_max=40.0,
        default_ref_min=4.5,
        default_ref_max=12.0,
    ),
    CanonicalBiomarker(
        canonical_name="Free Triiodothyronine (Free T3)",
        category="Thyroid Profile",
        aliases=["free t3", "ft3", "free triiodothyronine"],
        standard_units=["pg/mL", "pmol/L"],
        plausible_min=0.1,
        plausible_max=50.0,
        default_ref_min=2.0,
        default_ref_max=4.4,
    ),
    CanonicalBiomarker(
        canonical_name="Free Thyroxine (Free T4)",
        category="Thyroid Profile",
        aliases=["free t4", "ft4", "free thyroxine"],
        standard_units=["ng/dL", "pmol/L"],
        plausible_min=0.05,
        plausible_max=20.0,
        default_ref_min=0.8,
        default_ref_max=1.8,
    ),

    # ---------------- Vitamins & Micronutrients ----------------
    CanonicalBiomarker(
        canonical_name="Vitamin D3 (25-OH)",
        category="Vitamins & Minerals",
        aliases=["vitamin d", "vitamin d3", "25-oh vitamin d", "25-hydroxy vitamin d", "vit d3", "vit d", "25-oh vit d"],
        standard_units=["ng/mL", "nmol/L"],
        plausible_min=1.0,
        plausible_max=300.0,
        default_ref_min=30.0,
        default_ref_max=100.0,
    ),
    CanonicalBiomarker(
        canonical_name="Vitamin B12",
        category="Vitamins & Minerals",
        aliases=["vitamin b12", "vit b12", "cyanocobalamin", "b12", "serum vitamin b12"],
        standard_units=["pg/mL", "pmol/L"],
        plausible_min=10.0,
        plausible_max=5000.0,
        default_ref_min=200.0,
        default_ref_max=900.0,
    ),
    CanonicalBiomarker(
        canonical_name="Serum Iron",
        category="Iron Profile",
        aliases=["iron", "serum iron", "s. iron"],
        standard_units=["ug/dL", "mcg/dL", "umol/L"],
        plausible_min=5.0,
        plausible_max=600.0,
        default_ref_min=60.0,
        default_ref_max=170.0,
    ),
    CanonicalBiomarker(
        canonical_name="Serum Ferritin",
        category="Iron Profile",
        aliases=["ferritin", "serum ferritin", "s. ferritin"],
        standard_units=["ng/mL", "ug/L"],
        plausible_min=1.0,
        plausible_max=15000.0,
        default_ref_min=15.0,
        default_ref_max=300.0,
    ),
    CanonicalBiomarker(
        canonical_name="C-Reactive Protein (CRP)",
        category="Inflammatory Markers",
        aliases=["crp", "c-reactive protein", "c reactive protein", "hs-crp", "high sensitivity crp"],
        standard_units=["mg/L", "mg/dL"],
        plausible_min=0.01,
        plausible_max=500.0,
        default_ref_min=0.0,
        default_ref_max=5.0,
    ),
]

class BiomarkerNameNormalizer:
    """
    Fuzzy alias normalizer and taxonomy mapper for clinical lab investigations.
    Standardizes noisy OCR strings into unified canonical names.
    """

    def __init__(self, taxonomy: List[CanonicalBiomarker] = BIOMARKER_TAXONOMY):
        self.taxonomy = taxonomy
        # Build direct lookup dictionaries
        self.exact_alias_map: Dict[str, CanonicalBiomarker] = {}
        for bio in self.taxonomy:
            # Canonical name itself
            clean_canonical = self._clean_string(bio.canonical_name)
            self.exact_alias_map[clean_canonical] = bio
            
            # Aliases
            for alias in bio.aliases:
                clean_alias = self._clean_string(alias)
                self.exact_alias_map[clean_alias] = bio

    def _clean_string(self, text: str) -> str:
        """
        Cleans and simplifies string for alias matching:
        - Lowercases
        - Removes special characters and brackets
        - Normalizes whitespace
        - OCR character substitutions applied ONLY to non-numeric substrings
          to fix common OCR confusions in test names (e.g. 'B1lirubin' -> 'bilirubin')
          while preserving pure-numeric tokens intact.
        """
        if not text:
            return ""
        s = text.lower().strip()
        # Remove punctuation except letters, digits and spaces
        s = re.sub(r"[^\w\s]", " ", s)
        # Collapse multi spaces
        s = re.sub(r"\s+", " ", s).strip()
        # Apply OCR character substitutions only on word tokens that aren't purely numeric
        tokens = s.split()
        corrected = []
        for t in tokens:
            if re.match(r'^[0-9.]+$', t):
                # Pure numeric token — do NOT mangle digits
                corrected.append(t)
            else:
                # Non-numeric text token — apply OCR letter/digit confusion fixes
                t = t.replace("@", "a").replace("0", "o").replace("1", "l")
                corrected.append(t)
        return " ".join(corrected)

    def normalize(self, raw_name: str) -> NormalizationResult:
        """
        Maps raw OCR test name to canonical biomarker taxonomy using:
        1. Exact alias lookup
        2. Substring & Token containment lookup
        3. Fuzzy SequenceMatcher ratio calculation
        """
        clean_raw = self._clean_string(raw_name)
        if not clean_raw:
            return NormalizationResult(
                raw_name=raw_name,
                normalized_name=raw_name,
                category="General Lab Findings",
                match_type="UNRECOGNIZED",
                confidence_score=0.0,
            )

        # 1. Exact alias dictionary match
        if clean_raw in self.exact_alias_map:
            bio = self.exact_alias_map[clean_raw]
            return NormalizationResult(
                raw_name=raw_name,
                normalized_name=bio.canonical_name,
                category=bio.category,
                match_type="EXACT",
                confidence_score=100.0,
                canonical_info=bio,
            )

        # 2. Check if clean_raw starts with or exactly contains an alias
        best_match: Optional[CanonicalBiomarker] = None
        best_score: float = 0.0
        best_match_type = "FUZZY"

        for alias, bio in self.exact_alias_map.items():
            if len(alias) >= 3 and (clean_raw == alias or clean_raw.startswith(alias + " ") or clean_raw.endswith(" " + alias)):
                return NormalizationResult(
                    raw_name=raw_name,
                    normalized_name=bio.canonical_name,
                    category=bio.category,
                    match_type="ALIAS",
                    confidence_score=95.0,
                    canonical_info=bio,
                )

        # 3. Fuzzy SequenceMatcher scoring across all canonicals & aliases
        for alias, bio in self.exact_alias_map.items():
            # Calculate similarity ratio
            sim = difflib.SequenceMatcher(None, clean_raw, alias).ratio()
            if sim > best_score:
                best_score = sim
                best_match = bio

        # If similarity exceeds threshold (e.g. 70%), accept match
        if best_match and best_score >= 0.70:
            score_percent = round(best_score * 100, 1)
            return NormalizationResult(
                raw_name=raw_name,
                normalized_name=best_match.canonical_name,
                category=best_match.category,
                match_type="FUZZY",
                confidence_score=score_percent,
                canonical_info=best_match,
            )

        # Fallback for unrecognized test names
        return NormalizationResult(
            raw_name=raw_name,
            normalized_name=raw_name.strip(),
            category="Other Diagnostic Tests",
            match_type="UNRECOGNIZED",
            confidence_score=40.0,
        )

# Global singleton normalizer
biomarker_normalizer = BiomarkerNameNormalizer()

