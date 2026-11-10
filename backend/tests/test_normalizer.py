import pytest
from app.services.normalizer import biomarker_normalizer, BiomarkerNameNormalizer

def test_exact_alias_normalization():
    # Test Haemoglobin aliases
    assert biomarker_normalizer.normalize("Hb").normalized_name == "Haemoglobin"
    assert biomarker_normalizer.normalize("HGB").normalized_name == "Haemoglobin"
    assert biomarker_normalizer.normalize("Hemoglobin").normalized_name == "Haemoglobin"
    assert biomarker_normalizer.normalize("Total Haemoglobin").normalized_name == "Haemoglobin"

    # Test Glucose / Diabetes aliases
    assert biomarker_normalizer.normalize("FBS").normalized_name == "Fasting Blood Glucose"
    assert biomarker_normalizer.normalize("Glucose Fasting").normalized_name == "Fasting Blood Glucose"
    assert biomarker_normalizer.normalize("Blood Sugar Fasting").normalized_name == "Fasting Blood Glucose"
    assert biomarker_normalizer.normalize("PPBS").normalized_name == "Post Prandial Blood Glucose"
    assert biomarker_normalizer.normalize("HbA1c").normalized_name == "Glycated Hemoglobin (HbA1c)"

    # Test Renal & Liver Function aliases
    assert biomarker_normalizer.normalize("S. Creatinine").normalized_name == "Serum Creatinine"
    assert biomarker_normalizer.normalize("Blood Urea").normalized_name == "Blood Urea"
    assert biomarker_normalizer.normalize("SGOT").normalized_name == "SGOT / AST"
    assert biomarker_normalizer.normalize("SGPT").normalized_name == "SGPT / ALT"
    assert biomarker_normalizer.normalize("ALP").normalized_name == "Alkaline Phosphatase (ALP)"

    # Test Thyroid aliases
    assert biomarker_normalizer.normalize("TSH").normalized_name == "Thyroid Stimulating Hormone (TSH)"
    assert biomarker_normalizer.normalize("Total T3").normalized_name == "Total Triiodothyronine (Total T3)"
    assert biomarker_normalizer.normalize("Free T4").normalized_name == "Free Thyroxine (Free T4)"

def test_fuzzy_matching_ocr_typos():
    # OCR typo: '1' for 'l'/'i'
    res1 = biomarker_normalizer.normalize("Haemoglob1n")
    assert res1.normalized_name == "Haemoglobin"
    assert res1.match_type in ["EXACT", "FUZZY"]

    # OCR typo: '0' for 'o'
    res2 = biomarker_normalizer.normalize("Bl00d Urea")
    assert res2.normalized_name == "Blood Urea"

    # OCR typo: '0' in Cholesterol
    res3 = biomarker_normalizer.normalize("Cholester0l")
    assert res3.normalized_name == "Total Cholesterol"

    # OCR typo: '@' for 'a'
    res4 = biomarker_normalizer.normalize("Cre@tinine")
    assert res4.normalized_name == "Serum Creatinine"

    # OCR typo: 'Thyr0id'
    res5 = biomarker_normalizer.normalize("Thyr0id Stimulating Hormone")
    assert res5.normalized_name == "Thyroid Stimulating Hormone (TSH)"

def test_unrecognized_test_name():
    res = biomarker_normalizer.normalize("Custom Experimental Biomarker XYZ99")
    assert res.normalized_name == "Custom Experimental Biomarker XYZ99"
    assert res.match_type == "UNRECOGNIZED"
    assert res.category == "Other Diagnostic Tests"
