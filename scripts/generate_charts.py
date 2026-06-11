"""
Bluestock Fintech — Day 3+4: generate_charts.py
Generate all 15+ EDA and performance charts as PNG files.
Run: python scripts/generate_charts.py
"""

import sqlite3, warnings
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

warnings.filterwarnings("ignore")

BASE_DIR   = Path(__file__).resolve().parent.parent
DB_PATH    = BASE_DIR / "data" / "db" / "bluestock_mf.db"
CHARTS_DIR = BASE_DIR / "reports" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# Brand colours
BLUE   = "#1565C0"
TEAL   = "#00897B"
ORANGE = "#F4511E"
GOLD   = "#F9A825"
LIGHT  = "#E3F2FD"
DARK   = "#0D1B2A"

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "#F8FAFC",
    "axes.grid":        True,
    "grid.color":       "#E0E0E0",
    "grid.linewidth":   0.6,
    "font.family":      "DejaVu Sans",
    "axes.spines.top":  False,
    "axes.spines.right":False,
})

def db():
    return sqlite3.connect(DB_PATH)

def save(fig, name):
    p = CHARTS_DIR / f"{name}.png"
    fig.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✅  {name}.png")


# ── C1: NAV Trends — 8 flagship schemes ─────────────────────
def chart_nav_trends():
    conn = db()
    nav  = pd.read_sql("SELECT amfi_code, date, nav FROM fact_nav", conn, parse_dates=["date"])
    fund = pd.read_sql("SELECT amfi_code, scheme_name FROM dim_fund WHERE plan='Direct'", conn)
    conn.close()

    codes = [125497,119552,120503,118632,119092,120841,148567,120845]
    sel   = nav[nav["amfi_code"].isin(codes)].merge(fund, on="amfi_code")

    fig, ax = plt.subplots(figsize=(14,6))
    palette = plt.cm.tab10.colors
    for i, (code, grp) in enumerate(sel.groupby("amfi_code")):
        name  = grp["scheme_name"].iloc[0].replace(" - Direct","").replace(" - Growth","")[:35]
        grp_s = grp.sort_values("date")
        # Normalise to 100 at start
        base  = grp_s["nav"].iloc[0]
        ax.plot(grp_s["date"], grp_s["nav"]/base*100,
                label=name, color=palette[i % 10], linewidth=1.6)

    ax.set_title("NAV Indexed to 100 — 8 Flagship Funds (Jan 2022 – May 2026)",
                 fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Date"); ax.set_ylabel("Indexed NAV (Base = 100)")
    ax.legend(fontsize=7.5, ncol=2, loc="upper left")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))
    save(fig, "01_nav_trends")


# ── C2: AUM Growth Grouped Bar ───────────────────────────────
def chart_aum_growth():
    conn = db()
    aum  = pd.read_sql("SELECT date, fund_house, aum_lakh_crore FROM fact_aum", conn, parse_dates=["date"])
    conn.close()

    pivot = aum.pivot_table(index="fund_house", columns=aum["date"].dt.year,
                            values="aum_lakh_crore", aggfunc="max")
    pivot.sort_values(pivot.columns[-1], ascending=False, inplace=True)

    fig, ax = plt.subplots(figsize=(14,6))
    x = np.arange(len(pivot))
    w = 0.2
    colors = [BLUE, TEAL, ORANGE, GOLD]
    for i, yr in enumerate(pivot.columns):
        ax.bar(x + i*w, pivot[yr], width=w, label=str(yr),
               color=colors[i % len(colors)], alpha=0.9)

    ax.set_xticks(x + w*1.5)
    ax.set_xticklabels(pivot.index, rotation=30, ha="right", fontsize=9)
    ax.set_title("AUM by Fund House — 2022 to 2025 (₹ Lakh Crore)",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("AUM (₹ Lakh Crore)")
    ax.legend(title="Year")
    save(fig, "02_aum_growth")


# ── C3: SIP Inflow Time-Series ───────────────────────────────
def chart_sip_inflows():
    conn = db()
    sip  = pd.read_sql("SELECT month, sip_inflow_crore, active_sip_accounts_crore FROM fact_sip_industry",
                        conn, parse_dates=["month"])
    conn.close()
    sip.sort_values("month", inplace=True)

    fig, ax1 = plt.subplots(figsize=(14,5))
    ax2 = ax1.twinx()

    ax1.fill_between(sip["month"], sip["sip_inflow_crore"],
                     alpha=0.25, color=BLUE)
    ax1.plot(sip["month"], sip["sip_inflow_crore"],
             color=BLUE, linewidth=2.2, label="SIP Inflow (₹ Cr)")
    ax2.plot(sip["month"], sip["active_sip_accounts_crore"],
             color=ORANGE, linewidth=2, linestyle="--", label="Active SIP Accounts (Cr)")

    # Mark all-time high
    peak_idx = sip["sip_inflow_crore"].idxmax()
    ax1.annotate(f"ATH ₹{sip.loc[peak_idx,'sip_inflow_crore']:,}Cr",
                 xy=(sip.loc[peak_idx,"month"], sip.loc[peak_idx,"sip_inflow_crore"]),
                 xytext=(-60, -30), textcoords="offset points",
                 arrowprops=dict(arrowstyle="->", color="red"),
                 fontsize=9, color="red", fontweight="bold")

    ax1.set_title("Monthly SIP Inflows & Active Accounts (Jan 2022 – Dec 2025)",
                  fontsize=14, fontweight="bold")
    ax1.set_ylabel("SIP Inflow (₹ Crore)", color=BLUE)
    ax2.set_ylabel("Active SIP Accounts (Crore)", color=ORANGE)
    lines = [plt.Line2D([0],[0],color=BLUE,lw=2, label="SIP Inflow"),
             plt.Line2D([0],[0],color=ORANGE,lw=2,ls="--",label="Active Accounts")]
    ax1.legend(handles=lines, loc="upper left")
    save(fig, "03_sip_inflows")


# ── C4: Category Inflow Heatmap ───────────────────────────────
def chart_category_heatmap():
    conn = db()
    ci   = pd.read_sql("SELECT month, category, net_inflow_crore FROM fact_category_inflows",
                        conn, parse_dates=["month"])
    conn.close()

    pivot = ci.pivot_table(index="category", columns=ci["month"].dt.strftime("%b %y"),
                           values="net_inflow_crore", aggfunc="sum")
    pivot.fillna(0, inplace=True)

    fig, ax = plt.subplots(figsize=(16,6))
    sns.heatmap(pivot, cmap="RdYlGn", center=0, linewidths=0.4,
                fmt=".0f", annot=True, annot_kws={"size":7},
                ax=ax, cbar_kws={"label":"Net Inflow (₹ Cr)"})
    ax.set_title("Category-wise Net Inflows — FY 2024-25 (₹ Crore)",
                 fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Month"); ax.set_ylabel("")
    plt.xticks(rotation=45, ha="right")
    save(fig, "04_category_heatmap")


# ── C5: Investor Age Group Demographics ──────────────────────
def chart_demographics():
    conn = db()
    tx   = pd.read_sql(
        "SELECT age_group, transaction_type, amount_inr FROM fact_transactions", conn)
    conn.close()

    fig, axes = plt.subplots(1, 2, figsize=(14,5))

    # Pie: age distribution
    age_counts = tx["age_group"].value_counts()
    axes[0].pie(age_counts, labels=age_counts.index, autopct="%1.1f%%",
                startangle=140, colors=sns.color_palette("Set2"))
    axes[0].set_title("Investor Age Group Distribution", fontweight="bold")

    # Box: SIP amount by age group
    sip = tx[tx["transaction_type"] == "Sip"].copy()
    order = ["18-25","26-35","36-45","46-55","56+"]
    sns.boxplot(data=sip, x="age_group", y="amount_inr",
                order=order, palette="Set2", ax=axes[1], fliersize=2)
    axes[1].set_title("SIP Amount Distribution by Age Group", fontweight="bold")
    axes[1].set_ylabel("SIP Amount (₹)")
    axes[1].set_xlabel("Age Group")
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"₹{x:,.0f}"))
    plt.tight_layout()
    save(fig, "05_demographics")


# ── C6: Geographic SIP Distribution ──────────────────────────
def chart_geo_distribution():
    conn = db()
    tx   = pd.read_sql(
        "SELECT state, city_tier, amount_inr FROM fact_transactions "
        "WHERE transaction_type='Sip'", conn)
    conn.close()

    state_agg = (tx.groupby("state")["amount_inr"]
                   .sum().sort_values(ascending=True) / 1e7)
    tier_agg  = tx.groupby("city_tier")["amount_inr"].sum()

    fig, axes = plt.subplots(1, 2, figsize=(14,5))

    axes[0].barh(state_agg.index, state_agg.values, color=BLUE, alpha=0.85)
    axes[0].set_title("Total SIP Amount by State (₹ Crore)", fontweight="bold")
    axes[0].set_xlabel("SIP Amount (₹ Crore)")
    for i, v in enumerate(state_agg.values):
        axes[0].text(v + 0.5, i, f"₹{v:.0f}Cr", va="center", fontsize=8)

    axes[1].pie(tier_agg, labels=tier_agg.index, autopct="%1.1f%%",
                colors=[BLUE, TEAL], startangle=90)
    axes[1].set_title("T30 vs B30 City Tier Split", fontweight="bold")
    plt.tight_layout()
    save(fig, "06_geo_distribution")


# ── C7: Folio Count Growth ────────────────────────────────────
def chart_folio_growth():
    conn = db()
    fc   = pd.read_sql("SELECT * FROM fact_folio_count", conn, parse_dates=["month"])
    conn.close()
    fc.sort_values("month", inplace=True)

    fig, ax = plt.subplots(figsize=(12,5))
    ax.stackplot(fc["month"],
                 fc["equity_folios_crore"],
                 fc["debt_folios_crore"],
                 fc["hybrid_folios_crore"],
                 fc["others_folios_crore"],
                 labels=["Equity","Debt","Hybrid","Others"],
                 colors=[BLUE, ORANGE, TEAL, GOLD], alpha=0.85)
    ax.set_title("Industry Folio Count Growth by Type (Jan 2022 – Dec 2025)",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Folios (Crore)")
    ax.legend(loc="upper left")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0fCr"))

    # Annotate start and end
    ax.annotate(f"{fc['total_folios_crore'].iloc[0]:.2f}Cr",
                xy=(fc["month"].iloc[0], fc["total_folios_crore"].iloc[0]),
                xytext=(15,10), textcoords="offset points", fontsize=9, color=DARK)
    ax.annotate(f"{fc['total_folios_crore'].iloc[-1]:.2f}Cr",
                xy=(fc["month"].iloc[-1], fc["total_folios_crore"].iloc[-1]),
                xytext=(-60,10), textcoords="offset points", fontsize=9,
                color=DARK, fontweight="bold")
    save(fig, "07_folio_growth")


# ── C8: Correlation Matrix of NAV Returns ────────────────────
def chart_correlation():
    conn = db()
    nav  = pd.read_sql(
        "SELECT amfi_code, date, daily_return_pct FROM fact_nav "
        "WHERE amfi_code IN (119551,125497,120503,118632,119092,"
        "                    120841,148567,120845,122639,119597)", conn)
    fund = pd.read_sql("SELECT amfi_code, scheme_name FROM dim_fund", conn)
    conn.close()

    wide = nav.pivot(index="date", columns="amfi_code", values="daily_return_pct")
    wide.columns = [fund.set_index("amfi_code").loc[c,"scheme_name"]
                        .split(" - ")[0][:20] for c in wide.columns]
    corr = wide.corr()

    fig, ax = plt.subplots(figsize=(11,9))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="coolwarm",
                center=0, linewidths=0.5, ax=ax,
                annot_kws={"size":8})
    ax.set_title("Pairwise Return Correlation — 10 Selected Funds",
                 fontsize=13, fontweight="bold", pad=12)
    plt.xticks(rotation=35, ha="right", fontsize=8)
    plt.yticks(fontsize=8)
    save(fig, "08_correlation_matrix")


# ── C9: Sector Allocation Donut ───────────────────────────────
def chart_sector_allocation():
    conn = db()
    ph   = pd.read_sql("SELECT sector, weight_pct FROM fact_portfolio", conn)
    conn.close()

    sector_wt = ph.groupby("sector")["weight_pct"].sum().sort_values(ascending=False)
    top8  = sector_wt.head(8)
    other = sector_wt.iloc[8:].sum()
    data  = pd.concat([top8, pd.Series({"Other": other})])

    fig, ax = plt.subplots(figsize=(9,7))
    wedges, texts, autotexts = ax.pie(
        data, labels=data.index, autopct="%1.1f%%",
        startangle=140, pctdistance=0.8,
        colors=sns.color_palette("tab10"),
        wedgeprops=dict(width=0.55))
    for t in autotexts:
        t.set_fontsize(8)
    ax.set_title("Sector Allocation Across All Equity Fund Portfolios",
                 fontsize=13, fontweight="bold")
    save(fig, "09_sector_allocation")


# ── C10: Risk-Return Scatter (Bubble) ────────────────────────
def chart_risk_return():
    conn = db()
    perf = pd.read_sql("SELECT * FROM fact_performance", conn)
    conn.close()

    fig, ax = plt.subplots(figsize=(12,7))
    cats    = perf["category"].unique()
    palette = dict(zip(cats, sns.color_palette("Set1", len(cats))))

    for cat, grp in perf.groupby("category"):
        sc = ax.scatter(grp["std_dev_ann_pct"], grp["return_3yr_pct"],
                        s=grp["aum_crore"] / 500,
                        c=[palette[cat]] * len(grp),
                        alpha=0.7, label=cat, edgecolors="white", linewidth=0.5)

    ax.set_xlabel("Risk — Annualised Std Dev (%)", fontsize=11)
    ax.set_ylabel("3-Year CAGR (%)", fontsize=11)
    ax.set_title("Risk vs Return Scatter (Bubble size = AUM)",
                 fontsize=14, fontweight="bold")
    ax.legend(title="Category")

    # Label top 5 by sharpe
    top5 = perf.nlargest(5, "sharpe_ratio")
    for _, row in top5.iterrows():
        ax.annotate(row["scheme_name"].split(" - ")[0][:22],
                    xy=(row["std_dev_ann_pct"], row["return_3yr_pct"]),
                    xytext=(5, 5), textcoords="offset points", fontsize=7)
    save(fig, "10_risk_return_scatter")


# ── C11: Fund Scorecard Bar ───────────────────────────────────
def chart_scorecard():
    metrics_path = BASE_DIR / "data" / "processed" / "computed_metrics.csv"
    if not metrics_path.exists():
        print("  ⚠  computed_metrics.csv not found — run compute_metrics.py first")
        return
    m = pd.read_csv(metrics_path).head(15)
    labels = m["scheme_name"].str.split(" - ").str[0].str[:28]

    fig, ax = plt.subplots(figsize=(12,7))
    bars = ax.barh(labels[::-1], m["composite_score"][::-1],
                   color=[BLUE if s >= 70 else TEAL if s >= 55 else ORANGE
                          for s in m["composite_score"][::-1]],
                   alpha=0.9)
    ax.set_xlabel("Composite Score (0–100)")
    ax.set_title("Fund Scorecard — Top 15 by Composite Score",
                 fontsize=14, fontweight="bold")
    ax.axvline(70, color="red", linestyle="--", linewidth=1, label="Score = 70")
    ax.legend()
    for bar, val in zip(bars, m["composite_score"][::-1]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f"{val:.0f}", va="center", fontsize=8)
    save(fig, "11_fund_scorecard")


# ── C12: Rolling Sharpe (5 funds) ────────────────────────────
def chart_rolling_sharpe():
    conn = db()
    nav  = pd.read_sql(
        "SELECT amfi_code, date, daily_return_pct FROM fact_nav "
        "WHERE amfi_code IN (119551,125497,120503,148567,119092)",
        conn, parse_dates=["date"])
    fund = pd.read_sql("SELECT amfi_code, scheme_name FROM dim_fund", conn)
    conn.close()

    RF_D = 0.065 / 252
    fig, ax = plt.subplots(figsize=(14,5))
    palette = plt.cm.tab10.colors
    for i, (code, grp) in enumerate(nav.groupby("amfi_code")):
        grp = grp.sort_values("date").set_index("date")["daily_return_pct"]
        roll_sharpe = (grp.rolling(90).mean() - RF_D) / grp.rolling(90).std() * np.sqrt(252)
        name = fund.set_index("amfi_code").loc[code,"scheme_name"].split(" - ")[0][:25]
        ax.plot(roll_sharpe.index, roll_sharpe, label=name,
                color=palette[i], linewidth=1.6)

    ax.axhline(1, color="red", linestyle="--", linewidth=1, label="Sharpe = 1")
    ax.axhline(0, color="grey", linestyle="-", linewidth=0.7)
    ax.set_title("Rolling 90-Day Sharpe Ratio — 5 Key Funds",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Rolling Sharpe Ratio")
    ax.legend(fontsize=8)
    save(fig, "12_rolling_sharpe")


# ── C13: Benchmark vs Fund (Top 3 vs Nifty50 + Nifty100) ────
def chart_benchmark_comparison():
    conn = db()
    nav   = pd.read_sql(
        "SELECT amfi_code, date, nav FROM fact_nav "
        "WHERE amfi_code IN (119551,125497,120503)",
        conn, parse_dates=["date"])
    bench = pd.read_sql(
        "SELECT date, index_name, close_value FROM fact_benchmarks "
        "WHERE index_name IN ('NIFTY50','NIFTY100')",
        conn, parse_dates=["date"])
    fund  = pd.read_sql("SELECT amfi_code, scheme_name FROM dim_fund", conn)
    conn.close()

    fig, ax = plt.subplots(figsize=(14,6))
    palette = plt.cm.tab10.colors

    for i, (code, grp) in enumerate(nav.groupby("amfi_code")):
        grp  = grp.sort_values("date")
        norm = grp["nav"] / grp["nav"].iloc[0] * 100
        name = fund.set_index("amfi_code").loc[code,"scheme_name"].split(" - ")[0][:25]
        ax.plot(grp["date"], norm, label=name, color=palette[i], linewidth=2)

    for i, (idx, grp) in enumerate(bench.groupby("index_name")):
        grp  = grp.sort_values("date")
        norm = grp["close_value"] / grp["close_value"].iloc[0] * 100
        ax.plot(grp["date"], norm, label=idx,
                linestyle="--", linewidth=1.8, color=palette[i+3])

    ax.set_title("Fund Returns vs Benchmark Indices (Indexed to 100, Jan 2022)",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Indexed Return (Base = 100)")
    ax.legend(fontsize=9)
    save(fig, "13_benchmark_comparison")


# ── C14: Max Drawdown per Fund ────────────────────────────────
def chart_max_drawdown():
    conn = db()
    perf = pd.read_sql(
        "SELECT scheme_name, max_drawdown_pct, category FROM fact_performance "
        "WHERE category NOT IN ('Debt')", conn)
    conn.close()
    perf.sort_values("max_drawdown_pct", inplace=True)
    labels = perf["scheme_name"].str.split(" - ").str[0].str[:30]

    fig, ax = plt.subplots(figsize=(12,10))
    colors = [ORANGE if v < -20 else TEAL for v in perf["max_drawdown_pct"]]
    ax.barh(labels, perf["max_drawdown_pct"], color=colors, alpha=0.85)
    ax.axvline(-20, color="red", linestyle="--", linewidth=1.2, label="-20% threshold")
    ax.set_xlabel("Maximum Drawdown (%)")
    ax.set_title("Maximum Drawdown by Equity Fund (Peak-to-Trough)",
                 fontsize=14, fontweight="bold")
    ax.legend()
    save(fig, "14_max_drawdown")


# ── C15: Monthly Transaction Volume ──────────────────────────
def chart_transaction_volume():
    conn = db()
    tx   = pd.read_sql(
        "SELECT transaction_date, transaction_type, amount_inr FROM fact_transactions",
        conn, parse_dates=["transaction_date"])
    conn.close()

    tx["month"] = tx["transaction_date"].dt.to_period("M").dt.to_timestamp()
    monthly = (tx.groupby(["month","transaction_type"])["amount_inr"]
                 .sum().reset_index())
    monthly["amount_cr"] = monthly["amount_inr"] / 1e7

    fig, ax = plt.subplots(figsize=(14,5))
    for txtype, grp in monthly.groupby("transaction_type"):
        ax.plot(grp["month"], grp["amount_cr"], marker="o", markersize=3,
                label=txtype, linewidth=1.8)
    ax.set_title("Monthly Transaction Volume by Type (₹ Crore)",
                 fontsize=14, fontweight="bold")
    ax.set_ylabel("Amount (₹ Crore)")
    ax.legend()
    save(fig, "15_transaction_volume")


if __name__ == "__main__":
    sep = "=" * 65
    print(sep)
    print("  BLUESTOCK FINTECH — Generating All Charts")
    print(sep)
    chart_nav_trends()
    chart_aum_growth()
    chart_sip_inflows()
    chart_category_heatmap()
    chart_demographics()
    chart_geo_distribution()
    chart_folio_growth()
    chart_correlation()
    chart_sector_allocation()
    chart_risk_return()
    chart_scorecard()
    chart_rolling_sharpe()
    chart_benchmark_comparison()
    chart_max_drawdown()
    chart_transaction_volume()
    print(f"\n  All charts saved → {CHARTS_DIR}")
    print(sep)
