#!/usr/bin/env python3
"""
Zenoti → Monday.com Daily Sync

Pulls appointment, sales, and membership data from Zenoti,
parses key metrics, and pushes to a Monday.com board.

Usage:
    python sync.py                  # Pull yesterday's report
    python sync.py --date 2026-03-18  # Pull specific date
    python sync.py --setup          # Create Monday.com board
    python sync.py --scheduled      # Run on daily schedule
"""

import argparse
import json
import logging
import sys
from datetime import datetime, date
from pathlib import Path

import schedule
import time

from zenoti_client import ZenotiClient
from monday_client import MondayClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config():
    if not CONFIG_PATH.exists():
        log.error(
            "config.json not found. Copy config.example.json to config.json and fill in your API keys."
        )
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        return json.load(f)


def setup_board(config):
    """Create a new Monday.com board with the right columns."""
    monday = MondayClient(config["monday"]["api_key"])
    board_id = monday.create_report_board("Zenoti Daily Report")
    log.info(f"Board created! ID: {board_id}")
    log.info("Update config.json with this board_id to start syncing.")
    return board_id


def run_sync(config, target_date=None):
    """Pull Zenoti data and push to Monday.com."""
    zenoti = ZenotiClient(
        api_key=config["zenoti"]["api_key"],
        base_url=config["zenoti"]["api_base_url"],
    )
    monday = MondayClient(config["monday"]["api_key"])

    board_id = config["monday"].get("board_id")
    if not board_id:
        log.error("No board_id in config.json. Run with --setup first.")
        sys.exit(1)

    center_ids = config["zenoti"]["center_ids"]

    if target_date is None:
        target_date = date.today()
        # Default to yesterday for complete data
        from datetime import timedelta
        target_date = target_date - timedelta(days=1)

    log.info(f"Pulling Zenoti report for {target_date.isoformat()}...")
    report = zenoti.pull_daily_report(center_ids, date=target_date)

    # Log summary
    for location, data in report["locations"].items():
        appts = data["appointments"]
        rev = data["revenue"]
        mem = data["memberships"]
        log.info(
            f"  {location}: {appts['total']} appts "
            f"({appts.get('completion_rate', 0)}% complete), "
            f"${rev['total_revenue']:,.2f} revenue, "
            f"{mem['active']} active members"
        )

    log.info("Pushing to Monday.com...")
    monday.push_report(str(board_id), report)
    log.info("Sync complete.")


def run_scheduled(config):
    """Run sync on a daily schedule."""
    run_time = config.get("schedule", {}).get("run_daily_at", "07:00")
    log.info(f"Scheduler started. Will run daily at {run_time} ET.")

    schedule.every().day.at(run_time).do(run_sync, config)

    # Also run immediately on start
    run_sync(config)

    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="Zenoti → Monday.com sync")
    parser.add_argument("--setup", action="store_true", help="Create Monday.com board")
    parser.add_argument("--date", type=str, help="Date to pull (YYYY-MM-DD)")
    parser.add_argument("--scheduled", action="store_true", help="Run on daily schedule")

    args = parser.parse_args()
    config = load_config()

    if args.setup:
        setup_board(config)
    elif args.scheduled:
        run_scheduled(config)
    else:
        target_date = None
        if args.date:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        run_sync(config, target_date)


if __name__ == "__main__":
    main()
