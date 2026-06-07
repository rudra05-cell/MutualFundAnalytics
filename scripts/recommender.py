"""
Bluestock Fintech — Day 6: recommender.py
Simple rule-based fund recommendation engine.
Run: python scripts/recommender.py
"""

from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / "data" / "db" / "bluestock_mf.db"
PROC_DIR = BASE_DIR / "data" / "processed"


RISK_MAP = {
    "Low":      ["Debt", "Liquid", "Gilt", "Short Duration"],
    "Moderate": ["Large Cap", "Hybrid", "Flexi Cap"],
    "High":     ["Mid Cap", "Small Cap", "ELSS"],
}

HORIZON_MAP = {
    "Short (< 1yr)":  "return_1yr_pct",
    "Medium (1-3yr)": "return_3yr_pct",
    "Long (3yr+)":    "return_5yr_pct",
}


def recommend(risk_appetite: str = "Moderate",
              investment_horizon: str = "Long (3yr+)",
              top_n: int = 3) -> pd.DataFrame:
    """
    Input : risk_appetite     — Low / Moderate / High
            investment_horizon — Short / Medium / Long
            top_n             — number of funds to return

    Output: DataFrame of recommended funds with key metrics
    """
    conn = sqlite3.connect(DB_PATH)
    perf = pd.read_sql("SELECT * FROM fact_performance", conn)
    fund = pd.read_sql("SELECT amfi_code, sub_category FROM dim_fund", conn)
    conn.close()

    perf = perf.merge(fund, on="amfi_code")

    allowed_cats = RISK_MAP.get(risk_appetite, RISK_MAP["Moderate"])
    return_col   = HORIZON_MAP.get(investment_horizon, "return_3yr_pct")

    filtered = perf[perf["sub_category"].isin(allowed_cats)].copy()

    if filtered.empty:
        filtered = perf[perf["category"].str.contains(
            "|".join(allowed_cats), case=False, na=False)].copy()

    if filtered.empty:
        print("  No matching funds — showing all funds")
        filtered = perf.copy()

    # Sort: return_col desc, then sharpe desc
    filtered.sort_values([return_col, "sharpe_ratio"], ascending=False, inplace=True)

    cols = ["scheme_name","fund_house","sub_category",
            return_col,"sharpe_ratio","alpha","max_drawdown_pct",
            "expense_ratio_pct","morningstar_rating"]
    return filtered[cols].head(top_n).reset_index(drop=True)


def cohort_analysis() -> pd.DataFrame:
    """
    Group investors by first transaction year.
    Compute avg SIP, total invested, fund preference per cohort.
    """
    conn = sqlite3.connect(DB_PATH)
    tx   = pd.read_sql("SELECT * FROM fact_transactions", conn, parse_dates=["transaction_date"])
    fund = pd.read_sql("SELECT amfi_code, sub_category FROM dim_fund", conn)
    conn.close()

    tx = tx.merge(fund, on="amfi_code")

    tx["first_year"] = (tx.groupby("investor_id")["transaction_date"]
                          .transform("min").dt.year)

    cohort = (tx.groupby(["first_year","transaction_type"])
                .agg(
                    num_transactions=("amount_inr","count"),
                    total_invested_cr=("amount_inr", lambda x: x.sum()/1e7),
                    avg_amount=("amount_inr","mean"),
                    unique_investors=("investor_id","nunique"),
                )
                .round(2)
                .reset_index())
    return cohort


def sip_continuity_analysis() -> pd.DataFrame:
    """
    For investors with 6+ SIP transactions, compute avg gap.
    Flag investors with gap > 35 days as 'at-risk'.
    """
    conn = sqlite3.connect(DB_PATH)
    tx   = pd.read_sql(
        "SELECT investor_id, transaction_date FROM fact_transactions "
        "WHERE transaction_type = 'Sip'",
        conn, parse_dates=["transaction_date"])
    conn.close()

    tx.sort_values(["investor_id","transaction_date"], inplace=True)
    tx["gap_days"] = tx.groupby("investor_id")["transaction_date"].diff().dt.days

    summary = (tx.groupby("investor_id")
                 .agg(
                     num_sips=("transaction_date","count"),
                     avg_gap_days=("gap_days","mean"),
                     max_gap_days=("gap_days","max"),
                 )
                 .dropna()
                 .query("num_sips >= 6")
                 .round(1)
                 .reset_index())

    summary["at_risk"] = summary["avg_gap_days"] > 35

    out = PROC_DIR / "sip_continuity.csv"
    summary.to_csv(out, index=False)
    return summary


def sector_hhi() -> pd.DataFrame:
    """
    Herfindahl-Hirschman Index of sector concentration per fund.
    HHI = sum(weight_i^2). Higher = more concentrated.
    """
    conn = sqlite3.connect(DB_PATH)
    ph   = pd.read_sql("SELECT amfi_code, sector, weight_pct FROM fact_portfolio", conn)
    fund = pd.read_sql("SELECT amfi_code, scheme_name FROM dim_fund", conn)
    conn.close()

    sector_weights = (ph.groupby(["amfi_code","sector"])["weight_pct"]
                        .sum()
                        .reset_index())

    hhi = (sector_weights.groupby("amfi_code")
                         .apply(lambda g: (g["weight_pct"]**2).sum() / 10000, include_groups=False)
                         .reset_index()
                         .rename(columns={0: "hhi"}))

    hhi = hhi.merge(fund, on="amfi_code")
    hhi["concentration"] = pd.cut(hhi["hhi"],
                                  bins=[0, 0.10, 0.18, 1.0],
                                  labels=["Diversified","Moderate","Concentrated"])
    hhi.sort_values("hhi", ascending=False, inplace=True)
    out = PROC_DIR / "sector_hhi.csv"
    hhi.to_csv(out, index=False)
    return hhi


if __name__ == "__main__":
    sep = "=" * 65
    print(sep)
    print("  BLUESTOCK FINTECH — Day 6: Recommender & Advanced Analytics")
    print(sep)

    print("\n── Fund Recommendations ────────────────────────────────────")
    for risk, horizon in [("Low","Short (< 1yr)"),
                           ("Moderate","Long (3yr+)"),
                           ("High","Long (3yr+)")]:
        print(f"\n  Risk: {risk}  |  Horizon: {horizon}")
        rec = recommend(risk, horizon, top_n=3)
        print(rec.to_string(index=False))

    print("\n── Cohort Analysis ─────────────────────────────────────────")
    cohort = cohort_analysis()
    print(cohort.to_string(index=False))
    cohort.to_csv(PROC_DIR / "cohort_analysis.csv", index=False)

    print("\n── SIP Continuity ──────────────────────────────────────────")
    sip = sip_continuity_analysis()
    at_risk = sip["at_risk"].sum()
    print(f"  Investors analysed : {len(sip)}")
    print(f"  At-risk (gap>35d)  : {at_risk} ({at_risk/len(sip)*100:.1f}%)")
    print(sip.head(5).to_string(index=False))

    print("\n── Sector HHI ──────────────────────────────────────────────")
    hhi = sector_hhi()
    print(hhi[["scheme_name","hhi","concentration"]].head(10).to_string(index=False))

    print(f"\n{sep}")
    print("  Day 6: Advanced Analytics Complete ✅")
    print(sep)
