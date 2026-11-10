import pytest
from app.services.confidence_verifier import confidence_engine
from app.services.parser import medical_parser

def test_high_confidence_verified_item():
    res = confidence_engine.verify(
        raw_test_name="Haemoglobin",
        value_numeric=14.5,
        unit="g/dL",
        reference_range_raw="13.0 - 17.0",
        ocr_confidence=98.0,
    )
    assert res.verification_status == "verified"
    assert res.is_outlier is False
    assert res.composite_confidence >= 85.0
    assert "High multi-factor confidence" in res.verification_reason or "Verified" in res.verification_reason

def test_low_ocr_confidence_triggers_needs_review():
    res = confidence_engine.verify(
        raw_test_name="Haemoglobin",
        value_numeric=14.5,
        unit="g/dL",
        reference_range_raw="13.0 - 17.0",
        ocr_confidence=40.0,
    )
    assert res.verification_status == "needs_review"
    assert "Low OCR confidence" in res.verification_reason

def test_negative_value_flagged_as_outlier():
    res = confidence_engine.verify(
        raw_test_name="Serum Creatinine",
        value_numeric=-1.2,
        unit="mg/dL",
        reference_range_raw="0.6 - 1.2",
        ocr_confidence=95.0,
    )
    assert res.is_outlier is True
    assert res.verification_status == "needs_review"
    assert "Negative value" in res.verification_reason

def test_physiologically_impossible_value():
    # 450 g/dL Haemoglobin is impossible (normal is 12-17.5, max survivable is ~30)
    res = confidence_engine.verify(
        raw_test_name="Hb",
        value_numeric=450.0,
        unit="g/dL",
        reference_range_raw="12.0 - 16.0",
        ocr_confidence=95.0,
    )
    assert res.is_outlier is True
    assert res.verification_status == "needs_review"
    assert "exceeds physiological limit" in res.verification_reason

def test_user_corrected_status_preservation():
    res = confidence_engine.verify(
        raw_test_name="Hb",
        value_numeric=14.0,
        unit="g/dL",
        ocr_confidence=50.0,
        current_status="user_corrected",
    )
    assert res.verification_status == "user_corrected"
    assert res.composite_confidence == 100.0

def test_parser_end_to_end_with_verification():
    sample_text = """
    CLINICAL PATHOLOGY LABORATORY REPORT
    Haemoglob1n (Hb)    14.2   g/dL     13.0 - 17.0
    Fasting Glucose     92.0   mg/dL    70 - 99
    S. Creatinine       0.95   mg/dL    0.6 - 1.2
    Total Cholesterol   185.0  mg/dL    < 200
    TSH                 2.45   uIU/mL   0.35 - 4.50
    """
    results = medical_parser.parse_text(sample_text, default_confidence=96.0)
    assert len(results) == 5

    hb_item = next(r for r in results if r.normalized_name == "Haemoglobin")
    assert hb_item.raw_test_name == "Haemoglob1n (Hb)"
    assert hb_item.normalized_name == "Haemoglobin"
    assert hb_item.category == "Complete Blood Count (CBC)"
    assert hb_item.value_numeric == 14.2
    assert hb_item.unit == "g/dL"
    assert hb_item.flag == "NORMAL"
    assert hb_item.verification_status == "verified"
    assert hb_item.composite_confidence >= 85.0
