"""
control.py — RUNNING / PAUSED state and per-install token.

State lives in ~/.jev-loop/control.json.
Token lives in ~/.jev-loop/control.token.
The loop checks is_running() before every order.
"""
from __future__ import annotations
import json
import os
import secrets
from pathlib import Path

_DIR = Path.home() / ".jev-loop"
_CONTROL = _DIR / "control.json"
_TOKEN = _DIR / "control.token"


def _ensure_dir():
    _DIR.mkdir(parents=True, exist_ok=True)


def get_token() -> str:
    _ensure_dir()
    if _TOKEN.exists():
        return _TOKEN.read_text().strip()
    tok = secrets.token_hex(32)
    _TOKEN.write_text(tok)
    return tok


def is_running() -> bool:
    if not _CONTROL.exists():
        return True  # default: running
    try:
        data = json.loads(_CONTROL.read_text())
        return data.get("state", "RUNNING") == "RUNNING"
    except Exception:
        return True


def pause():
    _ensure_dir()
    _CONTROL.write_text(json.dumps({"state": "PAUSED"}))


def resume():
    _ensure_dir()
    _CONTROL.write_text(json.dumps({"state": "RUNNING"}))


def get_state() -> str:
    return "RUNNING" if is_running() else "PAUSED"
