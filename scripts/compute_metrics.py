"""
Bluestock Fintech — Day 4: compute_metrics.py
Compute CAGR, Sharpe, Sortino, Alpha, Beta, MaxDrawdown, VaR, CVaR.
Run: python scripts/compute_metrics.py
"""

from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
from scipy import stats

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / "data" / "db" / "bluestock_mf.db"
PROC_DIR = BASE_DIR / "data" / "processed"

RF_DAILY = 0.065 / 252   # Risk-free rate: 6.5% annualised → daily


def load_data():
    conn = sqlite3.connect(DB_PATH)
    nav  = pd.read_sql("SELECT amfi_code, date, nav, daily_return_pct FROM fact_nav", conn, parse_dates=["date"])
    fund = pd.read_sql("SELECT amfi_code, scheme_name, fund_house, category, sub_category, plan, benchmark FROM dim_fund", conn)
    bench= pd.read_sql("SELECT date, index_name, close_value, daily_return_pct FROM fact_benchmarks", conn, parse_dates=["date"])
    conn.close()
    return nav, fund, bench


def compute_cagr(series: pd.Series, n_days: int) -> float:
    """CAGR using actual trading day count (not calendar days)."""
    if len(series) < 2 or series.iloc[0] <= 0:
        return np.nan
    return (series.iloc[-1] / series.iloc[0]) ** (252 / n_days) - 1


def compute_sharpe(returns: pd.Series) -> float:
    excess = returns - RF_DAILY
    std    = returns.std()
    if std == 0 or np.isnan(std):
        return np.nan
    return (excess.mean() / std) * np.sqrt(252)


def compute_sortino(returns: pd.Series) -> float:
    excess   = returns - RF_DAILY
    neg      = returns[returns < 0]
    down_std = neg.std()
    if down_std == 0 or np.isnan(down_std):
        return np.nan
    return (excess.mean() / down_std) * np.sqrt(252)


def compute_max_drawdown(nav_series: pd.Series) -> float:
    roll_max = nav_series.cummax()
    dd       = (nav_series - roll_max) / roll_max
    return float(dd.min())


def compute_alpha_beta(fund_ret: pd.Series, bench_ret: pd.Series):
    merged = pd.DataFrame({"f": fund_ret, "b": bench_ret}).dropna()
    if len(merged) < 30:
        return np.nan, np.nan
    slope, intercept, *_ = stats.linregress(merged["b"], merged["f"])
    alpha = intercept * 252   # Annualise
    beta  = slope
    return round(alpha, 4), round(beta, 4)


def compute_var_cvar(returns: pd.Series, confidence=0.95):
    clean = returns.dropna()
    if len(clean) < 30:
        return np.nan, np.nan
    var  = float(np.percentile(clean, (1 - confidence) * 100))
    cvar = float(clean[clean <= var].mean())
    return round(var, 6), round(cvar, 6)


def run_metrics():
    sep = "=" * 65
    print(sep)
    print("  BLUESTOCK FINTECH — Day 4: Performance Metrics")
    print(sep)

    nav, fund, bench = load_data()

    # Nifty 100 as primary benchmark
    nifty100 = (bench[bench["index_name"] == "NIFTY100"]
                .set_index("date")["daily_return_pct"]
                .sort_index())

    cutoff_1yr = nav["date"].max() - pd.DateOffset(years=1)
    cutoff_3yr = nav["date"].max() - pd.DateOffset(years=3)

    results = []

    for code, grp in nav.groupby("amfi_code"):
        grp = grp.sort_values("date").set_index("date")
        returns = grp["daily_return_pct"].dropna()

        if len(returns) < 50:
            continue

        # Returns for different windows
        ret_1yr = returns[returns.index >= cutoff_1yr]
        ret_3yr = returns[returns.index >= cutoff_3yr]

        # NAV series
        nav_full = grp["nav"]
        nav_1yr  = nav_full[nav_full.index >= cutoff_1yr]
        nav_3yr  = nav_full[nav_full.index >= cutoff_3yr]

        # Alpha & Beta (3yr window vs Nifty 100)
        bench_3yr = nifty100[nifty100.index >= cutoff_3yr]
        alpha, beta = compute_alpha_beta(ret_3yr, bench_3yr)

        # VaR / CVaR
        var_95, cvar_95 = compute_var_cvar(returns)

        results.append({
            "amfi_code":        code,
            "cagr_1yr":         round(compute_cagr(nav_1yr, len(ret_1yr)) * 100, 2),
            "cagr_3yr":         round(compute_cagr(nav_3yr, len(ret_3yr)) * 100, 2),
            "cagr_full":        round(compute_cagr(nav_full, len(returns)) * 100, 2),
            "sharpe_ratio":     round(compute_sharpe(returns), 4),
            "sortino_ratio":    round(compute_sortino(returns), 4),
            "alpha":            alpha,
            "beta":             beta,
            "max_drawdown_pct": round(compute_max_drawdown(nav_full) * 100, 2),
            "std_dev_ann_pct":  round(returns.std() * np.sqrt(252) * 100, 2),
            "var_95_daily":     round(var_95 * 100, 4),
            "cvar_95_daily":    round(cvar_95 * 100, 4),
            "n_trading_days":   len(returns),
        })

    metrics = pd.DataFrame(results)
    metrics = metrics.merge(fund[["amfi_code","scheme_name","fund_house",
                                  "category","sub_category","plan"]], on="amfi_code")

    # ── Fund Scorecard (composite 0-100) ────────────────────
    # Rank each metric (higher = better rank, except drawdown/std)
    metrics["rank_3yr"]    = metrics["cagr_3yr"].rank(pct=True) * 100
    metrics["rank_sharpe"] = metrics["sharpe_ratio"].rank(pct=True) * 100
    metrics["rank_alpha"]  = metrics["alpha"].rank(pct=True) * 100
    metrics["rank_dd"]     = metrics["max_drawdown_pct"].rank(ascending=False, pct=True) * 100
    metrics["rank_std"]    = metrics["std_dev_ann_pct"].rank(ascending=False, pct=True) * 100

    metrics["composite_score"] = (
        0.30 * metrics["rank_3yr"]    +
        0.25 * metrics["rank_sharpe"] +
        0.20 * metrics["rank_alpha"]  +
        0.15 * metrics["rank_dd"]     +
        0.10 * metrics["rank_std"]
    ).round(1)

    metrics.sort_values("composite_score", ascending=False, inplace=True)
    metrics.reset_index(drop=True, inplace=True)
    metrics.index += 1   # Rank starts at 1

    # Save
    out = PROC_DIR / "computed_metrics.csv"
    metrics.to_csv(out, index_label="rank")
    print(f"\n  Metrics computed for {len(metrics)} funds")
    print(f"  Saved → {out.name}")

    print("\n  Top 10 by Composite Score:")
    cols = ["scheme_name","category","plan","cagr_3yr","sharpe_ratio",
            "alpha","max_drawdown_pct","composite_score"]
    print(metrics[cols].head(10).to_string())

    print(f"\n{sep}")
    print("  Day 4: Metrics Complete ✅")
    print(sep)
    return metrics


if __name__ == "__main__":
    run_metrics()
