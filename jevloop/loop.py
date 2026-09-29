"""
loop.py — the nine-stage trading loop.

Stages each tick:
  1. block on price event (or bar close)
  2. read the book
  3. state snapshot (deterministic)
  4. battery (seven Jev judgments, throttled)
  5. policy engine (compose_action → strategy hook)
  6. pricing (Avellaneda-Stoikov)
  7. risk veto (nine hard limits)
  8. execute (post-only quotes + directional leg)
  9. log + fills + inventory update

One JSON line per tick to ~/.jev-loop/log.jsonl.
Latest state to ~/.jev-loop/latest.json (the dashboard reads this).
"""
from __future__ import annotations
import json
import os
import signal
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from jevloop.assets import resolve as resolve_symbol
from jevloop.client import resolve_client
from jevloop.control import is_running
from jevloop.execution.alpaca import AlpacaClient
from jevloop.ladder import evaluate as ladder_eval
from jevloop.limits import NOTIONAL_USD, MAX_INVENTORY_FRACTION
from jevloop.policy import compose_action
from jevloop.pricing import avellaneda_stoikov, quote_prices
from jevloop.risk import check_order, RiskVeto
from jevloop.state import build_state

LOG_DIR = Path.home() / ".jev-loop"
LOG_PATH = LOG_DIR / "log.jsonl"
LATEST_PATH = LOG_DIR / "latest.json"

BAR_INTERVALS = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600}


def _next_bar_close(interval_s: int) -> float:
    """Return seconds until the next UTC-aligned bar close."""
    now = time.time()
    return interval_s - (now % interval_s)


def run(args):
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    symbol_str = args.symbol or os.environ.get("DEFAULT_SYMBOL", "BTC/USD")
    spec = resolve_symbol(symbol_str)
    symbol = spec["symbol"]
    kind = spec["kind"]

    # Live trading three-gate check
    live = getattr(args, "live", False)
    if live:
        allow = os.environ.get("JEV_LOOP_ALLOW_LIVE", "")
        if allow != "i-understand-the-risk":
            print("ERROR: Live trading refused. Set JEV_LOOP_ALLOW_LIVE=i-understand-the-risk.")
            sys.exit(1)
        phrase = "I understand this is real money and I accept the risk"
        typed = input(f'Type exactly: "{phrase}"\n> ')
        if typed.strip() != phrase:
            print("Confirmation phrase did not match. Exiting.")
            sys.exit(1)

    force_mock = getattr(args, "mock", False)
    dry_execution = getattr(args, "dry_execution", False)
    forever = getattr(args, "forever", False) or args.ticks == 0
    max_ticks = None if forever else args.ticks

    api_key = os.environ.get("ALPACA_API_KEY", "")
    secret_key = os.environ.get("ALPACA_SECRET_KEY", "")
    if not api_key or not secret_key:
        print("ERROR: ALPACA_API_KEY and ALPACA_SECRET_KEY are required in .env")
        sys.exit(1)

    alpaca = AlpacaClient(api_key, secret_key, live=live)
    client, throttle = resolve_client(force_mock=force_mock)

    bar_interval_s = None
    if args.bar:
        bar_interval_s = BAR_INTERVALS.get(args.bar)
        if not bar_interval_s:
            print(f"Unknown bar interval '{args.bar}'. Use: 1m 5m 15m 30m 1h")
            sys.exit(1)

    print(f"{'LIVE' if live else 'PAPER'} | {symbol} | mock={client.mock} | "
          f"dry={dry_execution} | {'forever' if forever else f'{max_ticks} ticks'}"
          + (f" | bar={args.bar}" if bar_interval_s else ""))

    if client.mock or dry_execution:
        print("⚠  No orders will be placed (mock or dry-execution mode).")

    # Get session-start equity
    try:
        account = alpaca.get_account()
        session_start_equity = account["equity"]
    except Exception as e:
        print(f"ERROR: Could not fetch account: {e}")
        sys.exit(1)

    session_trades = []
    tick_count = 0
    last_battery = None
    shutdown = False

    def _shutdown(sig, frame):
        nonlocal shutdown
        shutdown = True
        print("\nShutting down — cancelling own resting orders...")
        cancelled = alpaca.cancel_our_orders(symbol)
        print(f"Cancelled {cancelled} order(s).")
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while not shutdown:
        if max_ticks is not None and tick_count >= max_ticks:
            break

        tick_start = time.time()

        # Bar-mode: sleep until next close
        if bar_interval_s:
            wait = _next_bar_close(bar_interval_s)
            if wait > 2:
                time.sleep(min(wait, 2))
                continue

        # 2. Read the book
        try:
            quote = alpaca.get_quote(symbol, kind)
            bars = alpaca.get_bars_1m(symbol, kind, limit=30)
            account = alpaca.get_account()
            pos = alpaca.get_position(symbol)
        except Exception as e:
            print(f"  [tick {tick_count}] data error: {e}")
            time.sleep(2)
            continue

        bid, ask = quote["bid"], quote["ask"]
        if bid <= 0 or ask <= 0 or ask <= bid:
            time.sleep(1)
            continue

        # 3. State snapshot
        state = build_state(
            bid=bid, ask=ask,
            last_trade=quote["last_trade"],
            bid_size=quote["bid_size"], ask_size=quote["ask_size"],
            position_qty=pos["qty"], position_avg_px=pos["avg_px"],
            session_start_equity=session_start_equity,
            current_equity=account["equity"],
            session_trades=session_trades,
            bars_1m=bars, symbol=symbol,
        )

        # 4. Battery (throttled)
        jev_error = False
        try:
            battery = throttle.ask(state)
            last_battery = battery
        except Exception as e:
            jev_error = True
            battery = last_battery  # reuse last if available
            print(f"  [tick {tick_count}] Jev error: {e}")

        # Ladder
        rung = ladder_eval(battery, state, tick_start, jev_error=jev_error)

        action = "STAND_DOWN"
        if rung in ("RUN", "REDUCE") and battery:
            # 5. Policy
            action = compose_action(battery, state)
        elif rung == "RULES_ONLY":
            action = "QUOTE_WIDE"
        elif rung in ("KILL", "HOLD_LATE"):
            action = "KILL" if rung == "KILL" else "STAND_DOWN"

        # 6. Pricing
        vol = state.get("volatility_1m_pct") or 0.01
        r_price, half_bps = avellaneda_stoikov(
            mid=(bid + ask) / 2, position_qty=pos["qty"],
            volatility=vol / 100, T=3600, t=tick_count * 2,
        )
        widen = 2.0 if action in ("WIDEN", "QUOTE_WIDE") else 1.0
        quote_bid, quote_ask = quote_prices((bid + ask) / 2, half_bps, widen_factor=widen)

        # 7 + 8. Risk veto and execute
        working = alpaca.get_working_orders(symbol) if not (client.mock or dry_execution) else []
        working_buys = sum(1 for o in working if o["side"] == "buy")
        inv_frac = abs(pos["qty"] * (bid + ask) / 2) / 200.0  # vs max position

        if action in ("QUOTE_BOTH_SIDES", "QUOTE_WIDE", "WIDEN") and is_running():
            for side, px in [("buy", quote_bid), ("sell", quote_ask)]:
                if side == "sell" and pos["qty"] <= 0:
                    continue  # nothing to sell
                try:
                    check_order(
                        side=side, notional_usd=NOTIONAL_USD,
                        position_qty=pos["qty"],
                        position_notional_usd=pos["notional"],
                        working_buy_count=working_buys,
                        spread_bps=state["spread_bps"],
                        mid=(bid + ask) / 2,
                        session_start_equity=session_start_equity,
                        current_equity=account["equity"],
                        inventory_fraction=inv_frac,
                        mock=client.mock or dry_execution,
                    )
                    if not (client.mock or dry_execution):
                        alpaca.place_limit_order(symbol, side, NOTIONAL_USD, px, kind)
                except RiskVeto as e:
                    pass  # silent on normal vetoes

        elif action == "KILL":
            if not (client.mock or dry_execution):
                alpaca.cancel_our_orders(symbol)
                alpaca.close_position(symbol)
            print(f"  [tick {tick_count}] KILL — position closed, stopping.")
            break

        # 9. Log
        bat_dict = {}
        if battery:
            bat_dict = {
                "regime": battery.regime, "direction": battery.direction,
                "toxic_flow": battery.toxic_flow, "confidence": battery.confidence,
                "mock": battery.mock, "latency_ms": round(battery.latency_ms, 1),
            }

        record = {
            "tick": tick_count,
            "ts": time.time(),
            "symbol": symbol,
            "state": {k: state[k] for k in ("mid", "spread_bps", "position_qty",
                                               "drawdown_pct", "position_side")},
            "battery": bat_dict,
            "rung": rung,
            "action": action,
        }

        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(record) + "\n")
        LATEST_PATH.write_text(json.dumps(record, indent=2))

        mid = (bid + ask) / 2
        bat_str = ""
        if battery:
            bat_str = (f"  {battery.regime[:4]} {battery.direction[:4]} "
                       f"conf={battery.confidence:.2f} {'MOCK' if battery.mock else ''}")
        print(f"  tick {tick_count:4d} | {symbol} | mid={mid:.2f} | "
              f"pos={pos['qty']:+.4f} | {rung:10s} | {action:20s} |{bat_str}")

        tick_count += 1
        # Tick rate: 2s default, or sleep until next bar
        if not bar_interval_s:
            elapsed = time.time() - tick_start
            time.sleep(max(0, 2.0 - elapsed))

    # Clean exit
    if not shutdown:
        cancelled = alpaca.cancel_our_orders(symbol)
        if cancelled:
            print(f"Cancelled {cancelled} resting order(s) placed this run.")
    print(f"Done. {tick_count} ticks.")
