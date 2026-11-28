"""Unit tests for P1 modules: core/parser.py, core/metadata.py, core/chunker.py."""
from pathlib import Path

import pymupdf as fitz

from core.chunker import chunk_document
from core.metadata import extract_metadata
from core.parser import parse_pdf


def test_parse_digital_pdf(tmp_path: Path):
    pdf_path = tmp_path / "digital_notice.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "VISVESVARAYA TECHNOLOGICAL UNIVERSITY, BELAGAVI\n"
        "Ref. No: VTU/BGM/Reg(E)/PS/2026-2027/1283\n"
        "Date: 04-11-2026\n"
        "Sub: Submission of Online Application Forms for Examination.",
    )
    doc.save(pdf_path)
    doc.close()

    pages = parse_pdf(pdf_path)
    assert len(pages) == 1
    assert pages[0]["file"] == "digital_notice.pdf"
    assert pages[0]["page"] == 1
    assert pages[0]["mode"] == "digital"
    assert "VTU/BGM/Reg(E)/PS/2026-2027/1283" in pages[0]["text"]


def test_parse_scanned_ocr_fallback_and_corrupted_graceful(tmp_path: Path, monkeypatch):
    # Blank/image-only page (< 50 chars) should trigger OCR fallback
    scanned_pdf = tmp_path / "scanned_notice.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(scanned_pdf)
    doc.close()

    called = {"count": 0}

    def fake_ocr_page(page):
        called["count"] += 1
        return "VTU/Exam/QPDS/CW(1)/2025-2026/1508\nDate: 10.01.2026\nSub: Time Table"

    monkeypatch.setattr("core.parser._ocr_page", fake_ocr_page)

    pages = parse_pdf(scanned_pdf)
    assert called["count"] == 1
    assert len(pages) == 1
    assert pages[0]["mode"] == "scanned"
    assert "1508" in pages[0]["text"]

    # Corrupted and missing files must return [] without crashing
    bad_pdf = tmp_path / "corrupted.pdf"
    bad_pdf.write_bytes(b"not-a-valid-pdf-stream")
    assert parse_pdf(bad_pdf) == []
    assert parse_pdf(tmp_path / "does_not_exist.pdf") == []


def test_metadata_prefers_labeled_date_and_normalizes_formats():
    sample_text = (
        "VISVESVARAYA TECHNOLOGICAL UNIVERSITY\n"
        "VTU / BGM / Reg(E) / PS / 2026-2027 / 781\n"
        "Dated: 18 AUG 2026\n"
        "Sub: Revised Examination Schedule for 7th Semester\n"
        "Ref: VTU/BGM/Reg(E)/PS/2026-2027/700 dated 01-08-2026\n"
        "Last date for fee submission without fine is 25-09-2026 and with fine is 30/09/2026.\n"
    )
    meta = extract_metadata(sample_text)
    assert meta["circular_no"] == "VTU/BGM/Reg(E)/PS/2026-2027/781"
    assert meta["date"] == "2026-08-18"
    assert meta["subject"] == "Revised Examination Schedule for 7th Semester"
    assert meta["refs"] == ["VTU/BGM/Reg(E)/PS/2026-2027/700"]
    assert meta["linked_to"] == "VTU/BGM/Reg(E)/PS/2026-2027/700"

    assert extract_metadata("Dated: 04-11-2026")["date"] == "2026-11-04"
    assert extract_metadata("Date: 22/08/2026")["date"] == "2026-08-22"
    assert extract_metadata("Dt: 10.08.2026")["date"] == "2026-08-10"


def test_metadata_returns_none_when_missing():
    meta = extract_metadata("General university notice with no header fields or dates.")
    assert meta["circular_no"] is None
    assert meta["date"] is None
    assert meta["subject"] is None
    assert meta["refs"] == []
    assert meta["linked_to"] is None


def test_chunker_preserves_table_rows_and_metadata():
    table_rows = [
        "Sl.No   Course Code   Date         Fee",
        "1       21CS71        10-12-2026   Rs. 1500",
        "2       21CS72        12-12-2026   Rs. 1500",
        "3       21CS73        14-12-2026   Rs. 1500",
        "4       21CS74        16-12-2026   Rs. 1500",
    ]
    pages = [
        {
            "file": "2026-11_timetable_01.pdf",
            "page": 1,
            "mode": "digital",
            "text": (
                "VTU/Exam/QPDS/CW(1)/2026-2027/13\n"
                "Date: 08-11-2026\n"
                "Sub: Examination Time Table\n\n"
                "1. All principals are requested to note the schedule below.\n\n"
                + "\n".join(table_rows)
            ),
        }
    ]

    # Small max_chars forces splitting, but each table row must stay intact on one line
    chunks = chunk_document(pages, max_chars=120)
    assert len(chunks) >= 2

    reconstructed_rows = "\n".join(c["text"] for c in chunks)
    for row in table_rows:
        assert row in reconstructed_rows

    for chunk in chunks:
        assert set(chunk.keys()) == {"text", "file", "page", "circular_no", "date", "subject"}
        assert chunk["file"] == "2026-11_timetable_01.pdf"
        assert chunk["page"] == 1
        assert chunk["circular_no"] == "VTU/Exam/QPDS/CW(1)/2026-2027/13"
        assert chunk["date"] == "2026-11-08"
        assert chunk["subject"] == "Examination Time Table"


def test_metadata_wrapped_circular_missing_slash_and_next_line_date():
    wrapped = (
        "VISVESVARAYA TECHNOLOGICAL UNIVERSITY\n"
        "VTU/BGM/Reg(E)/PS/letters/2\n"
        "026-2027/1238\n"
        "Date:\n"
        "29-10-2026\n"
        "Sub: On-Demand Examination\n"
    )
    meta1 = extract_metadata(wrapped)
    assert meta1["circular_no"] == "VTU/BGM/Reg(E)/PS/letters/2026-2027/1238"
    assert meta1["date"] == "2026-10-29"

    missing_slash = (
        "VTU/Exam/QPDS/CW(1)/2026-2027380\n"
        "18/06/2026\n"
        "Sub: Revised Time Table\n"
    )
    meta2 = extract_metadata(missing_slash)
    assert meta2["circular_no"] == "VTU/Exam/QPDS/CW(1)/2026-2027/380"
    assert meta2["date"] == "2026-06-18"


def test_chunker_groups_table_rows_into_compact_chunks():
    rows = [
        f"{i}   21CS{70 + i}   1{i}-12-2026   Rs. 1500"
        for i in range(1, 7)
    ]
    pages = [
        {
            "file": "2026-09_application_01.pdf",
            "page": 1,
            "mode": "digital",
            "text": "VTU/BGM/Reg(E)/PS/2026-2027/1\nDate: 04-09-2026\nSub: Exam\n\n" + "\n".join(rows),
        }
    ]
    chunks = chunk_document(pages, max_chars=1000)
    # All 6 rows + short header fit comfortably into 1 grouped chunk rather than 6+ fragments
    assert len(chunks) == 1
    for row in rows:
        assert row in chunks[0]["text"]

