"""Tests for the asset resolver."""
import pytest
from jevloop.assets import resolve


def test_btc_usd_resolves():
    spec = resolve("BTC/USD")
    assert spec["kind"] == "crypto"
    assert spec["shorting"] is False
    assert spec["market_hours_only"] is False


def test_equity_resolves():
    spec = resolve("AAPL")
    assert spec["kind"] == "equity"
    assert spec["market_hours_only"] is True
    assert spec["qty_precision"] == 0


def test_lowercase_normalised():
    spec = resolve("eth/usd")
    assert spec["symbol"] == "ETH/USD"


def test_unknown_crypto_raises():
    with pytest.raises(ValueError):
        resolve("FAKE/USD")
