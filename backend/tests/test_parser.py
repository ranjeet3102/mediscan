import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.parser import medical_parser, MedicalReportParser

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer dev-user-token"}

SAMPLE_CBC_REPORT_TEXT = """
DIAGNOSTIC CLINICAL LABORATORY REPORT
Department of Haematology

Test Name              Result      Unit          Reference Range
Haemoglobin (Hb)       11.2        g/dL          12.0 - 16.0
Total Leucocyte Count  11800       cells/mcL     4000 - 11000
RBC Count              4.5         10^6/uL       4.0 - 5.5
Packed Cell Volume     34.0        %             36.0 - 46.0
Platelet Count         135000      /cumm         150000 - 450000
MCV                    78.0        fL            80 - 100
MCH                    26.0        pg            27 - 32
MCHC                   32.5        g/dL          32 - 36
"""

SAMPLE_LIPID_THYROID_TEXT = """
BIOCHEMISTRY REPORT
Investigation          Observed Value    Unit      Reference Interval
Total Cholesterol      235               mg/dL     < 200
Triglycerides          140               mg/dL     < 150
HDL Cholesterol        36                mg/dL     > 40
LDL Cholesterol        165               mg/dL     < 100
TSH - Thyroid Stim     6.20              uIU/mL    0.40 - 4.50
Fasting Blood Sugar    118               mg/dL     70 - 99
Serum Creatinine       0.95              mg/dL     0.70 - 1.30
"""

def test_reference_range_parser():
    """Verify parsing of various standard clinical reference boundary formats."""
    # 1. Range format "min - max"
    r1 = medical_parser.parse_reference_range("12.0 - 16.0")
    assert r1.ref_min == 12.0
    assert r1.ref_max == 16.0

    # 2. Less than "< max"
    r2 = medical_parser.parse_reference_range("< 200")
    assert r2.ref_min is None
    assert r2.ref_max == 200.0

    # 3. Greater than "> min"
    r3 = medical_parser.parse_reference_range("> 40")
    assert r3.ref_min == 40.0
    assert r3.ref_max is None

    # 4. Word format "70 to 99"
    r4 = medical_parser.parse_reference_range("70 to 99")
    assert r4.ref_min == 70.0
    assert r4.ref_max == 99.0

def test_determine_flag():
    """Verify diagnostic status flags: NORMAL, LOW, HIGH, CRITICAL."""
    # Value below min
    assert medical_parser.determine_flag(11.2, None, 12.0, 16.0) == "LOW"
    # Value within bounds
    assert medical_parser.determine_flag(13.5, None, 12.0, 16.0) == "NORMAL"
    # Value above max
    assert medical_parser.determine_flag(6.2, None, 0.40, 4.50) == "HIGH"
    # Value above '< 200'
    assert medical_parser.determine_flag(235.0, None, None, 200.0) == "HIGH"
    # Value below '> 40'
    assert medical_parser.determine_flag(36.0, None, 40.0, None) == "LOW"

def test_parse_cbc_report():
    """Verify structured parsing of Complete Blood Count (CBC) test lines."""
    results = medical_parser.parse_text(SAMPLE_CBC_REPORT_TEXT)
    assert len(results) >= 6

    # Verify Haemoglobin
    hb = next((r for r in results if "haemoglobin" in r.raw_test_name.lower() or "hb" in r.raw_test_name.lower()), None)
    assert hb is not None
    assert hb.value_numeric == 11.2
    assert hb.unit == "g/dL"
    assert hb.ref_min == 12.0
    assert hb.ref_max == 16.0
    assert hb.flag == "LOW"

    # Verify Total Leucocyte Count
    wbc = next((r for r in results if "leucocyte" in r.raw_test_name.lower()), None)
    assert wbc is not None
    assert wbc.value_numeric == 11800.0
    assert wbc.flag == "HIGH"

    # Verify Platelet Count
    plt = next((r for r in results if "platelet" in r.raw_test_name.lower()), None)
    assert plt is not None
    assert plt.value_numeric == 135000.0
    assert plt.flag == "LOW"

def test_parse_lipid_and_thyroid_report():
    """Verify structured parsing of Lipid Profile, TSH, and Blood Sugar."""
    results = medical_parser.parse_text(SAMPLE_LIPID_THYROID_TEXT)
    assert len(results) >= 5

    # TSH
    tsh = next((r for r in results if "tsh" in r.raw_test_name.lower()), None)
    assert tsh is not None
    assert tsh.value_numeric == 6.20
    assert tsh.unit == "uIU/mL"
    assert tsh.flag == "HIGH"

    # Total Cholesterol
    chol = next((r for r in results if "cholesterol" in r.raw_test_name.lower() and "total" in r.raw_test_name.lower()), None)
    assert chol is not None
    assert chol.value_numeric == 235.0
    assert chol.ref_max == 200.0
    assert chol.flag == "HIGH"

def test_structured_extraction_and_results_api():
    """Verify POST /api/v1/reports/{id}/extract-structured and GET test-results endpoints."""
    # 1. Upload a report
    from tests.test_image_preprocessing import create_synthetic_tilted_document
    sample_bytes = create_synthetic_tilted_document(angle_degrees=0.0)
    upload_res = client.post(
        "/api/v1/reports/upload",
        headers=AUTH_HEADERS,
        data={"title": "Comprehensive Health Check"},
        files={"file": ("comprehensive.jpg", sample_bytes, "image/jpeg")}
    )
    report_id = upload_res.json()["data"]["id"]

    # 2. Extract structured test results
    extract_res = client.post(
        f"/api/v1/reports/{report_id}/extract-structured",
        headers=AUTH_HEADERS
    )
    assert extract_res.status_code == 200
    extract_data = extract_res.json()
    assert extract_data["success"] is True
    assert extract_data["data"]["total_extracted"] > 0

    # 3. Get test results list
    results_res = client.get(
        f"/api/v1/reports/{report_id}/test-results",
        headers=AUTH_HEADERS
    )
    assert results_res.status_code == 200
    results_list = results_res.json()
    assert len(results_list) > 0
    first_test = results_list[0]
    assert "raw_test_name" in first_test
    assert "flag" in first_test
    assert first_test["flag"] in ["NORMAL", "LOW", "HIGH", "CRITICAL", "UNCERTAIN"]
    result_id = first_test["id"]

    # 4. Update/correct a test result manually
    update_res = client.put(
        f"/api/v1/reports/test-results/{result_id}",
        headers=AUTH_HEADERS,
        json={
            "value_numeric": 14.0,
            "verification_status": "user_corrected"
        }
    )
    assert update_res.status_code == 200
    assert update_res.json()["success"] is True
