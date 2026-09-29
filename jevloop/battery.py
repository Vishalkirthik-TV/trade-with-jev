"""
battery.py — the seven-question Jev judgment battery.

One call to Jev, seven typed answers. Never arithmetic, never "what should I do."
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional

from jevloop.split import BATTERY_KEYS, validate_question


@dataclass
class BatteryResult:
    regime: str = "unknown"             # trending | mean_reverting | chaotic
    direction: str = "neutral"          # up | down | neutral
    toxic_flow: float = 0.5             # 0–1 probability flow is toxic
    liquidity_stress: float = 0.5       # 0–1 how stressed liquidity is
    quote_environment: float = 0.5      # 0–1 quality of quote environment
    inventory_pressure: float = 0.5     # 0–1 how much inventory pressure exists
    execution_health: float = 0.5       # 0–1 execution health (1 = optimal)
    confidence: float = 0.5            # overall confidence in the battery
    latency_ms: float = 0.0
    model: str = "unknown"
    mock: bool = False
    ts: float = field(default_factory=time.time)

    def age_s(self) -> float:
        return time.time() - self.ts

    def is_stale(self, max_age_s: float) -> bool:
        return self.age_s() > max_age_s


BATTERY_PROMPT_TEMPLATE = """\
Market state snapshot (deterministic, computed by code):
{state_summary}

Answer exactly seven questions. For each, give a label and a confidence
score 0.0–1.0. Never calculate; all arithmetic was done before this call.

1. regime: is the market trending, mean_reverting, or chaotic? (confidence)
2. direction: is price likely up, down, or neutral over the next few minutes? (confidence)
3. toxic_flow: probability 0–1 that the flow just seen is toxic (informed, not noise)
4. liquidity_stress: probability 0–1 that liquidity is currently stressed
5. quote_environment: score 0–1 for quality of the quoting environment (1=optimal)
6. inventory_pressure: probability 0–1 that current inventory is under pressure to unwind
7. execution_health: score 0–1 for execution health (1=optimal, 0=degraded)

Respond in JSON only:
{{"regime":"<trending|mean_reverting|chaotic>","regime_conf":<0-1>,
  "direction":"<up|down|neutral>","direction_conf":<0-1>,
  "toxic_flow":<0-1>,"liquidity_stress":<0-1>,"quote_environment":<0-1>,
  "inventory_pressure":<0-1>,"execution_health":<0-1>,"overall_confidence":<0-1>}}
"""


def build_prompt(state: dict) -> str:
    lines = []
    for k, v in state.items():
        if v is not None:
            lines.append(f"  {k}: {v}")
    return BATTERY_PROMPT_TEMPLATE.format(state_summary="\n".join(lines))


def parse_response(raw: dict, latency_ms: float, model: str, mock: bool) -> BatteryResult:
    return BatteryResult(
        regime=raw.get("regime", "chaotic"),
        direction=raw.get("direction", "neutral"),
        toxic_flow=float(raw.get("toxic_flow", 0.5)),
        liquidity_stress=float(raw.get("liquidity_stress", 0.5)),
        quote_environment=float(raw.get("quote_environment", 0.5)),
        inventory_pressure=float(raw.get("inventory_pressure", 0.5)),
        execution_health=float(raw.get("execution_health", 0.5)),
        confidence=float(raw.get("overall_confidence", 0.5)),
        latency_ms=latency_ms,
        model=model,
        mock=mock,
    )
