"""
Module: core/parser.py
Owner: P1 (parsing/OCR/metadata/chunking)

Purpose:
Extract text from official VTU circular PDFs using PyMuPDF and RapidOCR
for scanned/image-based notices.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Union

import pymupdf as fitz

logger = logging.getLogger(__name__)

MIN_DIGITAL_CHARS = 50
OCR_DPI = 300

_ocr_engine = None


def _get_ocr():
    """Lazily initialize and cache the RapidOCR engine."""
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR

        _ocr_engine = RapidOCR()
    return _ocr_engine


def _ocr_page(page: fitz.Page) -> str:
    """Render a PyMuPDF page at 300 DPI and extract text via RapidOCR."""
    scale = OCR_DPI / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
    img_bytes = pix.tobytes("png")
    ocr = _get_ocr()
    result, _ = ocr(img_bytes)
    if not result:
        return ""
    lines = [item[1].strip() for item in result if len(item) >= 2 and item[1]]
    return "\n".join(lines).strip()


def parse_pdf(pdf_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Extract text page-by-page from a PDF file.

    Uses PyMuPDF text extraction for digital pages and falls back to 300 DPI
    RapidOCR when a page has fewer than 50 extracted characters.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        List of page dicts:
        [{"file": str, "page": int, "text": str, "mode": "digital" | "scanned"}]
        Returns [] if the file is missing, unreadable, or corrupted.
    """
    path = Path(pdf_path)
    if not path.is_file():
        logger.warning("PDF file not found: %s", path)
        return []

    pages: List[Dict[str, Any]] = []
    try:
        doc = fitz.open(path)
    except Exception as exc:
        logger.warning("Failed to open PDF %s: %s", path, exc)
        return []

    try:
        for idx in range(len(doc)):
            page_num = idx + 1
            try:
                page = doc[idx]
                raw_text = (page.get_text("text") or "").strip()
                if len(raw_text) < MIN_DIGITAL_CHARS:
                    ocr_text = _ocr_page(page)
                    text = ocr_text if ocr_text else raw_text
                    mode = "scanned"
                else:
                    text = raw_text
                    mode = "digital"

                pages.append(
                    {
                        "file": path.name,
                        "page": page_num,
                        "text": text,
                        "mode": mode,
                    }
                )
            except Exception as exc:
                logger.warning("Failed to parse page %d of %s: %s", page_num, path.name, exc)
                pages.append(
                    {
                        "file": path.name,
                        "page": page_num,
                        "text": "",
                        "mode": "scanned",
                    }
                )
    finally:
        doc.close()

    return pages
