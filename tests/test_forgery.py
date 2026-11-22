"""
Tests for core/forgery_rules.py
"""
import pytest
from core.forgery_rules import check_forgery


def test_bad_circular_number_gives_hard_flag():
    """Circular number not matching VTU pattern gives a hard flag."""
    claim = {
        "event": "exam",
        "exam": "3rd sem",
        "new_date": "2026-12-12",
        "circular_no": "FAKE-NOTICE-999",
        "issuer": "VTU",
    }
    flags = check_forgery(claim)
    assert len(flags) > 0
    hard_flags = [f for f in flags if f.get("severity") == "hard"]
    assert len(hard_flags) >= 1
    assert any(f["rule"] == "invalid_circular_format" for f in hard_flags)


def test_empty_claim_gives_no_flags():
    """Empty claim or claim with missing optional fields gives no flags."""
    claim = {
        "event": None,
        "exam": None,
        "new_date": None,
        "circular_no": None,
        "issuer": None,
    }
    flags = check_forgery(claim)
    assert flags == []

    # Completely empty dict
    assert check_forgery({}) == []
