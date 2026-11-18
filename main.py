"""Main CLI and Autonomous Server Entrypoint for GTA 6 Autopilot."""

import argparse
import sys
import threading
from pathlib import Path
from src.config import SystemConfig, ensure_directories
from src.database import Database
from src.engine import AutopilotEngine
from src.dashboard import run_dashboard_server, get_local_ip


def parse_args():
    parser = argparse.ArgumentParser(
        description="GTA 6 Autonomous 24/7 Clipping & Cross-Posting Pipeline"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for responsive mobile & PC web dashboard (default: 8080)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host binding (0.0.0.0 allows mobile phone access)",
    )
    parser.add_argument(
        "--low-spec",
        action="store_true",
        default=True,
        help="Enable low-spec PC optimization mode (default: True)",
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run a single clipping and publishing cycle then exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Run in simulation mode (safe testing without live upload)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    ensure_directories()

    config = SystemConfig.load()
    config.port = args.port
    config.host = args.host
    config.low_spec_mode = args.low_spec
    config.social.dry_run = args.dry_run
    config.save()

    db = Database()
    engine = AutopilotEngine(config, db)

    local_ip = get_local_ip()

    print("=" * 65)
    print(" 🌴 GTA 6 AUTOPILOT - 24/7 CLIPPING & CROSS-POSTING SYSTEM 🌴")
    print("=" * 65)
    print(f" [✓] PC Dashboard:      http://localhost:{config.port}")
    print(f" [✓] Mobile Access:     http://{local_ip}:{config.port}")
    print(f" [✓] Low-Spec PC Mode:  {'ENABLED (Optimized)' if config.low_spec_mode else 'DISABLED'}")
    print(f" [✓] Dry-Run Mode:      {'ENABLED (Simulation)' if config.social.dry_run else 'LIVE PRODUCTION'}")
    print("=" * 65)

    if args.run_once:
        print("[*] Executing single autonomous cycle...")
        result = engine.run_full_cycle()
        print(f"[✓] Single cycle complete: {result}")
        sys.exit(0)

    # Start autonomous engine in background thread
    engine.start()
    print("[*] Autonomous background worker running...")
    print("[*] Press Ctrl+C to terminate.")

    # Run dashboard server on main thread
    try:
        run_dashboard_server(config, engine, db, block=True)
    except KeyboardInterrupt:
        print("\n[*] Shutting down GTA 6 Autopilot gracefully...")
        engine.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
