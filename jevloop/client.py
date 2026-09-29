"""
client.py — resolve the Jev decision client and manage the call throttle.

Priority:
  1. TYPESAFE_API_KEY  → direct TypeSafe (faster, higher rate limit)
  2. AI_GATEWAY_API_KEY → Vercel AI Gateway (normal route, no waitlist)
  3. neither           → clearly-labelled mock (random answers, no orders)

One shared client, one call at a time (JevThrottle).
Rate-limit backoff: 5s, 10s, 20s, up to 120s.
"""
from __future__ import annotations
import json
import os
import random
import threading
import time
from typing import Optional

import requests

from jevloop.battery import BatteryResult, parse_response

TYPESAFE_API_URL = "https://api.typesafe.ai/v1/systemone"
AI_GATEWAY_API_URL = "https://ai-gateway.vercel.sh/typesafe/v1/systemone"
JEV_MODEL_DIRECT = "jev-latest"
JEV_MODEL_GATEWAY = "typesafe-ai/jev"

_BACKOFF_SEQUENCE = [5, 10, 20, 40, 80, 120]


class MockJevClient:
    """Random-answer client used when no real key is present. Never places orders."""

    name = "mock"
    mock = True

    def ask(self, state: dict) -> BatteryResult:
        time.sleep(0.05)
        raw = {
            "regime": random.choice(["trending", "mean_reverting", "chaotic"]),
            "direction": random.choice(["up", "down", "neutral"]),
            "toxic_flow": random.random(),
            "liquidity_stress": random.random(),
            "quote_environment": random.random(),
            "inventory_pressure": random.random(),
            "execution_health": random.random(),
            "overall_confidence": random.uniform(0.4, 0.9),
        }
        return parse_response(raw, latency_ms=50.0, model="mock", mock=True)


class RealJevClient:
    """HTTP client for TypeSafe direct or Vercel AI Gateway using /v1/systemone."""

    def __init__(self, api_key: str, url: str, model: str, name: str):
        self.api_key = api_key
        self.url = url
        self.model = model
        self.name = name
        self.mock = False
        self._backoff_idx = 0
        self._backoff_until = 0.0

    def ask(self, state: dict) -> BatteryResult:
        now = time.time()
        if now < self._backoff_until:
            wait = self._backoff_until - now
            time.sleep(wait)

        state_summary = self._build_state_summary(state)
        questions = self._build_questions()

        t0 = time.time()
        try:
            resp = requests.post(
                self.url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "state": state_summary,
                    "questions": questions,
                },
                timeout=10,
            )
            latency_ms = (time.time() - t0) * 1000

            if resp.status_code == 429 or "frequency" in resp.text.lower():
                self._apply_backoff()
                raise RuntimeError(f"Jev rate-limited (429). Backing off {self._current_backoff()}s.")

            resp.raise_for_status()
            self._backoff_idx = 0

            data = resp.json()
            return self._parse_typesafe_response(data, latency_ms)

        except requests.exceptions.Timeout:
            self._apply_backoff()
            raise RuntimeError(f"Jev request timed out. Backing off.")

    def _build_state_summary(self, state: dict) -> str:
        lines = []
        for k, v in state.items():
            if v is not None:
                lines.append(f"  {k}: {v}")
        return "Market state snapshot (deterministic, computed by code):\n" + "\n".join(lines)

    def _build_questions(self) -> dict:
        return {
            "regime": {
                "type": "choice",
                "instructions": "Is the market trending, mean_reverting, or chaotic?",
                "criteria": {
                    "trending": "Clear directional trend with momentum",
                    "mean_reverting": "Price oscillating around a mean, likely to revert",
                    "chaotic": "No clear pattern, high noise, unpredictable",
                },
            },
            "direction": {
                "type": "choice",
                "instructions": "Is price likely up, down, or neutral over the next few minutes?",
                "criteria": {
                    "up": "Price likely to increase",
                    "down": "Price likely to decrease",
                    "neutral": "No clear directional bias",
                },
            },
            "toxic_flow": {
                "type": "noul",
                "instructions": "Is the flow just seen toxic (informed, not noise)?",
            },
            "liquidity_stress": {
                "type": "noul",
                "instructions": "Is liquidity currently stressed?",
            },
            "quote_environment": {
                "type": "score",
                "instructions": "Rate the quality of the quoting environment (1=degraded, 10=optimal)",
                "scale_min": 1,
                "scale_max": 10,
                "criteria": ["Degraded", "Optimal"],
            },
            "inventory_pressure": {
                "type": "noul",
                "instructions": "Is current inventory under pressure to unwind?",
            },
            "execution_health": {
                "type": "score",
                "instructions": "Rate execution health (1=degraded, 10=optimal)",
                "scale_min": 1,
                "scale_max": 10,
                "criteria": ["Degraded", "Optimal"],
            },
        }

    def _parse_typesafe_response(self, data: dict, latency_ms: float) -> BatteryResult:
        answers = data.get("answers", {})
        model = data.get("model", self.model)

        regime_ans = answers.get("regime", {})
        direction_ans = answers.get("direction", {})
        toxic_flow_ans = answers.get("toxic_flow", {})
        liquidity_stress_ans = answers.get("liquidity_stress", {})
        quote_env_ans = answers.get("quote_environment", {})
        inventory_pressure_ans = answers.get("inventory_pressure", {})
        execution_health_ans = answers.get("execution_health", {})

        raw = {
            "regime": regime_ans.get("choice", "chaotic"),
            "direction": direction_ans.get("choice", "neutral"),
            "toxic_flow": toxic_flow_ans.get("noul", 0.5),
            "liquidity_stress": liquidity_stress_ans.get("noul", 0.5),
            "quote_environment": quote_env_ans.get("score", 0.5),
            "inventory_pressure": inventory_pressure_ans.get("noul", 0.5),
            "execution_health": execution_health_ans.get("score", 0.5),
            "overall_confidence": self._compute_overall_confidence(answers),
        }
        return parse_response(raw, latency_ms=latency_ms, model=model, mock=False)

    def _compute_overall_confidence(self, answers: dict) -> float:
        confidences = []
        for key, ans in answers.items():
            if "confidence" in ans:
                confidences.append(ans["confidence"])
            elif "choice" in ans and "probabilities" in ans:
                probs = ans["probabilities"]
                if probs:
                    confidences.append(max(probs.values()))
            elif "noul" in ans:
                confidences.append(max(ans["noul"], 1 - ans["noul"]))
            elif "score" in ans:
                score = ans["score"]
                confidences.append(1 - abs(score - 5.5) / 4.5)
        return sum(confidences) / len(confidences) if confidences else 0.5

    def _current_backoff(self) -> int:
        return _BACKOFF_SEQUENCE[min(self._backoff_idx, len(_BACKOFF_SEQUENCE) - 1)]

    def _apply_backoff(self):
        delay = self._current_backoff()
        self._backoff_until = time.time() + delay
        self._backoff_idx = min(self._backoff_idx + 1, len(_BACKOFF_SEQUENCE) - 1)


class JevThrottle:
    """
    One shared client, one call at a time.

    - Calls Jev at most once every JEV_MIN_INTERVAL_S (default 4s).
    - Calls sooner on a material move (price or spread moved JEV_MATERIAL_MOVE_BPS bps
      or position flipped), but never sooner than JEV_MIN_GAP_S (default 3s).
    - Reuses the last judgment otherwise.
    - Judgment older than JEV_MAX_JUDGMENT_AGE_S is treated as stale.
    """

    def __init__(self, client, min_interval_s: float = 4.0, min_gap_s: float = 3.0,
                 material_move_bps: float = 15.0, max_age_s: float = 60.0):
        self.client = client
        self.min_interval_s = min_interval_s
        self.min_gap_s = min_gap_s
        self.material_move_bps = material_move_bps
        self.max_age_s = max_age_s
        self._lock = threading.Lock()
        self._last_result: Optional[BatteryResult] = None
        self._last_call_ts: float = 0.0
        self._last_mid: Optional[float] = None
        self._last_position: Optional[float] = None

    def ask(self, state: dict, force: bool = False) -> BatteryResult:
        with self._lock:
            now = time.time()
            mid = state.get("mid")
            position = state.get("position_qty", 0.0)

            material = False
            if self._last_mid and mid:
                move_bps = abs(mid - self._last_mid) / self._last_mid * 10000
                if move_bps >= self.material_move_bps:
                    material = True
            if self._last_position is not None and position != self._last_position:
                material = True

            elapsed = now - self._last_call_ts
            stale = self._last_result is None or self._last_result.is_stale(self.max_age_s)

            should_call = (
                force
                or stale
                or elapsed >= self.min_interval_s
                or (material and elapsed >= self.min_gap_s)
            )

            if not should_call and self._last_result is not None:
                return self._last_result

            result = self.client.ask(state)
            self._last_result = result
            self._last_call_ts = now
            self._last_mid = mid
            self._last_position = position
            return result


def resolve_client(force_mock: bool = False) -> tuple:
    """Return (client, throttle). Prints which client won."""
    min_interval = float(os.environ.get("JEV_MIN_INTERVAL_S", "4"))
    min_gap = float(os.environ.get("JEV_MIN_GAP_S", "3"))
    material_bps = float(os.environ.get("JEV_MATERIAL_MOVE_BPS", "15"))
    max_age = float(os.environ.get("JEV_MAX_JUDGMENT_AGE_S", "60"))

    if force_mock:
        client = MockJevClient()
        print("[!] Jev client: MOCK (forced). Answers are random. No orders will be placed.")
    elif key := os.environ.get("TYPESAFE_API_KEY"):
        client = RealJevClient(key, TYPESAFE_API_URL, JEV_MODEL_DIRECT, "typesafe-direct")
        print("[+] Jev client: TypeSafe direct (faster, higher rate limit)")
    elif key := os.environ.get("AI_GATEWAY_API_KEY"):
        client = RealJevClient(key, AI_GATEWAY_API_URL, JEV_MODEL_GATEWAY, "ai-gateway")
        print("[+] Jev client: Vercel AI Gateway")
    else:
        client = MockJevClient()
        print("[!] Jev client: MOCK (no API key found). Answers are random. No orders will be placed.")

    throttle = JevThrottle(client, min_interval_s=min_interval, min_gap_s=min_gap,
                           material_move_bps=material_bps, max_age_s=max_age)
    return client, throttle