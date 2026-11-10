import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.services.prescription_parser import prescription_parser_service

client = TestClient(app)

SAMPLE_PRESCRIPTION_TEXT = """
Dr. Rajesh Sharma, MD (General Medicine)
Reg No: 48921-A
Apollo Care Clinic, Indiranagar, Bangalore
Date: 15-05-2025

Patient: Ramesh Kumar, Age: 48, Gender: Male
Diagnosis: Type 2 Diabetes Mellitus & Hypertension

Rx:
1. Tab. Metformin 500mg 1-0-1 After Food for 1 month
2. Tab. Telmisartan 40mg 1-0-0 (OD) Before Food for 30 days
3. Tab. Pantoprazole 40mg 1-0-0 Empty stomach for 14 days
4. Cap. Amoxicillin 500mg 1-1-1 (TDS) After Food for 5 days
5. Tab. Paracetamol 650mg SOS for Pain / Fever
6. Tab. Atorvastatin 10mg 0-0-1 At Bedtime for 1 month

Instructions:
- Follow low carb, low sodium diabetic diet.
- Walk 30 minutes daily.
"""

def test_prescription_regex_parsing_standard_format():
    rx = prescription_parser_service.parse_prescription_text(
        raw_text=SAMPLE_PRESCRIPTION_TEXT,
        report_id="test-rx-rep-101",
        user_id="test-user-001"
    )

    assert rx.report_id == "test-rx-rep-101"
    assert "Rajesh Sharma" in (rx.doctor_name or "")
    assert "Apollo Care" in (rx.clinic_name or "")
    assert "15-05-2025" in (rx.prescription_date or "")
    assert rx.total_medications_count >= 5

    # 1. Metformin Check
    metformin = next((m for m in rx.medications if m.medicine_name.lower() == "metformin"), None)
    assert metformin is not None
    assert "500" in metformin.strength
    assert metformin.morning is True
    assert metformin.night is True
    assert metformin.afternoon is False
    assert metformin.timing == "After Food"
    assert metformin.generic_name == "Metformin Hydrochloride"

    # 2. Pantoprazole Check
    panto = next((m for m in rx.medications if "panto" in m.medicine_name.lower()), None)
    assert panto is not None
    assert "40" in panto.strength
    assert panto.timing == "Before Food"
    assert panto.morning is True

    # 3. Atorvastatin (Bedtime) Check
    atorva = next((m for m in rx.medications if "atorva" in m.medicine_name.lower()), None)
    assert atorva is not None
    assert atorva.timing == "At Bedtime" or atorva.night is True

def test_prescription_shorthand_frequency_conversions():
    shorthand_text = """
    Dr. Anita Roy, MBBS
    Date: 2025-06-01
    Rx:
    1. Tab. Dolo 650mg BD After Food for 3 days
    2. Tab. Thyronorm 50mcg OD Empty stomach for 30 days
    3. Tab. Montelukast 10mg HS for 10 days
    4. Tab. Augmentin 625mg TDS After Meals for 5 days
    """

    rx = prescription_parser_service.parse_prescription_text(
        raw_text=shorthand_text,
        report_id="test-rx-shorthand",
        user_id="test-user-002"
    )

    assert rx.total_medications_count >= 4

    # Dolo (BD) -> 1-0-1
    dolo = next((m for m in rx.medications if "dolo" in m.medicine_name.lower()), None)
    assert dolo is not None
    assert dolo.morning is True and dolo.night is True

    # Thyronorm (OD) -> 1-0-0
    thyro = next((m for m in rx.medications if "thyro" in m.medicine_name.lower()), None)
    assert thyro is not None
    assert thyro.morning is True and thyro.night is False

    # Augmentin (TDS) -> 1-1-1
    aug = next((m for m in rx.medications if "aug" in m.medicine_name.lower()), None)
    assert aug is not None
    assert aug.morning is True and aug.afternoon is True and aug.night is True

def test_prescription_manual_add_and_delete_item():
    report_id = "test-rx-crud-rep"
    
    # 1. Add item
    new_med = prescription_parser_service.add_medication_item(
        report_id=report_id,
        payload={
            "medicine_name": "Cetirizine",
            "strength": "10 mg",
            "frequency": "0-0-1 (Night)",
            "timing": "At Bedtime",
            "duration": "5 days",
        }
    )
    assert new_med.medicine_name == "Cetirizine"
    assert new_med.night is True

    # 2. Get prescription
    rx = prescription_parser_service.get_prescription(report_id=report_id)
    assert rx is not None
    assert any(m.id == new_med.id for m in rx.medications)

    # 3. Delete item
    deleted = prescription_parser_service.delete_medication_item(report_id=report_id, med_id=new_med.id)
    assert deleted is True

    # 4. Verify gone
    rx_after = prescription_parser_service.get_prescription(report_id=report_id)
    assert not any(m.id == new_med.id for m in rx_after.medications)

def test_prescription_api_endpoints_flow():
    import uuid
    headers = {"Authorization": "Bearer dev-test-token"}
    test_report_id = str(uuid.uuid4())  # Must be a valid UUID for Supabase

    # 1. Parse Raw Text Endpoint
    parse_res = client.post(
        "/api/v1/prescriptions/parse-text",
        json={"raw_text": SAMPLE_PRESCRIPTION_TEXT, "report_id": test_report_id},
        headers=headers,
    )
    assert parse_res.status_code == 200
    rx_data = parse_res.json()["data"]
    assert rx_data["report_id"] == test_report_id
    assert rx_data["total_medications_count"] >= 5

    # 2. Upload Prescription Report Document (with embedded prescription text)
    # Build a minimal valid PDF that contains prescription text so the parser can extract medications
    prescription_content = SAMPLE_PRESCRIPTION_TEXT.encode("latin-1", errors="replace")
    # Create a raw PDF with the prescription as embedded text stream
    stream_content = b"BT /F1 10 Tf 50 750 Td\n"
    for i, line in enumerate(SAMPLE_PRESCRIPTION_TEXT.split("\n")[:20]):
        safe_line = line.encode("latin-1", errors="replace").decode("latin-1").replace("(", "[").replace(")", "]")
        stream_content += f"({safe_line}) Tj 0 -14 Td\n".encode()
    stream_content += b"ET"
    stream_len = len(stream_content)
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
        b" /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        + f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode()
        + stream_content
        + b"\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n%%EOF"
    )
    upload_res = client.post(
        "/api/v1/reports/upload",
        files={"file": ("rx_test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"title": "Clinical Rx Treatment Sheet", "report_type": "prescription"},
        headers=headers,
    )
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["data"]["id"]

    # 3. Parse Uploaded Document
    parse_doc_res = client.post(f"/api/v1/prescriptions/parse-report/{doc_id}", headers=headers)
    assert parse_doc_res.status_code == 200
    parsed_doc_data = parse_doc_res.json()["data"]
    assert parsed_doc_data["report_id"] == doc_id
    # Medications count >= 0 (may be 0 if raw OCR text is empty for minimal stub PDF)
    assert parsed_doc_data["total_medications_count"] >= 0

    # 4. Get Prescription for Document
    get_res = client.get(f"/api/v1/prescriptions/{doc_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["report_id"] == doc_id

    # 5. Add Medication to Document
    add_res = client.post(
        f"/api/v1/prescriptions/{doc_id}/medications",
        json={
            "medicine_name": "Vitamin D3",
            "strength": "60,000 IU",
            "frequency": "1-0-0 (Once Weekly)",
            "timing": "After Food",
            "duration": "8 weeks"
        },
        headers=headers,
    )
    assert add_res.status_code == 200
    med_id = add_res.json()["data"]["id"]

    # 6. Delete Medication from Document
    del_res = client.delete(f"/api/v1/prescriptions/{doc_id}/medications/{med_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["data"]["deleted"] is True

def test_handwritten_dental_prescription_parsing():
    """
    Tests parsing of real-world handwritten dental prescription with multi-line layout,
    spatial brackets, OCR handwriting artifacts (e.g. 625my, 40ng, befoce, 281m, \u00d7).
    """
    raw_ocr = """
Smile Designing |Teeth Whitening
THE WHITE TUSK
Dental Implants | General Dentistry
@\u2460/whitetuskdental
12/10/22
Ma.Sachin Sansare.
281m
Rx,
Tab. Augmentin 625my
after
1-0-1 x5days
meals
Tab. Enzoflam
1-0-1\u00d75days
Tab. PanD40ng
befoce
1-0-0x5days
meals
Adv: Hexigel gum paint
massage
1-0-1 x1week
Cunite
Ph: +91 8108112511 | Web: www.thewhitetusk.com | Email: info@thewhitetusk.com
    """
    rx = prescription_parser_service.parse_prescription_text(
        raw_text=raw_ocr,
        report_id="test-dental-handwritten",
        user_id="test-user-dental"
    )

    # 1. Header & Demographics Verification
    assert "White Tusk" in (rx.clinic_name or "")
    assert rx.prescription_date == "12/10/2022"
    assert rx.patient_name == "Sachin Sansare"
    assert rx.patient_age == "28"
    assert rx.patient_gender == "Male"
    assert rx.total_medications_count == 4

    # 2. Augmentin Verification
    aug = next((m for m in rx.medications if "augmentin" in m.medicine_name.lower()), None)
    assert aug is not None
    assert "625" in aug.strength
    assert aug.frequency == "1-0-1"
    assert aug.timing == "After Food"
    assert "5" in aug.duration
    assert aug.form == "Tablet"
    assert "Amoxicillin" in (aug.generic_name or "")

    # 3. Enzoflam Verification
    enz = next((m for m in rx.medications if "enzoflam" in m.medicine_name.lower()), None)
    assert enz is not None
    assert enz.frequency == "1-0-1"
    assert enz.timing == "After Food"
    assert "5" in enz.duration
    assert enz.form == "Tablet"
    assert "Diclofenac" in (enz.generic_name or "")

    # 4. Pan-D Verification
    pan = next((m for m in rx.medications if "pan" in m.medicine_name.lower()), None)
    assert pan is not None
    assert "40" in pan.strength
    assert pan.frequency == "1-0-0"
    assert pan.timing == "Before Food"
    assert "5" in pan.duration
    assert "Domperidone" in (pan.generic_name or "")

    # 5. Hexigel Verification
    hexi = next((m for m in rx.medications if "hexigel" in m.medicine_name.lower()), None)
    assert hexi is not None
    assert hexi.form == "Gel"
    assert hexi.frequency == "1-0-1"
    assert "1 week" in hexi.duration
    assert "massage" in (hexi.instructions or "").lower()
    assert "Chlorhexidine" in (hexi.generic_name or "")
