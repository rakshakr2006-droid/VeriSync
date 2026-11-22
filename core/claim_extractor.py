"""
Module: core/claim_extractor.py
Owner: P3 (LLM/claims/verifier)

Purpose:
Extract key claims from forwarded social media / WhatsApp VTU messages.
"""
from typing import Dict, Any, Optional


def extract_claim(message: str) -> Dict[str, Optional[str]]:
    """
    STUB, owner replaces this.

    Extract structured claims from forwarded message text.

    Args:
        message: Forwarded notice text.

    Returns:
        dict: {"event", "exam", "new_date", "circular_no", "issuer"}
              (values are None if missing)
    """
    return {
        "event": "postponement",
        "exam": "3rd sem",
        "new_date": "2026-12-12",
        "circular_no": None,
        "issuer": "VTU",
    }
