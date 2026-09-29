"""Entry point: python -m jevloop <subcommand>."""
import argparse
import sys

# Force UTF-8 on Windows consoles to prevent cp1252 charmap encoding errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser(prog="jevloop")
    sub = parser.add_subparsers(dest="cmd")

    run_p = sub.add_parser("run", help="Run the trading loop")
    run_p.add_argument("--paper", action="store_true", default=True)
    run_p.add_argument("--live", action="store_true")
    run_p.add_argument("--mock", action="store_true", help="Force mock Jev client (no orders)")
    run_p.add_argument("--dry-execution", action="store_true", help="Real data/battery, no orders")
    run_p.add_argument("--ticks", type=int, default=60)
    run_p.add_argument("--forever", action="store_true", help="Run until Ctrl+C")
    run_p.add_argument("--symbol", type=str, default=None)
    run_p.add_argument("--bar", type=str, default=None,
                       help="Bar interval: 1m/5m/15m/30m/1h (one decision per close)")

    sub.add_parser("explain-split", help="Print the deterministic vs probabilistic table")
    sub.add_parser("calibrate", help="Brier score + reliability table from log")
    sub.add_parser("serve", help="Start the dashboard at http://127.0.0.1:8765")
    sub.add_parser("pause", help="Pause order placement (same as Stop on dashboard)")
    sub.add_parser("resume", help="Resume order placement (same as Start on dashboard)")

    vs_p = sub.add_parser("validate-symbol", help="Resolve a symbol before running")
    vs_p.add_argument("symbol")

    args = parser.parse_args()

    if args.cmd == "run":
        from jevloop.loop import run
        run(args)
    elif args.cmd == "explain-split":
        from jevloop.split import explain_split
        explain_split()
    elif args.cmd == "calibrate":
        from jevloop.calibrate import calibrate
        calibrate()
    elif args.cmd == "serve":
        from jevloop.serve import serve
        serve()
    elif args.cmd == "pause":
        from jevloop.control import pause
        pause()
        print("PAUSED — no new orders will be placed until resume.")
    elif args.cmd == "resume":
        from jevloop.control import resume
        resume()
        print("RUNNING — order placement resumed.")
    elif args.cmd == "validate-symbol":
        from jevloop.assets import resolve
        spec = resolve(args.symbol)
        print(f"✓ {spec['symbol']} → {spec['kind']} | notional_floor=${spec['notional_floor']} "
              f"| qty_precision={spec['qty_precision']} | shorting={spec['shorting']}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
