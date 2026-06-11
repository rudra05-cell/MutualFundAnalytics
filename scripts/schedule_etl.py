"""
Bluestock Fintech — Bonus B1: Scheduled ETL
Auto-fetches live NAV from mfapi.in every weekday at 8 PM
and appends to the SQLite database.

HOW TO RUN (always-on):
  python scripts/schedule_etl.py

HOW TO RUN AS A CRON JOB (Linux/Mac):
  crontab -e
  Add line:  0 20 * * 1-5 /usr/bin/python3 /path/to/scripts/schedule_etl.py

WINDOWS TASK SCHEDULER:
  Action: python scripts/schedule_etl.py
  Trigger: Daily at 8:00 PM, weekdays only
"""

import sqlite3, time, logging
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / "data" / "db" / "bluestock_mf.db"
LOG_PATH = BASE_DIR / "reports" / "etl_schedule.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()]
)
log = logging.getLogger("bluestock_etl")

SCHEMES = {
    125497: "HDFC Top 100 Direct",
    119551: "SBI Bluechip Regular",
    120503: "ICICI Pru Bluechip Direct",
    118632: "Nippon Large Cap Direct",
    119092: "Axis Bluechip Direct",
    120841: "Kotak Bluechip Direct",
}


def fetch_latest_nav(amfi_code: int) -> dict | None:
    """Fetch the most recent NAV for one scheme from mfapi.in."""
    try:
        r = requests.get(f"https://api.mfapi.in/mf/{amfi_code}", timeout=12)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "SUCCESS" or not data.get("data"):
            return None
        latest = data["data"][0]          # Newest record is first
        return {
            "amfi_code": amfi_code,
            "date":      latest["date"],   # "DD-MM-YYYY"
            "nav":       float(latest["nav"]),
        }
    except Exception as e:
        log.warning(f"  Fetch failed for {amfi_code}: {e}")
        return None


def upsert_nav(conn: sqlite3.Connection, record: dict) -> bool:
    """Insert new NAV record only if (amfi_code, date) doesn't already exist."""
    date_iso = pd.to_datetime(record["date"], format="%d-%m-%Y").strftime("%Y-%m-%d")
    exists = conn.execute(
        "SELECT 1 FROM fact_nav WHERE amfi_code=? AND date=?",
        (record["amfi_code"], date_iso)
    ).fetchone()
    if exists:
        return False   # Already loaded — no duplicate
    conn.execute(
        "INSERT INTO fact_nav (amfi_code, date, nav) VALUES (?,?,?)",
        (record["amfi_code"], date_iso, record["nav"])
    )
    return True


def run_daily_fetch():
    """Core job: fetch latest NAV for all schemes and load into SQLite."""
    log.info("=" * 60)
    log.info("Starting scheduled NAV fetch")
    conn    = sqlite3.connect(DB_PATH)
    inserted, skipped, failed = 0, 0, 0

    for code, name in SCHEMES.items():
        record = fetch_latest_nav(code)
        if record is None:
            log.warning(f"  FAIL  {name}")
            failed += 1
            continue
        if upsert_nav(conn, record):
            log.info(f"  NEW   {name}  NAV={record['nav']:.4f}  date={record['date']}")
            inserted += 1
        else:
            log.info(f"  SKIP  {name}  (already loaded for {record['date']})")
            skipped += 1
        time.sleep(0.4)

    conn.commit()
    conn.close()
    log.info(f"Done — inserted={inserted}  skipped={skipped}  failed={failed}")
    log.info("=" * 60)


def run_scheduler():
    """
    Check every minute if it's 8 PM on a weekday.
    When triggered, run the fetch job.
    Keeps running until you press Ctrl+C.
    """
    log.info("Scheduler started. Waiting for 8:00 PM weekday trigger...")
    log.info("Press Ctrl+C to stop.")

    last_run_date = None

    while True:
        now = datetime.now()
        is_weekday   = now.weekday() < 5          # Mon=0 … Fri=4
        is_8pm       = now.hour == 20 and now.minute == 0
        already_ran  = last_run_date == now.date()

        if is_weekday and is_8pm and not already_ran:
            log.info(f"Trigger fired at {now.strftime('%Y-%m-%d %H:%M')}")
            run_daily_fetch()
            last_run_date = now.date()

        time.sleep(60)    # Check every 60 seconds


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        # python scripts/schedule_etl.py --now  → run immediately (testing)
        log.info("Manual trigger (--now flag)")
        run_daily_fetch()
    else:
        run_scheduler()
