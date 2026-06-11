"""
============================================================
Bluestock Fintech — Mutual Fund Analytics Capstone
Day 1: data_ingestion.py

PURPOSE:
  Load all 10 raw CSV datasets, print shape/dtypes/head,
  flag anomalies, and produce a data-quality report.

HOW TO RUN:
  python scripts/data_ingestion.py

WHAT YOU'LL LEARN:
  - How to load multiple CSVs in a loop with robust error handling
  - How to detect data quality issues automatically (nulls,
    duplicates, type mismatches) — the kind of thing that
    impresses senior data engineers
  - How to write a compact but professional data-quality report

AUTHOR: Bluestock Fintech Internship Capstone 2026
============================================================
"""

import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# ── Path setup ───────────────────────────────────────────────
# Using pathlib.Path so this works on Windows, Mac, and Linux.
# Never hard-code paths like "C:/Users/rudra/..." — that breaks
# on every other machine.
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR  = BASE_DIR / "data" / "raw"
PROC_DIR = BASE_DIR / "data" / "processed"

# Ensure processed directory exists
PROC_DIR.mkdir(parents=True, exist_ok=True)


# ── Dataset registry ─────────────────────────────────────────
# We define each dataset as a dict so we can loop cleanly.
# This is a common pattern in production ETL pipelines —
# configuration-driven ingestion instead of repeated copy-paste.
DATASETS = [
    {
        "key":  "fund_master",
        "file": "01_fund_master.csv",
        "desc": "Master list of 40 mutual fund schemes",
        "pk":   "amfi_code",
        "date_cols": ["launch_date"],
    },
    {
        "key":  "nav_history",
        "file": "02_nav_history.csv",
        "desc": "Daily NAV for all 40 schemes (Jan 2022 – May 2026)",
        "pk":   None,
        "date_cols": ["date"],
    },
    {
        "key":  "aum_by_fund_house",
        "file": "03_aum_by_fund_house.csv",
        "desc": "Quarterly AUM per fund house (2022–2025)",
        "pk":   None,
        "date_cols": ["date"],
    },
    {
        "key":  "monthly_sip_inflows",
        "file": "04_monthly_sip_inflows.csv",
        "desc": "Monthly SIP inflows and account counts",
        "pk":   "month",
        "date_cols": ["month"],
    },
    {
        "key":  "category_inflows",
        "file": "05_category_inflows.csv",
        "desc": "Net inflows by fund category (FY 2024-25)",
        "pk":   None,
        "date_cols": ["month"],
    },
    {
        "key":  "industry_folio_count",
        "file": "06_industry_folio_count.csv",
        "desc": "Industry folio count by type (2022–2025)",
        "pk":   "month",
        "date_cols": ["month"],
    },
    {
        "key":  "scheme_performance",
        "file": "07_scheme_performance.csv",
        "desc": "Risk-return metrics per scheme (as of Dec 2025)",
        "pk":   "amfi_code",
        "date_cols": [],
    },
    {
        "key":  "investor_transactions",
        "file": "08_investor_transactions.csv",
        "desc": "32K+ simulated SIP/Lumpsum/Redemption transactions",
        "pk":   None,
        "date_cols": ["transaction_date"],
    },
    {
        "key":  "portfolio_holdings",
        "file": "09_portfolio_holdings.csv",
        "desc": "Top equity holdings per fund (Dec 2025)",
        "pk":   None,
        "date_cols": ["portfolio_date"],
    },
    {
        "key":  "benchmark_indices",
        "file": "10_benchmark_indices.csv",
        "desc": "Daily closing values for Nifty 50, 100, Midcap, BSE",
        "pk":   None,
        "date_cols": ["date"],
    },
]


# ── Helper: quick anomaly scanner ───────────────────────────
def scan_anomalies(df: pd.DataFrame, pk: str | None) -> dict:
    """
    Run a quick, automated data-quality scan on a DataFrame.

    Returns a dict with:
      - null_counts:   columns with missing values
      - duplicate_rows: count of fully duplicate rows
      - pk_dupes:       duplicate primary key values (if pk given)
      - negative_nav:   flag if numeric cols have unexpected negatives
    """
    issues = {}

    # 1. Null counts (only columns that actually have nulls)
    null_counts = df.isnull().sum()
    null_counts = null_counts[null_counts > 0]
    if len(null_counts):
        issues["null_counts"] = null_counts.to_dict()

    # 2. Duplicate rows
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        issues["duplicate_rows"] = int(dup_count)

    # 3. Primary key duplicates
    if pk and pk in df.columns:
        pk_dupes = df[pk].duplicated().sum()
        if pk_dupes > 0:
            issues["pk_dupes"] = int(pk_dupes)

    # 4. Negative values in columns that should be positive
    suspicious_cols = [c for c in df.select_dtypes("number").columns
                       if any(kw in c.lower() for kw in
                              ["nav", "aum", "amount", "inflow", "weight"])]
    for col in suspicious_cols:
        neg_count = (df[col] < 0).sum()
        if neg_count > 0:
            issues.setdefault("negative_values", {})[col] = int(neg_count)

    return issues


# ── Main ingestion loop ──────────────────────────────────────
def run_ingestion() -> dict[str, pd.DataFrame]:
    """
    Load every dataset from RAW_DIR, print a rich profile,
    collect anomalies, and return a dict of DataFrames.
    """
    dataframes = {}
    quality_report = {}

    separator = "=" * 65

    print(separator)
    print("  BLUESTOCK FINTECH — Day 1: Data Ingestion")
    print(f"  Reading from: {RAW_DIR}")
    print(separator)

    for ds in DATASETS:
        filepath = RAW_DIR / ds["file"]

        if not filepath.exists():
            print(f"\n[WARN] File not found: {filepath}")
            continue

        # Load CSV — parse date columns immediately so downstream
        # code never has to guess types.
        try:
            df = pd.read_csv(
                filepath,
                parse_dates=ds["date_cols"] if ds["date_cols"] else False,
            )
        except Exception as exc:
            print(f"\n[ERROR] Could not read {ds['file']}: {exc}")
            continue

        dataframes[ds["key"]] = df

        # ── Print dataset profile ────────────────────────────
        print(f"\n{'─'*65}")
        print(f"  📁  {ds['key'].upper().replace('_', ' ')}")
        print(f"  {ds['desc']}")
        print(f"{'─'*65}")
        print(f"  Shape      : {df.shape[0]:,} rows  ×  {df.shape[1]} columns")
        print(f"  Memory     : {df.memory_usage(deep=True).sum() / 1024:.1f} KB")

        print("\n  dtypes:")
        for col, dtype in df.dtypes.items():
            null_pct = df[col].isnull().mean() * 100
            null_str = f"  ⚠  {null_pct:.1f}% null" if null_pct > 0 else ""
            print(f"    {col:<35} {str(dtype):<12}{null_str}")

        print("\n  Head (2 rows):")
        print(df.head(2).to_string(index=False))

        # ── Unique value summaries for key categorical cols ──
        cat_cols = df.select_dtypes("object").columns.tolist()
        if cat_cols:
            print("\n  Key categoricals:")
            for col in cat_cols[:4]:          # Show first 4 to keep output clean
                uniq = df[col].nunique()
                samples = df[col].dropna().unique()[:5].tolist()
                print(f"    {col:<30} {uniq:>4} unique | sample: {samples}")

        # ── Anomaly scan ─────────────────────────────────────
        anomalies = scan_anomalies(df, ds["pk"])
        quality_report[ds["key"]] = anomalies

        if anomalies:
            print("\n  ⚠  Anomalies detected:")
            for issue, detail in anomalies.items():
                print(f"    [{issue}]: {detail}")
        else:
            print("\n  ✅ No anomalies detected")

    # ── Final data-quality summary ───────────────────────────
    print(f"\n{separator}")
    print("  DATA QUALITY SUMMARY")
    print(separator)
    clean  = sum(1 for v in quality_report.values() if not v)
    issues = sum(1 for v in quality_report.values() if v)
    print(f"  Datasets loaded : {len(dataframes)}")
    print(f"  Clean           : {clean}")
    print(f"  Issues found    : {issues}")
    print()
    for ds_key, anomalies in quality_report.items():
        status = "✅ CLEAN" if not anomalies else f"⚠  {len(anomalies)} issue(s)"
        print(f"    {ds_key:<30} {status}")

    # ── AMFI code validation ─────────────────────────────────
    # Every amfi_code in fund_master MUST exist in nav_history.
    # This is a referential integrity check — critical before
    # loading into a relational database.
    print(f"\n{separator}")
    print("  AMFI CODE VALIDATION (Referential Integrity)")
    print(separator)

    if "fund_master" in dataframes and "nav_history" in dataframes:
        master_codes = set(dataframes["fund_master"]["amfi_code"].astype(str))
        nav_codes    = set(dataframes["nav_history"]["amfi_code"].astype(str))

        missing_in_nav = master_codes - nav_codes
        extra_in_nav   = nav_codes - master_codes

        print(f"  fund_master codes : {len(master_codes)}")
        print(f"  nav_history codes : {len(nav_codes)}")

        if not missing_in_nav:
            print("  ✅ All fund_master codes are present in nav_history")
        else:
            print(f"  ❌ {len(missing_in_nav)} codes in fund_master MISSING from nav_history:")
            print(f"     {sorted(missing_in_nav)}")

        if extra_in_nav:
            print(f"  ℹ  {len(extra_in_nav)} codes in nav_history not in fund_master (orphans)")
    else:
        print("  [SKIP] fund_master or nav_history not loaded")

    print(f"\n{separator}")
    print("  Day 1 Ingestion Complete ✅")
    print(separator)

    return dataframes


# ── Entry point ──────────────────────────────────────────────
if __name__ == "__main__":
    # When you run: python scripts/data_ingestion.py
    # Python sets __name__ to "__main__", so this block runs.
    # When another script imports this file, this block is SKIPPED.
    # That's best-practice module design.
    loaded = run_ingestion()
    print(f"\nDataFrames available: {list(loaded.keys())}")
