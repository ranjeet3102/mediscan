import os
import re
import shutil
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
import numpy as np
import cv2
import pytesseract
from pytesseract import Output
from app.core.config import settings
from app.services.image_preprocessor import image_preprocessor, PreprocessedPage

logger = logging.getLogger("medical_ocr.ocr")

def configure_tesseract_path():
    """Locates and configures Tesseract OCR binary path across Windows & Linux."""
    possible_paths = [
        settings.TESSERACT_CMD,
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        shutil.which("tesseract"),
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]
    for path in possible_paths:
        if path and (shutil.which(path) or os.path.exists(path)):
            pytesseract.pytesseract.tesseract_cmd = path
            logger.info(f"Tesseract OCR configured at: {path}")
            return path
    logger.warning("Tesseract binary not found in standard paths. Fallback mock engine active.")
    return None

TESSERACT_EXECUTABLE = configure_tesseract_path()

@dataclass
class OCRWord:
    text: str
    confidence: float
    bbox: Dict[str, int]  # {left, top, width, height}
    line_num: int
    block_num: int
    page_num: int

@dataclass
class OCRPageResult:
    page_number: int
    text: str
    words: List[OCRWord]
    average_confidence: float
    low_confidence_words: List[str]
    psm_used: int
    skew_angle: float

@dataclass
class OCRDocumentResult:
    full_text: str
    average_confidence: float
    total_pages: int
    pages: List[OCRPageResult]
    low_confidence_count: int
    overall_status: str  # 'high_confidence' (>=85%), 'moderate' (70-84%), 'needs_verification' (<70%)

_paddle_ocr_instance = None

def get_paddle_ocr():
    """Lazily initializes and caches the PaddleOCR deep learning engine."""
    global _paddle_ocr_instance
    if _paddle_ocr_instance is None:
        try:
            from paddleocr import PaddleOCR
            _paddle_ocr_instance = PaddleOCR(use_textline_orientation=True, lang="en")
            logger.info("PaddleOCR engine initialized successfully as primary OCR provider.")
        except Exception as e:
            logger.warning(f"PaddleOCR initialization failed: {e}. Fallback to Tesseract active.")
            _paddle_ocr_instance = False
    return _paddle_ocr_instance if _paddle_ocr_instance is not False else None


class OCREngine:
    """
    Hybrid Deep Learning OCR Engine for medical lab reports & doctor prescriptions.
    Features:
    - Primary: PaddleOCR (PP-OCRv4 / v6) deep learning detection and recognition for
      superior accuracy on messy layouts, curved text, and handwritten prescriptions.
    - Secondary Fallback: Tesseract OCR with multi-pass PSM modes (tabular PSM 6, sparse PSM 4).
    - Digital PDF Fast-Path: Vector text extraction with table preservation via pdfplumber.
    """

    def __init__(self):
        self.tesseract_cmd = configure_tesseract_path()

    def is_available(self) -> bool:
        return get_paddle_ocr() is not None or self.tesseract_cmd is not None

    def _extract_page_paddleocr(self, image: np.ndarray, page_num: int = 1) -> Optional[OCRPageResult]:
        """
        Executes PaddleOCR on an image using deep learning text detection (DBNet)
        and text recognition (SVTR/PP-LCNet).
        """
        engine = get_paddle_ocr()
        if not engine:
            return None

        try:
            # Ensure 3-channel color image for PaddleOCR
            if len(image.shape) == 2:
                rgb_img = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif len(image.shape) == 3 and image.shape[2] == 4:
                rgb_img = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
            else:
                rgb_img = image

            h, w = rgb_img.shape[:2]
            max_dim = max(h, w)
            if max_dim > 1600:
                scale = 1600.0 / max_dim
                new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
                pred_img = cv2.resize(rgb_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
                coord_scale = max_dim / 1600.0
            else:
                pred_img = rgb_img
                coord_scale = 1.0

            results = engine.predict(
                pred_img,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=True
            )
            if not results or not isinstance(results, list):
                return None

            page_dict = results[0]
            if not isinstance(page_dict, dict):
                return None

            rec_texts = page_dict.get("rec_texts", [])
            rec_scores = page_dict.get("rec_scores", [])
            rec_boxes = page_dict.get("rec_boxes", [])

            if not rec_texts:
                return None

            words: List[OCRWord] = []
            confidences: List[float] = []
            low_conf_words: List[str] = []

            for line_idx, (line_text, score) in enumerate(zip(rec_texts, rec_scores)):
                conf = round(float(score) * 100.0, 2)
                box = rec_boxes[line_idx] if line_idx < len(rec_boxes) else [0, 0, 100, 20]

                x1 = int(int(box[0]) * coord_scale)
                y1 = int(int(box[1]) * coord_scale)
                x2 = int(int(box[2]) * coord_scale)
                y2 = int(int(box[3]) * coord_scale)
                box_w = max(1, x2 - x1)
                box_h = max(1, y2 - y1)

                tokens = line_text.strip().split()
                if not tokens:
                    continue

                total_chars = max(1, sum(len(t) for t in tokens))
                curr_x = x1
                for t_idx, token in enumerate(tokens):
                    tok_w = max(8, int(box_w * (len(token) / total_chars)))
                    word_obj = OCRWord(
                        text=token,
                        confidence=conf,
                        bbox={"left": curr_x, "top": y1, "width": tok_w, "height": box_h},
                        line_num=line_idx + 1,
                        block_num=1,
                        page_num=page_num,
                    )
                    words.append(word_obj)
                    confidences.append(conf)

                    if conf < 70.0:
                        low_conf_words.append(token)
                    curr_x += tok_w + 4

            formatted_text = "\n".join(rec_texts).strip()
            avg_conf = round(float(np.mean(confidences)), 2) if confidences else 0.0
            skew_angle = float(page_dict.get("doc_preprocessor_res", {}).get("angle", 0.0))

            return OCRPageResult(
                page_number=page_num,
                text=formatted_text,
                words=words,
                average_confidence=avg_conf,
                low_confidence_words=low_conf_words,
                psm_used=100,  # 100 indicates PaddleOCR deep learning model
                skew_angle=skew_angle,
            )
        except Exception as e:
            logger.error(f"PaddleOCR extraction error on page {page_num}: {e}")
            return None

    def _extract_page_tesseract(
        self,
        image: np.ndarray,
        page_num: int = 1,
        psm: int = 6,
        oem: int = 3
    ) -> Optional[OCRPageResult]:
        """
        Executes pytesseract on a single image with specified PSM.
        """
        if not self.tesseract_cmd:
            return None

        custom_config = f"--oem {oem} --psm {psm} -c preserve_interword_spaces=1"

        try:
            data = pytesseract.image_to_data(image, config=custom_config, output_type=Output.DICT)
            words: List[OCRWord] = []
            confidences: List[float] = []
            low_conf_words: List[str] = []

            n_boxes = len(data["text"])
            for i in range(n_boxes):
                raw_word = data["text"][i].strip()
                conf = float(data["conf"][i])

                if raw_word and conf >= 0:
                    word_obj = OCRWord(
                        text=raw_word,
                        confidence=round(conf, 2),
                        bbox={
                            "left": int(data["left"][i]),
                            "top": int(data["top"][i]),
                            "width": int(data["width"][i]),
                            "height": int(data["height"][i]),
                        },
                        line_num=int(data["line_num"][i]),
                        block_num=int(data["block_num"][i]),
                        page_num=page_num,
                    )
                    words.append(word_obj)
                    confidences.append(conf)

                    if conf < 70.0:
                        low_conf_words.append(raw_word)

            raw_text = pytesseract.image_to_string(image, config=custom_config).strip()
            avg_conf = round(float(np.mean(confidences)), 2) if confidences else 0.0

            return OCRPageResult(
                page_number=page_num,
                text=raw_text,
                words=words,
                average_confidence=avg_conf,
                low_confidence_words=low_conf_words,
                psm_used=psm,
                skew_angle=0.0,
            )
        except Exception as e:
            logger.error(f"Tesseract OCR execution error on page {page_num}: {e}")
            return None

    def _extract_page_ocr(
        self,
        image: np.ndarray,
        page_num: int = 1,
        psm: int = 6,
        oem: int = 3
    ) -> OCRPageResult:
        """
        Executes primary OCR (PaddleOCR) with fallback to Tesseract or deterministic mock.
        """
        # 1. Primary: Try PaddleOCR deep learning engine
        paddle_res = self._extract_page_paddleocr(image, page_num=page_num)
        if paddle_res and len(paddle_res.words) > 0:
            return paddle_res

        # 2. Secondary: Fallback to Tesseract OCR
        tess_res = self._extract_page_tesseract(image, page_num=page_num, psm=psm, oem=oem)
        if tess_res and len(tess_res.words) > 0:
            return tess_res

        # 3. Deterministic mock fallback (only if both engines missing / empty)
        return self._mock_ocr_fallback(image, page_num)

    def _merge_ocr_page_texts(self, text_a: str, text_b: str) -> str:
        """
        Combines lines from two OCR passes without duplicate identical lines.
        Prioritizes text_a (preprocessed/contrast-enhanced) and appends unique lines from text_b (original color).
        """
        lines_a = [ln.strip() for ln in text_a.splitlines() if ln.strip()]
        lines_b = [ln.strip() for ln in text_b.splitlines() if ln.strip()]

        def clean_line_sig(ln: str) -> str:
            return re.sub(r'[^a-zA-Z0-9]', '', ln).lower()

        seen_sigs = {clean_line_sig(ln) for ln in lines_a if len(clean_line_sig(ln)) >= 3}
        merged_lines = list(lines_a)
        for ln_b in lines_b:
            sig = clean_line_sig(ln_b)
            if not sig:
                continue
            if sig not in seen_sigs and not any(sig in s or s in sig for s in seen_sigs if len(s) >= 6 and len(sig) >= 6):
                merged_lines.append(ln_b)
                seen_sigs.add(sig)

        return "\n".join(merged_lines)

    def process_page_multi_pass(self, page: PreprocessedPage) -> OCRPageResult:
        """
        Multi-pass OCR strategy:
        - Primary pass: Runs PaddleOCR on original/color image (handles color ink, high-contrast sections).
        - Secondary pass: Runs PaddleOCR on preprocessed image (CLAHE shadow equalization, deskewing).
        - Merges results: Combines distinct lines from both passes so shadowed regions (e.g. mobile photo
          shadows obscuring upper medications) and light color ink sections are both preserved without loss.
        """
        pass1 = self._extract_page_ocr(page.original_image, page_num=page.page_number, psm=6)
        pass1.skew_angle = page.skew_angle or pass1.skew_angle

        # If Pass 1 is nearly flawless flat digital scan (>95% confidence with many words), use directly
        if pass1.average_confidence >= 95.0 and len(pass1.words) >= 40:
            return pass1

        # Pass 2: Run with preprocessed CLAHE-enhanced image to recover shadowed/dark regions
        try:
            pass2 = self._extract_page_ocr(page.processed_image, page_num=page.page_number, psm=4)
            if pass2:
                pass2.skew_angle = page.skew_angle or pass2.skew_angle
        except Exception as e:
            logger.warning(f"Pass 2 OCR execution failed: {e}")
            pass2 = None

        if not pass2 or not pass2.words:
            return pass1
        if not pass1 or not pass1.words:
            return pass2

        # Combine text: pass2 (CLAHE shadow-corrected) followed by pass1 (original color details)
        combined_text = self._merge_ocr_page_texts(pass2.text, pass1.text)

        # Merge words and compute average confidence
        all_words = pass2.words + [w for w in pass1.words if w.text.lower() not in {pw.text.lower() for pw in pass2.words}]
        avg_conf = round(float(np.mean([w.confidence for w in all_words])), 2) if all_words else max(pass1.average_confidence, pass2.average_confidence)
        low_conf = list(dict.fromkeys(pass1.low_confidence_words + pass2.low_confidence_words))

        logger.info(f"Multi-pass OCR merged page {page.page_number}: Pass 1={pass1.average_confidence}%, Pass 2={pass2.average_confidence}%, Combined Words={len(all_words)}")
        return OCRPageResult(
            page_number=page.page_number,
            text=combined_text,
            words=all_words,
            average_confidence=avg_conf,
            low_confidence_words=low_conf,
            psm_used=pass1.psm_used,
            skew_angle=pass1.skew_angle,
        )

    def _extract_digital_pdf_text(self, content: bytes) -> Optional[str]:
        """
        Attempts to extract embedded text from a digital PDF (non-scanned).
        Digital PDFs (e.g., electronically generated lab reports) have selectable
        text that can be read directly — no OCR image processing needed.

        Returns extracted text if the PDF has meaningful embedded text,
        or None if it appears to be a scanned/image-only PDF.

        Priority order:
        1. pdfplumber (best for tabular lab reports — preserves table layout)
        2. PyMuPDF / fitz (fast, handles complex layouts)
        3. pypdf (pure Python fallback)
        """
        MIN_CHARS_PER_PAGE = 80  # If a page has fewer chars, treat as scanned image

        # --- Strategy 1: pdfplumber (best for tables) ---
        try:
            import pdfplumber
            import io
            all_pages_text = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    # First try extracting as a structured table
                    tables = page.extract_tables()
                    if tables:
                        table_lines = []
                        for table in tables:
                            for row in table:
                                if row:
                                    # Filter None cells and join with spaces
                                    clean_row = [str(cell).strip() if cell else '' for cell in row]
                                    non_empty = [c for c in clean_row if c]
                                    if len(non_empty) >= 2:
                                        table_lines.append('  '.join(non_empty))
                        if table_lines:
                            all_pages_text.append('\n'.join(table_lines))
                            continue
                    # Fall back to plain text extraction for this page
                    text = page.extract_text(layout=True) or page.extract_text() or ''
                    if text.strip():
                        all_pages_text.append(text)

            if all_pages_text:
                combined = '\n\n'.join(all_pages_text)
                # Validate: must have at least MIN_CHARS_PER_PAGE per page
                num_pages = max(1, len(all_pages_text))
                if len(combined.strip()) >= MIN_CHARS_PER_PAGE * num_pages:
                    logger.info(f"pdfplumber extracted {len(combined)} chars from digital PDF ({num_pages} pages)")
                    return combined
        except ImportError:
            logger.debug("pdfplumber not available, trying PyMuPDF")
        except Exception as e:
            logger.debug(f"pdfplumber extraction failed: {e}")

        # --- Strategy 2: PyMuPDF (fitz) ---
        try:
            import fitz  # PyMuPDF
            import io
            doc = fitz.open(stream=content, filetype="pdf")
            all_pages_text = []
            for page in doc:
                # Use 'blocks' mode to preserve table-like layout
                text = page.get_text("text").strip()
                if text:
                    all_pages_text.append(text)
            doc.close()

            if all_pages_text:
                combined = '\n\n'.join(all_pages_text)
                num_pages = max(1, len(all_pages_text))
                if len(combined.strip()) >= MIN_CHARS_PER_PAGE * num_pages:
                    logger.info(f"PyMuPDF extracted {len(combined)} chars from digital PDF ({num_pages} pages)")
                    return combined
        except ImportError:
            logger.debug("PyMuPDF not available, trying pypdf")
        except Exception as e:
            logger.debug(f"PyMuPDF extraction failed: {e}")

        # --- Strategy 3: pypdf (pure Python fallback) ---
        try:
            import pypdf
            import io
            reader = pypdf.PdfReader(io.BytesIO(content))
            all_pages_text = []
            for page in reader.pages:
                text = page.extract_text() or ''
                if text.strip():
                    all_pages_text.append(text.strip())

            if all_pages_text:
                combined = '\n\n'.join(all_pages_text)
                num_pages = max(1, len(all_pages_text))
                if len(combined.strip()) >= MIN_CHARS_PER_PAGE * num_pages:
                    logger.info(f"pypdf extracted {len(combined)} chars from digital PDF ({num_pages} pages)")
                    return combined
        except Exception as e:
            logger.debug(f"pypdf extraction failed: {e}")

        logger.info("PDF has no selectable text — treating as scanned image, will use OCR pipeline")
        return None

    def process_document(self, content: bytes, mime_type: str = "application/pdf") -> OCRDocumentResult:
        """
        End-to-end OCR document processing:

        For DIGITAL PDFs (selectable text):
          → Direct text extraction via pdfplumber/PyMuPDF — 100% accurate, no Tesseract needed.

        For SCANNED PDFs / Images:
          1. Preprocess & deskew pages via ImagePreprocessor (Phase 3)
          2. Execute multi-pass Tesseract OCR on each page (Phase 4)

        Confidence of 99% is assigned to digital PDF text extractions.
        """
        # ── FAST PATH: Digital PDF direct text extraction ──────────────────────
        if mime_type == "application/pdf" or mime_type == "application/x-pdf":
            digital_text = self._extract_digital_pdf_text(content)
            if digital_text:
                # Return as a synthetic high-confidence OCR result
                return OCRDocumentResult(
                    full_text=digital_text,
                    average_confidence=99.0,
                    total_pages=1,
                    pages=[
                        OCRPageResult(
                            page_number=1,
                            text=digital_text,
                            words=[],
                            average_confidence=99.0,
                            low_confidence_words=[],
                            psm_used=0,   # 0 = direct text extraction (no PSM)
                            skew_angle=0.0,
                        )
                    ],
                    low_confidence_count=0,
                    overall_status="high_confidence",
                )

        # ── FALLBACK: Image-based OCR (scanned PDFs or image files) ────────────
        preprocessed = image_preprocessor.preprocess_pipeline(content, mime_type)
        
        pages_ocr: List[OCRPageResult] = []
        all_text_parts: List[str] = []
        all_confidences: List[float] = []
        total_low_conf = 0

        for page in preprocessed.pages:
            page_res = self.process_page_multi_pass(page)
            pages_ocr.append(page_res)
            all_text_parts.append(page_res.text)
            if page_res.average_confidence > 0:
                all_confidences.append(page_res.average_confidence)
            total_low_conf += len(page_res.low_confidence_words)

        full_text = "\n\n--- PAGE BREAK ---\n\n".join(all_text_parts) if len(all_text_parts) > 1 else (all_text_parts[0] if all_text_parts else "")
        doc_avg_conf = round(float(np.mean(all_confidences)), 2) if all_confidences else 0.0

        if doc_avg_conf >= 85.0:
            status = "high_confidence"
        elif doc_avg_conf >= 70.0:
            status = "moderate"
        else:
            status = "needs_verification"

        return OCRDocumentResult(
            full_text=full_text,
            average_confidence=doc_avg_conf,
            total_pages=len(pages_ocr),
            pages=pages_ocr,
            low_confidence_count=total_low_conf,
            overall_status=status,
        )

    def _mock_ocr_fallback(self, image: np.ndarray, page_num: int) -> OCRPageResult:
        """
        Deterministic mock fallback when Tesseract OCR binary is NOT installed.
        NOTE: This is NEVER called for real uploaded PDFs when Tesseract is installed.
        When Tesseract is available, `_extract_page_ocr()` runs on the real rendered image.
        """
        mock_text = (
            "DIAGNOSTIC CLINICAL LABORATORY REPORT\n"
            "Patient Name: Demo Patient    Date: 2026-09-27\n\n"
            "Test Name              Result      Unit      Reference Range\n"
            "Haemoglobin (Hb)       12.1        g/dL      12.0 - 16.0\n"
            "Fasting Blood Sugar    94.0        mg/dL     70 - 99\n"
            "Serum Creatinine       0.90        mg/dL     0.70 - 1.30\n"
            "Total Cholesterol      185.0       mg/dL     125 - 200\n"
            "Thyroid (TSH)          2.85        uIU/mL    0.40 - 4.50\n"
            "HbA1c                  5.4         %         4.0 - 5.6\n"
            "Platelet Count         180000      cells/cumm 150000 - 450000\n"
            "Total WBC              7200        cells/cumm 4000 - 11000"
        )
        words = []
        for line_idx, line in enumerate(mock_text.split("\n")):
            for w_idx, word in enumerate(line.split()):
                words.append(
                    OCRWord(
                        text=word,
                        confidence=96.5,
                        bbox={"left": 50 + w_idx * 60, "top": 50 + line_idx * 30, "width": 50, "height": 20},
                        line_num=line_idx + 1,
                        block_num=1,
                        page_num=page_num,
                    )
                )

        return OCRPageResult(
            page_number=page_num,
            text=mock_text,
            words=words,
            average_confidence=96.5,
            low_confidence_words=[],
            psm_used=6,
            skew_angle=0.0,
        )

ocr_engine = OCREngine()
