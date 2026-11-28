"""
Module: core/chunker.py
Owner: P1 (parsing/OCR/metadata/chunking)

Purpose:
Split parsed circular text into semantic, clause-aware chunks preserving
document metadata (file, page, circular_no, date, subject) and keeping
tables, schedules, and date-fee rows intact.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from core.metadata import extract_metadata

_TABLE_LINE_RE = re.compile(
    r"(\|)|"  # Pipe-delimited table
    r"(\t)|"  # Tab-delimited columns
    r"(\S\s{3,}\S)|"  # Multi-space column alignment (3+ spaces)
    r"(^\s*(?:Sl\.?\s*No\.?|S\.?\s*No\.?|Date\s+Day|Course\s+Code|Particulars)\b)|"
    r"(^\s*\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\s+.+)|"  # Date-schedule row
    r"(^\s*\d{1,3}\s+[A-Z0-9]{4,10}\s+.+)",  # Sl.No + Course code row
    re.IGNORECASE,
)


def _is_table_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return bool(_TABLE_LINE_RE.search(stripped))


def _segment_blocks(text: str) -> List[Dict[str, Any]]:
    """
    Group page text into alternating 'table' and 'prose' blocks.
    Table blocks preserve individual rows intact.
    """
    lines = text.splitlines()
    blocks: List[Dict[str, Any]] = []
    cur_type: Optional[str] = None
    cur_lines: List[str] = []

    def flush():
        nonlocal cur_type, cur_lines
        if cur_lines:
            blocks.append({"type": cur_type, "lines": cur_lines})
            cur_lines = []
            cur_type = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue

        line_type = "table" if _is_table_line(line) else "prose"
        if cur_type is None:
            cur_type = line_type
            cur_lines = [stripped]
        elif cur_type == line_type:
            cur_lines.append(stripped)
        else:
            flush()
            cur_type = line_type
            cur_lines = [stripped]

    flush()
    return blocks


def _split_prose_block(lines: List[str], max_chars: int) -> List[str]:
    """Split prose lines by numbered clauses or size without breaking mid-line."""
    # Join lines into clauses where numbered items start a new clause
    clauses: List[str] = []
    buf: List[str] = []
    for line in lines:
        if re.match(r"^(?:\d+\.|[a-z]\)|•|-)\s+", line) and buf:
            clauses.append(" ".join(buf))
            buf = [line]
        else:
            buf.append(line)
    if buf:
        clauses.append(" ".join(buf))

    chunks: List[str] = []
    cur = ""
    for clause in clauses:
        if len(clause) > max_chars:
            if cur:
                chunks.append(cur)
                cur = ""
            # Split oversized prose clause at sentence boundaries
            sentences = re.split(r"(?<=[.!?])\s+", clause)
            sent_buf = ""
            for sent in sentences:
                if len(sent_buf) + len(sent) + 1 <= max_chars:
                    sent_buf = f"{sent_buf} {sent}".strip()
                else:
                    if sent_buf:
                        chunks.append(sent_buf)
                    sent_buf = sent
            if sent_buf:
                chunks.append(sent_buf)
        elif len(cur) + len(clause) + 1 <= max_chars:
            cur = f"{cur}\n{clause}".strip()
        else:
            if cur:
                chunks.append(cur)
            cur = clause
    if cur:
        chunks.append(cur)
    return chunks


def _split_table_block(lines: List[str], max_chars: int) -> List[str]:
    """
    Keep table/schedule/date-fee rows intact.
    Never splits a single row across two chunks.
    """
    chunks: List[str] = []
    cur_rows: List[str] = []
    cur_len = 0

    for row in lines:
        row_len = len(row) + (1 if cur_rows else 0)
        if cur_rows and cur_len + row_len > max_chars:
            chunks.append("\n".join(cur_rows))
            cur_rows = [row]
            cur_len = len(row)
        else:
            cur_rows.append(row)
            cur_len += row_len

    if cur_rows:
        chunks.append("\n".join(cur_rows))
    return chunks


def chunk_document(
    pages: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
    file_name: Optional[str] = None,
    max_chars: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Split parsed pages into clause/table-preserving chunks with full metadata.

    Args:
        pages: List of page dicts from `parse_pdf`.
        metadata: Optional metadata dict from `extract_metadata`. Computed if omitted.
        file_name: Optional override for the `file` metadata key.
        max_chars: Target maximum characters per chunk (table rows are never split).

    Returns:
        List of chunk dicts:
        [{"text", "file", "page", "circular_no", "date", "subject"}]
    """
    if not pages:
        return []

    meta = metadata if metadata is not None else extract_metadata(pages)
    all_chunks: List[Dict[str, Any]] = []

    for page_dict in pages:
        text = (page_dict.get("text") or "").strip()
        if not text:
            continue

        resolved_file = file_name or page_dict.get("file")
        page_num = page_dict.get("page", 1)
        blocks = _segment_blocks(text)

        page_texts: List[str] = []
        for blk in blocks:
            if blk["type"] == "table":
                page_texts.extend(_split_table_block(blk["lines"], max_chars))
            else:
                page_texts.extend(_split_prose_block(blk["lines"], max_chars))

        # Pack consecutive small fragments on the same page up to max_chars
        # without ever splitting a table row.
        packed_texts: List[str] = []
        for frag in page_texts:
            frag = frag.strip()
            if not frag:
                continue
            if packed_texts and len(packed_texts[-1]) + len(frag) + 1 <= max_chars:
                packed_texts[-1] = f"{packed_texts[-1]}\n{frag}"
            else:
                packed_texts.append(frag)

        for chunk_text in packed_texts:
            all_chunks.append(
                {
                    "text": chunk_text,
                    "file": resolved_file,
                    "page": page_num,
                    "circular_no": meta.get("circular_no"),
                    "date": meta.get("date"),
                    "subject": meta.get("subject"),
                }
            )

    return all_chunks
