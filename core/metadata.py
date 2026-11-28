"""
Module: core/metadata.py
Owner: P1 (parsing/OCR/metadata/chunking)

Purpose:
Extract structured metadata from parsed circulars such as circular number,
issue date, subject, and referenced circular numbers.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple, Union

_MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

_CIRCULAR_RE = re.compile(
    r"(?:Ref\.?\s*(?:No\.?)?|No\.?)?\s*"
    r"(VTU\s*/\s*[A-Za-z0-9()._-]+(?:\s*/\s*[A-Za-z0-9()._-]+){1,8})",
    re.IGNORECASE,
)

_REFNO_FALLBACK_RE = re.compile(
    r"Ref\.?\s*No\.?\s*[:\-]?\s*"
    r"([A-Za-z0-9()._-]+(?:\s*/\s*[A-Za-z0-9()._-]+){2,8})",
    re.IGNORECASE,
)


def _normalize_circular_no(raw: str) -> Optional[str]:
    """Normalize OCR whitespace, missing slashes, and trailing punctuation in a VTU circular number."""
    val = re.sub(r"\s*/\s*", "/", raw).strip(" .,:;/")
    val = re.sub(r"/{2,}", "/", val)
    # Fix leading OCR case noise on VTU prefix
    val = re.sub(r"^vtu/", "VTU/", val, flags=re.IGNORECASE)
    # Restore missing slash between academic year and trailing digits (e.g., 2026-2027380 -> 2026-2027/380)
    val = re.sub(r"(20\d{2}-20\d{2})(\d{1,5})\b", r"\1/\2", val)
    val = re.sub(r"(20\d{2}-(?!20)\d{2})(\d{1,5})\b", r"\1/\2", val)
    # Reject bare dates or URLs
    if not val or "http" in val.lower() or re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", val):
        return None
    return val


def _parse_date_from_chunk(chunk: str) -> Optional[str]:
    """Parse a single date string into ISO YYYY-MM-DD, or return None."""
    # DD.MM.YYYY | DD-MM-YYYY | DD/MM/YYYY | DD-MM-YY
    m = re.search(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})\b", chunk)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if year < 100:
            year += 2000
        if 1 <= month <= 12 and 1 <= day <= 31 and 2020 <= year <= 2030:
            return f"{year:04d}-{month:02d}-{day:02d}"

    # DD Month YYYY (e.g., 18 AUG 2026, 18th August, 2026)
    m = re.search(
        r"\b(\d{1,2})(?:st|nd|rd|th)?[\s,]+([A-Za-z]{3,9})[\s,]+(20\d{2})\b",
        chunk,
        re.IGNORECASE,
    )
    if m:
        day = int(m.group(1))
        month = _MONTHS.get(m.group(2).lower())
        year = int(m.group(3))
        if month and 1 <= day <= 31 and 2020 <= year <= 2030:
            return f"{year:04d}-{month:02d}-{day:02d}"

    # Month DD, YYYY (e.g., AUG 18, 2026)
    m = re.search(
        r"\b([A-Za-z]{3,9})[\s,]+(\d{1,2})(?:st|nd|rd|th)?[\s,]+(20\d{2})\b",
        chunk,
        re.IGNORECASE,
    )
    if m:
        month = _MONTHS.get(m.group(1).lower())
        day = int(m.group(2))
        year = int(m.group(3))
        if month and 1 <= day <= 31 and 2020 <= year <= 2030:
            return f"{year:04d}-{month:02d}-{day:02d}"

    return None


def _extract_issue_date(page1_text: str) -> Optional[str]:
    """
    Prefer dates immediately following Date:/Dated:/Dt. labels on Page 1
    (including when the date wraps onto the next line in OCR output).
    Fall back to standalone header dates in the top 15 lines if no label exists.
    """
    labeled = re.findall(
        r"(?:Date|Dated|Dt\.?)\s*[:\-]?\s*([^\n]{0,40}(?:\n[^\n]{1,40})?)",
        page1_text,
        re.IGNORECASE,
    )
    for chunk in labeled:
        parsed = _parse_date_from_chunk(chunk)
        if parsed:
            return parsed

    # Fallback: scan standalone dates in the top 15 lines (before Sub:/Subject: if present)
    top_lines = "\n".join(page1_text.splitlines()[:15])
    sub_match = re.search(r"\bSub(?:ject)?\s*[:\-]", top_lines, re.IGNORECASE)
    header = top_lines[: sub_match.start()] if sub_match else top_lines
    return _parse_date_from_chunk(header)


def _extract_circular_no(page1_text: str) -> Optional[str]:
    """Extract the primary circular number from Page 1 header (excluding Ref: body lines)."""
    lines = page1_text.splitlines()
    header_lines = []
    for line in lines[:25]:
        if re.match(r"^\s*Ref(?:erence)?\s*[:\-]", line, re.IGNORECASE):
            continue
        header_lines.append(line)
    header_text = "\n".join(header_lines)

    # Unwrap line-broken VTU reference numbers (e.g., ".../2\n026-2027/1238" or ".../\n380")
    header_text = re.sub(
        r"(VTU[^\n]{0,80}?(?:/\d{0,3}|-))\s*\n\s*"
        r"(?!(?:Date|Dated|Dt|Sub|Subject|Ref|Reference|To|CIRCULAR|NOTIFICATION)\b)"
        r"([A-Za-z0-9()._-]+(?:/[A-Za-z0-9()._-]+)*)",
        lambda m: m.group(1) + m.group(2),
        header_text,
        flags=re.IGNORECASE,
    )

    for pattern in (_CIRCULAR_RE, _REFNO_FALLBACK_RE):
        m = pattern.search(header_text)
        if m:
            norm = _normalize_circular_no(m.group(1))
            if norm:
                return norm
    return None


def _extract_subject(page1_text: str) -> Optional[str]:
    """Extract the Sub: / Subject: line cleanly from Page 1."""
    m = re.search(
        r"(?:^|\n)\s*Sub(?:ject)?\s*[:\-]\s*(.+?)"
        r"(?=\n\s*(?:Ref(?:erence)?\s*[:\-]|With\s+reference|In\s+continuation|"
        r"Sir|Madam|1\.|CIRCULAR|NOTIFICATION)|\n\s*\n|$)",
        page1_text,
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return None
    subj = re.sub(r"\s+", " ", m.group(1)).strip(" :-")
    return subj if subj else None


def _extract_refs(page1_text: str, primary_circular: Optional[str]) -> List[str]:
    """Extract any referenced earlier circular numbers from Ref: lines."""
    refs: List[str] = []
    ref_blocks = re.findall(
        r"(?:^|\n)\s*Ref(?:erence)?\s*[:\-]\s*(.+?)(?=\n\s*\n|\n\s*[A-Z][a-z]+\s*:|$)",
        page1_text,
        re.IGNORECASE | re.DOTALL,
    )
    for block in ref_blocks:
        for m in _CIRCULAR_RE.finditer(block):
            norm = _normalize_circular_no(m.group(1))
            if norm and norm != primary_circular and norm not in refs:
                refs.append(norm)
    return refs


def extract_metadata(pages: Union[List[Dict[str, Any]], str]) -> Dict[str, Any]:
    """
    Parse VTU circular metadata from extracted document pages or raw text.

    Args:
        pages: List of page dicts from `parse_pdf`, or a raw Page 1 string.

    Returns:
        {
            "circular_no": str | None,
            "date": str | None,       # ISO YYYY-MM-DD
            "subject": str | None,
            "refs": list[str],
            "linked_to": str | None,
        }
    """
    if isinstance(pages, str):
        page1_text = pages
    elif pages:
        page1_text = pages[0].get("text", "") or ""
    else:
        page1_text = ""

    if not page1_text.strip():
        return {
            "circular_no": None,
            "date": None,
            "subject": None,
            "refs": [],
            "linked_to": None,
        }

    circular_no = _extract_circular_no(page1_text)
    date = _extract_issue_date(page1_text)
    subject = _extract_subject(page1_text)
    refs = _extract_refs(page1_text, circular_no)
    linked_to = refs[0] if refs else None

    return {
        "circular_no": circular_no,
        "date": date,
        "subject": subject,
        "refs": refs,
        "linked_to": linked_to,
    }
