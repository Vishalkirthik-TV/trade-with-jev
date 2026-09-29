"""Tests for the split guard (arithmetic detection)."""
import pytest
from jevloop.split import is_arithmetic, validate_question, BATTERY_KEYS


def test_arithmetic_detected():
    assert is_arithmetic("what is the mid-price?")
    assert is_arithmetic("calculate the spread in bps")
    assert is_arithmetic("how much does BTCUSD cost?")


def test_non_arithmetic_passes():
    assert not is_arithmetic("Is the market trending or mean-reverting?")
    assert not is_arithmetic("Is flow toxic or noise?")


def test_unknown_key_rejected():
    with pytest.raises(ValueError, match="Unknown battery key"):
        validate_question("unknown_key", "Is the market trending?")


def test_arithmetic_question_rejected():
    with pytest.raises(ValueError, match="arithmetic"):
        validate_question("regime", "What is the mid-price?")


def test_valid_question_passes():
    for key in BATTERY_KEYS:
        validate_question(key, "Is conditions favourable or stressed?")
