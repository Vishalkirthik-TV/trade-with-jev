"""
calibrate.py — Brier score + 10-bin reliability table from ~/.jev-loop/log.jsonl.

Scores Jev's confidence in each up/down direction call against whether
price actually moved that way over the next tick.
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict


LOG_PATH = Path.home() / ".jev-loop" / "log.jsonl"


def calibrate():
    if not LOG_PATH.exists():
        print(f"No log found at {LOG_PATH}. Run the loop first.")
        return

    ticks = []
    with open(LOG_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    ticks.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    if len(ticks) < 2:
        print(f"Need at least 2 ticks to calibrate (have {len(ticks)}).")
        return

    # Pair each tick with the next to get actual outcome
    scored = []
    for i in range(len(ticks) - 1):
        t = ticks[i]
        t_next = ticks[i + 1]
        direction = t.get("battery", {}).get("direction")
        confidence = t.get("battery", {}).get("confidence")
        mid_now = t.get("state", {}).get("mid")
        mid_next = t_next.get("state", {}).get("mid")
        if None in (direction, confidence, mid_now, mid_next):
            continue
        if direction == "up":
            forecast_prob = confidence
            outcome = 1 if mid_next > mid_now else 0
        elif direction == "down":
            forecast_prob = confidence
            outcome = 1 if mid_next < mid_now else 0
        else:
            continue  # skip neutral
        scored.append((forecast_prob, outcome))

    if not scored:
        print("No direction forecasts with outcomes found in log.")
        return

    # Brier score
    brier = sum((p - o) ** 2 for p, o in scored) / len(scored)

    # 10-bin reliability table
    bins = defaultdict(lambda: {"count": 0, "hits": 0, "prob_sum": 0.0})
    for p, o in scored:
        b = int(p * 10)  # 0..10
        b = min(b, 9)
        bins[b]["count"] += 1
        bins[b]["hits"] += o
        bins[b]["prob_sum"] += p

    print(f"\nCalibration report — {len(scored)} direction forecasts")
    print(f"Brier score: {brier:.4f}  (lower is better; 0.25 = random, 0.0 = perfect)\n")
    print(f"{'Bin':>6} {'Forecast%':>10} {'Actual%':>10} {'Count':>7}")
    print("-" * 38)
    for b in range(10):
        if b not in bins:
            continue
        d = bins[b]
        avg_forecast = d["prob_sum"] / d["count"] * 100
        avg_actual = d["hits"] / d["count"] * 100
        print(f"{b*10:>5}% {avg_forecast:>9.1f}% {avg_actual:>9.1f}% {d['count']:>7}")

    # Optionally save reliability.png
    try:
        import matplotlib.pyplot as plt
        xs = []
        ys = []
        for b in range(10):
            if b in bins:
                d = bins[b]
                xs.append(d["prob_sum"] / d["count"])
                ys.append(d["hits"] / d["count"])
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
        ax.scatter(xs, ys, s=60, zorder=5)
        ax.set_xlabel("Forecast probability")
        ax.set_ylabel("Observed frequency")
        ax.set_title(f"Jev reliability diagram  (Brier={brier:.4f})")
        ax.legend()
        out = Path.home() / ".jev-loop" / "reliability.png"
        fig.savefig(out, dpi=120)
        print(f"\nReliability diagram saved to {out}")
    except ImportError:
        pass
