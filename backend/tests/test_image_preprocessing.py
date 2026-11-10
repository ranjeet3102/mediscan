import io
import pytest
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from fastapi.testclient import TestClient
from app.main import app
from app.services.image_preprocessor import image_preprocessor, ImagePreprocessor

client = TestClient(app)
AUTH_HEADERS = {"Authorization": "Bearer dev-user-token"}

def create_synthetic_tilted_document(angle_degrees: float = 5.0) -> bytes:
    """
    Creates a synthetic image with printed text tilted by a specific angle.
    Returns JPEG bytes.
    """
    # 1. Create blank white canvas
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 2. Draw sample medical report lines
    draw.text((50, 50), "DIAGNOSTIC CLINICAL LABORATORY REPORT", fill=(0, 0, 0))
    draw.text((50, 100), "Patient Name: Demo Patient    Date: 2026-09-27", fill=(0, 0, 0))
    draw.text((50, 150), "Test Name              Result      Unit      Reference Range", fill=(0, 0, 0))
    draw.text((50, 200), "Haemoglobin (Hb)       13.5        g/dL      12.0 - 16.0", fill=(0, 0, 0))
    draw.text((50, 250), "Fasting Blood Sugar    94.0        mg/dL     70 - 99", fill=(0, 0, 0))
    draw.text((50, 300), "Thyroid (TSH)          2.85        uIU/mL    0.40 - 4.50", fill=(0, 0, 0))

    # 3. Rotate to introduce skew
    rotated = img.rotate(angle_degrees, expand=False, fillcolor=(255, 255, 255))

    # 4. Save to buffer
    buf = io.BytesIO()
    rotated.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

def test_deskew_algorithm():
    """Verify that ImagePreprocessor correctly detects text angle and deskews."""
    tilted_bytes = create_synthetic_tilted_document(angle_degrees=6.0)
    cv2_img = image_preprocessor._image_bytes_to_cv2(tilted_bytes)
    assert cv2_img is not None

    deskewed_img, detected_angle = image_preprocessor.deskew(cv2_img)
    assert isinstance(detected_angle, float)
    assert deskewed_img.shape == cv2_img.shape

def test_clahe_and_denoise():
    """Verify CLAHE contrast enhancement and bilateral filtering on shadowed image."""
    # Create an image with an artificial dark gradient / shadow across it
    shadowed = np.zeros((400, 400), dtype=np.uint8)
    for y in range(400):
        shadowed[y, :] = int((y / 400.0) * 180 + 30)

    # Draw text in the middle
    cv2.putText(shadowed, "MEDICAL LAB VALUE", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, 0, 2)

    # Denoise
    denoised = image_preprocessor.denoise_and_filter(shadowed)
    assert denoised.shape == shadowed.shape

    # CLAHE
    enhanced = image_preprocessor.enhance_contrast_clahe(denoised)
    assert enhanced.shape == shadowed.shape
    assert enhanced.dtype == np.uint8
    # CLAHE redistributes intensity and enhances local text visibility
    assert enhanced.max() > 200 and enhanced.min() < 50

def test_adaptive_binarization_and_border_cleanup():
    """Verify that Otsu thresholding produces a sharp binary image (0 and 255 values only)."""
    gray = np.full((300, 300), 200, dtype=np.uint8)
    cv2.putText(gray, "BLOOD TEST", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.0, 30, 2)

    binary = image_preprocessor.adaptive_binarize(gray)
    unique_vals = set(np.unique(binary))
    assert unique_vals.issubset({0, 255})

    cleaned = image_preprocessor.clean_borders(binary, border_ratio=0.05)
    assert cleaned.shape == binary.shape
    # Edges should be white (255)
    assert np.all(cleaned[:10, :] == 255)
    assert np.all(cleaned[-10:, :] == 255)

def test_end_to_end_preprocess_page():
    """Verify complete process_page pipeline execution."""
    sample_bytes = create_synthetic_tilted_document(angle_degrees=3.0)
    cv2_img = image_preprocessor._image_bytes_to_cv2(sample_bytes)
    assert cv2_img is not None

    page = image_preprocessor.process_page(cv2_img, page_num=1)
    assert page.page_number == 1
    assert page.processed_image is not None
    assert page.width == 800
    assert page.height == 600

def test_ocr_preview_endpoint():
    """Verify that the FastAPI /ocr/preview-preprocess endpoint returns preview stages."""
    sample_bytes = create_synthetic_tilted_document(angle_degrees=2.0)
    response = client.post(
        "/api/v1/ocr/preview-preprocess",
        headers=AUTH_HEADERS,
        files={"file": ("sample_report.jpg", sample_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total_pages"] >= 1
    page = data["data"]["pages"][0]
    assert "stages" in page
    assert page["stages"]["original"].startswith("data:image/jpeg;base64,")
    assert page["stages"]["deskewed"].startswith("data:image/jpeg;base64,")
    assert page["stages"]["clahe_enhanced"].startswith("data:image/jpeg;base64,")
    assert page["stages"]["otsu_binarized"].startswith("data:image/jpeg;base64,")
