"""
Bluestock Fintech — Day 2: etl_pipeline.py
Clean all 10 datasets and load into SQLite star schema.
Run: python scripts/etl_pipeline.py
"""

import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR  = BASE_DIR / "data" / "raw"
PROC_DIR = BASE_DIR / "data" / "processed"
DB_DIR   = BASE_DIR / "data" / "db"
DB_PATH  = DB_DIR / "bluestock_mf.db"

PROC_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)


def clean_fund_master():
    df = pd.read_csv(RAW_DIR / "01_fund_master.csv", parse_dates=["launch_date"])
    df.drop_duplicates(subset=["amfi_code"], inplace=True)
    df["fund_house"]    = df["fund_house"].str.strip()
    df["scheme_name"]   = df["scheme_name"].str.strip()
    df["risk_category"] = df["risk_category"].str.strip()
    df["expense_ratio_pct"] = df["expense_ratio_pct"].clip(0.05, 3.0)
    print(f"  dim_fund           :    {len(df):>3} rows  ✅")
    return df


def clean_nav_history():
    df = pd.read_csv(RAW_DIR / "02_nav_history.csv", parse_dates=["date"])
    df.drop_duplicates(subset=["amfi_code", "date"], inplace=True)
    df = df[df["nav"] > 0].copy()
    df.sort_values(["amfi_code", "date"], inplace=True)

    # Pivot wide → reindex to business days → ffill → melt back
    pivot    = df.pivot(index="date", columns="amfi_code", values="nav")
    full_idx = pd.date_range(pivot.index.min(), pivot.index.max(), freq="B")
    pivot    = pivot.reindex(full_idx).ffill()

    df = (pivot.reset_index()
               .melt(id_vars="index", var_name="amfi_code", value_name="nav")
               .rename(columns={"index": "date"})
               .dropna(subset=["nav"])
               .sort_values(["amfi_code", "date"])
               .reset_index(drop=True))

    df["daily_return_pct"] = (df.groupby("amfi_code")["nav"]
                                .pct_change().round(6))
    print(f"  fact_nav           : {len(df):>6} rows  ✅  (ffill + daily_return)")
    return df


def clean_aum():
    df = pd.read_csv(RAW_DIR / "03_aum_by_fund_house.csv", parse_dates=["date"])
    df.drop_duplicates(inplace=True)
    print(f"  fact_aum           :    {len(df):>3} rows  ✅")
    return df


def clean_sip_inflows():
    df = pd.read_csv(RAW_DIR / "04_monthly_sip_inflows.csv", parse_dates=["month"])
    df.sort_values("month", inplace=True)
    df.reset_index(drop=True, inplace=True)
    print(f"  fact_sip_industry  :    {len(df):>3} rows  ✅")
    return df


def clean_category_inflows():
    df = pd.read_csv(RAW_DIR / "05_category_inflows.csv", parse_dates=["month"])
    df.drop_duplicates(inplace=True)
    df["category"] = df["category"].str.strip()
    print(f"  fact_category_inflows: {len(df):>3} rows  ✅")
    return df


def clean_folio_count():
    df = pd.read_csv(RAW_DIR / "06_industry_folio_count.csv", parse_dates=["month"])
    df.drop_duplicates(inplace=True)
    print(f"  fact_folio_count   :    {len(df):>3} rows  ✅")
    return df


def clean_scheme_performance():
    df = pd.read_csv(RAW_DIR / "07_scheme_performance.csv")
    df.drop_duplicates(subset=["amfi_code"], inplace=True)
    numeric = ["return_1yr_pct","return_3yr_pct","return_5yr_pct",
               "alpha","beta","sharpe_ratio","sortino_ratio",
               "std_dev_ann_pct","max_drawdown_pct","expense_ratio_pct"]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    print(f"  fact_performance   :    {len(df):>3} rows  ✅")
    return df


def clean_transactions():
    df = pd.read_csv(RAW_DIR / "08_investor_transactions.csv",
                     parse_dates=["transaction_date"])
    df = df[df["amount_inr"] > 0].copy()
    df.drop_duplicates(inplace=True)
    df["transaction_type"] = df["transaction_type"].str.strip().str.title()
    df["kyc_status"]       = df["kyc_status"].str.strip()
    df["city_tier"]        = df["city_tier"].str.upper().str.strip()
    print(f"  fact_transactions  : {len(df):>6} rows  ✅")
    return df


def clean_portfolio():
    df = pd.read_csv(RAW_DIR / "09_portfolio_holdings.csv",
                     parse_dates=["portfolio_date"])
    df.drop_duplicates(inplace=True)
    df["weight_pct"] = df["weight_pct"].clip(0, 100)
    print(f"  fact_portfolio     :   {len(df):>4} rows  ✅")
    return df


def clean_benchmarks():
    df = pd.read_csv(RAW_DIR / "10_benchmark_indices.csv", parse_dates=["date"])
    df.drop_duplicates(inplace=True)
    df = df[df["close_value"] > 0].copy()
    df.sort_values(["index_name", "date"], inplace=True)
    df["daily_return_pct"] = (df.groupby("index_name")["close_value"]
                                .pct_change().round(6))
    print(f"  fact_benchmarks    : {len(df):>6} rows  ✅")
    return df


def build_dim_date():
    dates = pd.date_range("2022-01-01", "2026-05-31", freq="D")
    df = pd.DataFrame({"date": dates})
    df["year"]        = df["date"].dt.year
    df["month"]       = df["date"].dt.month
    df["month_name"]  = df["date"].dt.strftime("%B")
    df["quarter"]     = df["date"].dt.quarter
    df["day_of_week"] = df["date"].dt.day_name()
    df["is_weekday"]  = (df["date"].dt.weekday < 5).astype(int)
    df["fy_year"]     = df["date"].apply(
        lambda d: d.year if d.month >= 4 else d.year - 1)
    print(f"  dim_date           : {len(df):>6} rows  ✅")
    return df


def load_to_sqlite(tables):
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    for tname, df in tables.items():
        df_copy = df.copy()
        for col in df_copy.select_dtypes(include=["datetime64"]).columns:
            df_copy[col] = df_copy[col].dt.strftime("%Y-%m-%d")
        df_copy.to_sql(tname, conn, if_exists="replace", index=False)
        count = conn.execute(f"SELECT COUNT(*) FROM [{tname}]").fetchone()[0]
        print(f"  {tname:<30} → {count:>7,} rows")
    conn.close()
    size_kb = DB_PATH.stat().st_size // 1024
    print(f"\n  DB: {DB_PATH.name}  ({size_kb:,} KB)")


def save_processed(tables):
    for name, df in tables.items():
        df.to_csv(PROC_DIR / f"{name}.csv", index=False)
    print(f"  Processed CSVs → {PROC_DIR}")


def run_etl():
    sep = "=" * 65
    print(sep)
    print("  BLUESTOCK FINTECH — Day 2: ETL Pipeline")
    print(sep)

    print("\n[1/3] Cleaning all datasets ...")
    tables = {
        "dim_fund":              clean_fund_master(),
        "dim_date":              build_dim_date(),
        "fact_nav":              clean_nav_history(),
        "fact_transactions":     clean_transactions(),
        "fact_performance":      clean_scheme_performance(),
        "fact_portfolio":        clean_portfolio(),
        "fact_aum":              clean_aum(),
        "fact_sip_industry":     clean_sip_inflows(),
        "fact_category_inflows": clean_category_inflows(),
        "fact_folio_count":      clean_folio_count(),
        "fact_benchmarks":       clean_benchmarks(),
    }

    print("\n[2/3] Loading into SQLite ...")
    load_to_sqlite(tables)

    print("\n[3/3] Saving processed CSVs ...")
    save_processed(tables)

    print(f"\n{sep}")
    print("  Day 2: ETL Complete ✅")
    print(sep)
    return tables


if __name__ == "__main__":
    run_etl()
