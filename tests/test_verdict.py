"""
Tests for core/verdict.py
"""
import pytest
from core.verdict import decide


def test_verdict_contradicts():
    """result == 'contradicts' -> 'Contradicted'"""
    assert decide("contradicts", []) == "Contradicted"
    # Even if flags are present, contradictions are Contradicted
    assert decide("contradicts", [{"rule": "test", "severity": "hard"}]) == "Contradicted"


def test_verdict_supports_no_flags():
    """result == 'supports' and no hard flag -> 'Verified'"""
    assert decide("supports", []) == "Verified"


def test_verdict_supports_soft_flag():
    """result == 'supports' with soft flag -> 'Verified'"""
    flags = [{"rule": "unknown_circular_number", "severity": "soft", "detail": "not indexed"}]
    assert decide("supports", flags) == "Verified"


def test_verdict_supports_hard_flag():
    """result == 'supports' with hard flag -> 'Unverified'"""
    flags = [{"rule": "suspicious_date", "severity": "hard", "detail": "bad year"}]
    assert decide("supports", flags) == "Unverified"


def test_verdict_not_found():
    """everything else (including 'not_found') -> 'Unverified'. NOT FOUND MUST NEVER BE CALLED FAKE."""
    assert decide("not_found", []) == "Unverified"
    assert decide("not_found", [{"rule": "suspicious_date", "severity": "hard"}]) == "Unverified"
