"""
============================================================
Bluestock Fintech — Mutual Fund Analytics Capstone
Day 1: live_nav_fetch.py

PURPOSE:
  Fetch live / historical NAV data from the free mfapi.in API
  for 6 key schemes and save each as a CSV in data/raw/.

API ENDPOINT:
  GET https://api.mfapi.in/mf/{scheme_code}
  Returns JSON: { status: "SUCCESS", meta: {...}, data: [{date, nav}, ...] }
  No authentication required. Rate limit: ~10 requests/second.

HOW TO RUN:
  python scripts/live_nav_fetch.py

WHAT YOU'LL LEARN:
  - How to call a real-world REST API from Python
  - Robust error handling (timeouts, HTTP errors, bad JSON)
  - How to normalise the JSON response into a clean DataFrame
  - Why you save API responses to disk immediately (so you
    don't hammer the API every time you re-run analysis)

AUTHOR: Bluestock Fintech Internship Capstone 2026
============================================================
"""

import time
import json
from pathlib import Path
from datetime import datetime

import requests
import pandas as pd

# ── Config ───────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
RAW_DIR    = BASE_DIR / "data" / "raw"
API_BASE   = "https://api.mfapi.in/mf"

# The 6 schemes we want to fetch live NAV for.
# Format: { scheme_name: amfi_code }
# These are real AMFI codes — you can verify on amfiindia.com
SCHEMES = {
    "HDFC_Top100_Direct":        125497,
    "SBI_Bluechip_Regular":      119551,
    "ICICI_Pru_Bluechip_Direct": 120503,
    "Nippon_LargeCap_Direct":    118632,
    "Axis_Bluechip_Direct":      119092,
    "Kotak_Bluechip_Direct":     120841,
}

# Request settings
TIMEOUT_SECONDS = 15     # Fail fast if API is slow
RETRY_COUNT     = 3      # Retry on transient failures
RETRY_DELAY     = 2.0    # Seconds between retries
POLITE_DELAY    = 0.5    # Pause between scheme fetches (be a good API citizen)


# ── Core fetch function ──────────────────────────────────────
def fetch_nav(scheme_code: int, scheme_name: str) -> pd.DataFrame | None:
    """
    Fetch complete NAV history for one scheme from mfapi.in.

    The API returns newest-first, so we reverse to get
    chronological order (oldest → newest).

    Returns a clean DataFrame with columns:
      amfi_code | scheme_name | date | nav

    Returns None if the fetch fails after all retries.
    """
    url = f"{API_BASE}/{scheme_code}"

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            print(f"  [{attempt}/{RETRY_COUNT}] Fetching {scheme_name} "
                  f"(code: {scheme_code}) ...", end=" ", flush=True)

            response = requests.get(url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()  # Raises HTTPError for 4xx/5xx

            payload = response.json()

            # ── Validate the response structure ──────────────
            # The API can return { "status": "ERROR" } for invalid codes
            if payload.get("status") != "SUCCESS":
                print(f"❌  API error: {payload.get('status')}")
                return None

            data_records = payload.get("data", [])
            meta         = payload.get("meta", {})

            if not data_records:
                print("❌  Empty data array returned")
                return None

            # ── Build DataFrame ───────────────────────────────
            df = pd.DataFrame(data_records)

            # The API returns date as "DD-MM-YYYY" string — parse it
            df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
            df["nav"]  = pd.to_numeric(df["nav"], errors="coerce")

            # Drop any rows where NAV parsing failed
            df = df.dropna(subset=["nav"])

            # Sort chronologically (API gives newest first)
            df = df.sort_values("date").reset_index(drop=True)

            # Add identifier columns
            df.insert(0, "amfi_code",    scheme_code)
            df.insert(1, "scheme_name",  meta.get("scheme_name", scheme_name))

            date_range = f"{df['date'].min().date()} → {df['date'].max().date()}"
            print(f"✅  {len(df):,} rows | {date_range}")

            return df

        except requests.exceptions.Timeout:
            print(f"⏱  Timeout (attempt {attempt})")
        except requests.exceptions.HTTPError as e:
            print(f"HTTP {e.response.status_code}: {e}")
            break   # Don't retry on HTTP errors (4xx/5xx are not transient)
        except requests.exceptions.ConnectionError:
            print(f"🔌 Connection error (attempt {attempt})")
        except json.JSONDecodeError:
            print("❌  Invalid JSON in response")
            break
        except Exception as exc:
            print(f"❌  Unexpected error: {exc}")
            break

        if attempt < RETRY_COUNT:
            print(f"     Retrying in {RETRY_DELAY}s ...")
            time.sleep(RETRY_DELAY)

    print(f"  [FAIL] Could not fetch {scheme_name} after {RETRY_COUNT} attempts")
    return None


# ── Save to CSV ──────────────────────────────────────────────
def save_to_csv(df: pd.DataFrame, scheme_name: str) -> Path:
    """
    Save a fetched NAV DataFrame to data/raw/ as a CSV.

    We use a timestamp in the filename so you can track when
    you last fetched the data — useful for scheduled pipelines.
    """
    # Format: scheme_name_nav_YYYYMMDD.csv
    today     = datetime.today().strftime("%Y%m%d")
    filename  = f"{scheme_name.lower()}_nav_{today}.csv"
    filepath  = RAW_DIR / filename

    df.to_csv(filepath, index=False, date_format="%Y-%m-%d")
    print(f"  💾 Saved: {filepath.name}  ({df.memory_usage(deep=True).sum() // 1024} KB)")
    return filepath


# ── Main ─────────────────────────────────────────────────────
def run_live_nav_fetch() -> dict[str, pd.DataFrame]:
    """
    Fetch NAV data for all configured schemes.
    Returns dict of { scheme_name: DataFrame }.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    sep = "=" * 65
    print(sep)
    print("  BLUESTOCK FINTECH — Day 1: Live NAV Fetch (mfapi.in)")
    print(sep)
    print(f"  Fetching {len(SCHEMES)} schemes from {API_BASE}")
    print()

    results       = {}
    failed        = []
    all_frames    = []

    for scheme_name, scheme_code in SCHEMES.items():
        df = fetch_nav(scheme_code, scheme_name)

        if df is not None:
            save_to_csv(df, scheme_name)
            results[scheme_name] = df
            all_frames.append(df)
        else:
            failed.append(scheme_name)

        # Polite delay between requests — don't hammer the API
        time.sleep(POLITE_DELAY)

    # ── Combine all fetched NAV into one master file ─────────
    # This is useful for the EDA notebook — one file to load
    if all_frames:
        combined = pd.concat(all_frames, ignore_index=True)
        combined_path = RAW_DIR / "live_nav_combined.csv"
        combined.to_csv(combined_path, index=False, date_format="%Y-%m-%d")
        print(f"\n  📦 Combined file: live_nav_combined.csv ({len(combined):,} rows)")

    # ── Summary ──────────────────────────────────────────────
    print(f"\n{sep}")
    print("  FETCH SUMMARY")
    print(sep)
    print(f"  ✅  Success : {len(results)} schemes")
    print(f"  ❌  Failed  : {len(failed)} schemes")
    if failed:
        print(f"  Failed schemes: {failed}")

    print(f"\n  Files saved to: {RAW_DIR}")
    print(sep)

    return results


# ── If API is unavailable, load the pre-fetched files ────────
def load_prefetched_nav() -> dict[str, pd.DataFrame]:
    """
    Fallback: load the pre-fetched NAV CSVs that came with
    the project (hdfc_top100_nav_live.csv, sbi_bluechip_nav_live.csv).

    These were fetched from mfapi.in and are included so the
    project works even without internet access.
    """
    prefetched = {
        "HDFC_Top100_Direct":   RAW_DIR / "hdfc_top100_nav_live.csv",
        "SBI_Bluechip_Regular": RAW_DIR / "sbi_bluechip_nav_live.csv",
    }

    loaded = {}
    print("\n  Loading pre-fetched NAV files (offline mode)...")
    for name, path in prefetched.items():
        if path.exists():
            df = pd.read_csv(path, parse_dates=["date"])
            df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
            df = df.sort_values("date").reset_index(drop=True)
            loaded[name] = df
            print(f"  ✅  {name}: {len(df):,} rows | "
                  f"{df['date'].min().date()} → {df['date'].max().date()}")
    return loaded


# ── Entry point ──────────────────────────────────────────────
if __name__ == "__main__":
    # Try live fetch first; fall back to pre-fetched files if API is down
    try:
        fetched = run_live_nav_fetch()
    except Exception as exc:
        print(f"\n[WARN] Live fetch encountered an error: {exc}")
        print("  Falling back to pre-fetched NAV files ...\n")
        fetched = load_prefetched_nav()

    if fetched:
        print(f"\nLoaded {len(fetched)} NAV dataset(s).")
        for name, df in fetched.items():
            print(f"  {name}: {df.shape}")
    else:
        print("\n[ERROR] No NAV data available. Check your internet connection.")
