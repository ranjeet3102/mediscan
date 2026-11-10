"""
Test digital PDF text extraction from a PDF that matches the user's actual lab report structure.
This verifies pdfplumber correctly extracts values & reference ranges from a digital PDF.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import io

def create_test_pdf() -> bytes:
    """Create a minimal PDF with embedded text that matches the user's actual lab report."""
    try:
        import reportlab.pdfgen.canvas as rlcanvas
        from reportlab.lib.pagesizes import A4
        buf = io.BytesIO()
        c = rlcanvas.Canvas(buf, pagesize=A4)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 780, "CLINICAL LABORATORY REPORT")
        c.setFont("Helvetica", 10)
        c.drawString(50, 750, "Test-data notice: All patient information and values in this document are fictional.")
        c.setFont("Helvetica-Bold", 10)
        y = 710
        headers = ["Test", "Result", "Unit", "Reference Range", "Flag"]
        x_positions = [50, 200, 290, 360, 470]
        for i, h in enumerate(headers):
            c.drawString(x_positions[i], y, h)
        c.setFont("Helvetica", 10)
        rows = [
            ["Haemoglobin", "12.1", "g/dL", "13.0-17.0", "LOW"],
            ["WBC Count", "7800", "/uL", "4000-11000", ""],
            ["Platelet Count", "245", "x10^3/uL", "150-450", ""],
            ["Fasting Glucose", "112", "mg/dL", "70-99", "HIGH"],
            ["HbA1c", "5.8", "%", "4.0-5.6", "HIGH"],
            ["Creatinine", "0.94", "mg/dL", "0.70-1.30", ""],
            ["ALT (SGPT)", "44", "U/L", "7-45", ""],
            ["Total Cholesterol", "221", "mg/dL", "<200", "HIGH"],
            ["LDL Cholesterol", "135", "mg/dL", "<100", "HIGH"],
            ["TSH", "4.8", "mIU/L", "0.40-4.00", "HIGH"],
        ]
        for row in rows:
            y -= 25
            for i, cell in enumerate(row):
                c.drawString(x_positions[i], y, cell)
        c.save()
        return buf.getvalue()
    except ImportError:
        # Fallback: create PDF using raw PDF syntax
        pdf = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj

2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj

3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj

4 0 obj
<< /Length 800 >>
stream
BT
/F1 12 Tf
50 750 Td
(CLINICAL LABORATORY REPORT) Tj
0 -40 Td
(Test                Result    Unit      Reference Range  Flag) Tj
0 -20 Td
(Haemoglobin         12.1      g/dL      13.0-17.0        LOW) Tj
0 -20 Td
(WBC Count           7800      /uL       4000-11000) Tj
0 -20 Td
(Platelet Count      245       x10^3/uL  150-450) Tj
0 -20 Td
(Fasting Glucose     112       mg/dL     70-99            HIGH) Tj
0 -20 Td
(HbA1c               5.8       %         4.0-5.6          HIGH) Tj
0 -20 Td
(Creatinine          0.94      mg/dL     0.70-1.30) Tj
0 -20 Td
(ALT (SGPT)          44        U/L       7-45) Tj
0 -20 Td
(Total Cholesterol   221       mg/dL     <200             HIGH) Tj
0 -20 Td
(LDL Cholesterol     135       mg/dL     <100             HIGH) Tj
0 -20 Td
(TSH                 4.8       mIU/L     0.40-4.00        HIGH) Tj
ET
endstream
endobj

5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj

xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000001118 00000 n

trailer
<< /Size 6 /Root 1 0 R >>
startxref
1200
%%EOF"""
        return pdf


def test_digital_pdf_extraction():
    """Test that pdfplumber correctly reads values from a digital PDF."""
    print("=" * 60)
    print("Testing Digital PDF Text Extraction")
    print("=" * 60)

    pdf_bytes = create_test_pdf()
    print(f"Created test PDF: {len(pdf_bytes)} bytes")

    # Test pdfplumber
    import pdfplumber
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"\n--- pdfplumber Page {i+1} ---")
            # Try table extraction first
            tables = page.extract_tables()
            if tables:
                print("Tables found:")
                for table in tables:
                    for row in table:
                        if row:
                            print("  | " + " | ".join(str(c or '').strip() for c in row))
            else:
                text = page.extract_text(layout=True) or page.extract_text() or ''
                print("Plain text:")
                print(text[:500])

    # Now test through OCR engine
    print("\n--- Testing through OCREngine.process_document() ---")
    from app.services.ocr_engine import ocr_engine
    result = ocr_engine.process_document(pdf_bytes, "application/pdf")
    print(f"Status: {result.overall_status}")
    print(f"Confidence: {result.average_confidence}%")
    print(f"Pages: {result.total_pages}")
    print(f"Text length: {len(result.full_text)} chars")
    print("\n--- Extracted Text ---")
    print(result.full_text[:800])

    # Test parser on extracted text
    print("\n--- Parser Results ---")
    from app.services.parser import medical_parser
    parsed = medical_parser.parse_text(result.full_text)
    print(f"Parsed {len(parsed)} biomarkers:")
    for item in parsed:
        print(f"  {item.normalized_name:30s} Value={item.value_numeric:8} Unit={item.unit or '':10s} "
              f"Range={item.ref_min}-{item.ref_max}  Flag={item.flag}")

    print("\n" + "=" * 60)
    print("EXPECTED: Haemoglobin 12.1, ref 13.0-17.0, flag LOW")
    print("EXPECTED: Total Cholesterol 221, flag HIGH")
    print("EXPECTED: TSH 4.8, ref 0.40-4.00, flag HIGH")
    print("=" * 60)

if __name__ == "__main__":
    test_digital_pdf_extraction()
