"""
Module: core/forgery_rules.py
Owner: P4 (forgery/verdict/app/repo)

Purpose:
Rule-based heuristic checks for forwarded VTU notices to detect forgery,
invalid circular numbering, and anomalous dates.
"""
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Collection


# Regex pattern starting with VTU/
# TODO: adjust after checking 10 real circular numbers
VTU_CIRCULAR_PATTERN = re.compile(r"^VTU/[A-Z0-9_\-]+/[A-Z0-9_\-]+", re.IGNORECASE)


def _parse_year(date_str: str) -> Optional[int]:
    """Try parsing a year from a date string (e.g. YYYY-MM-DD or containing 4 digits)."""
    if not date_str or not isinstance(date_str, str):
        return None
    # Try ISO date first
    try:
        dt = datetime.fromisoformat(date_str.strip())
        return dt.year
    except ValueError:
        pass
    # Try finding 4 consecutive digits
    match = re.search(r"\b(19\d\d|20\d\d)\b", date_str)
    if match:
        return int(match.group(1))
    return None


def check_forgery(
    claim: Dict[str, Any], known_numbers: Optional[Collection[str]] = None
) -> List[Dict[str, str]]:
    """
    Check extracted claim for common indicators of forgery.

    Rules:
    - Circular number does not match the VTU pattern -> HARD flag.
    - Circular number matches but is not in known_numbers -> SOFT flag only.
    - new_date year before 2000 or more than 2 years in the future -> HARD flag.
    - Unreadable date -> no flag (do not guess).
    Only use HARD for clearly wrong things.

    Args:
        claim: Dict with keys event, exam, new_date, circular_no, issuer.
        known_numbers: Optional collection of known/indexed circular numbers.

    Returns:
        List of dicts: {"rule": str, "severity": "hard" | "soft", "detail": str}
    """
    flags: List[Dict[str, str]] = []
    circular_no = claim.get("circular_no")
    new_date = claim.get("new_date")

    # 1. Circular number pattern check
    if circular_no:
        circular_str = str(circular_no).strip()
        if not VTU_CIRCULAR_PATTERN.match(circular_str):
            flags.append(
                {
                    "rule": "invalid_circular_format",
                    "severity": "hard",
                    "detail": f"Circular number '{circular_str}' does not match official VTU format.",
                }
            )
        elif known_numbers is not None and circular_str not in known_numbers:
            flags.append(
                {
                    "rule": "unknown_circular_number",
                    "severity": "soft",
                    "detail": f"Circular number '{circular_str}' is not in known indexed circulars (may not be indexed yet).",
                }
            )

    # 2. Date anomaly check
    if new_date:
        year = _parse_year(str(new_date))
        if year is not None:
            current_year = datetime.now().year
            if year < 2000 or year > (current_year + 2):
                flags.append(
                    {
                        "rule": "suspicious_date",
                        "severity": "hard",
                        "detail": f"Claimed date '{new_date}' has year {year}, which is outside expected range (2000 - {current_year + 2}).",
                    }
                )
        # Unreadable date -> no flag (do not guess)

    return flags
