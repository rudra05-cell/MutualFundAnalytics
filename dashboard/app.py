"""
Bluestock Fintech — Mutual Fund Analytics Platform
Streamlit Dashboard (Bonus B2)
Run: streamlit run dashboard/app.py
"""

import sqlite3, sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / "data" / "db" / "bluestock_mf.db"

try:
    import streamlit as st
except ImportError:
    print("Install streamlit: pip install streamlit")
    sys.exit(1)

st.set_page_config(
    page_title="Bluestock MF Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
  .metric-card {
    background: linear-gradient(135deg, #1565C0, #00897B);
    padding: 18px 22px; border-radius: 12px; color: white;
    text-align: center; margin: 4px;
  }
  .metric-card h2 { font-size: 2rem; margin: 0; }
  .metric-card p  { margin: 0; opacity: 0.85; font-size: 0.9rem; }
  .section-title  { color: #1565C0; border-bottom: 2px solid #1565C0;
                    padding-bottom: 4px; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_all():
    conn = sqlite3.connect(DB_PATH)
    data = {
        "fund":       pd.read_sql("SELECT * FROM dim_fund", conn),
        "perf":       pd.read_sql("SELECT * FROM fact_performance", conn),
        "nav":        pd.read_sql("SELECT * FROM fact_nav", conn, parse_dates=["date"]),
        "sip":        pd.read_sql("SELECT * FROM fact_sip_industry", conn, parse_dates=["month"]),
        "aum":        pd.read_sql("SELECT * FROM fact_aum", conn, parse_dates=["date"]),
        "tx":         pd.read_sql("SELECT * FROM fact_transactions", conn, parse_dates=["transaction_date"]),
        "folio":      pd.read_sql("SELECT * FROM fact_folio_count", conn, parse_dates=["month"]),
        "cat":        pd.read_sql("SELECT * FROM fact_category_inflows", conn, parse_dates=["month"]),
        "bench":      pd.read_sql("SELECT * FROM fact_benchmarks", conn, parse_dates=["date"]),
        "portfolio":  pd.read_sql("SELECT * FROM fact_portfolio", conn),
    }
    conn.close()
    return data


def metric_card(label, value, delta=None):
    delta_html = f"<small style='color:#80CBC4'>{delta}</small>" if delta else ""
    st.markdown(f"""
    <div class="metric-card">
      <h2>{value}</h2>
      <p>{label}</p>
      {delta_html}
    </div>""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/fluency/96/fund-accounting.png", width=60)
st.sidebar.title("🏦 Bluestock MF Analytics")
st.sidebar.markdown("**Capstone Project 2026**")

page = st.sidebar.radio(
    "Navigate",
    ["🏠 Industry Overview",
     "📈 Fund Performance",
     "👥 Investor Analytics",
     "📊 SIP & Market Trends"],
)

d = load_all()

# ════════════════════════════════════════════════════════════
# PAGE 1 — INDUSTRY OVERVIEW
# ════════════════════════════════════════════════════════════
if page == "🏠 Industry Overview":
    st.title("🏠 Industry Overview")
    st.markdown("**India's Mutual Fund Industry — Key Metrics as of December 2025**")

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Industry AUM", "₹81 Lakh Cr", "All-time high")
    with c2: metric_card("Monthly SIP Inflow", "₹31,002 Cr", "Dec 2025 ATH")
    with c3: metric_card("Total Folios", "26.12 Crore", "+97% since 2022")
    with c4: metric_card("Active SIP Accounts", "9.35 Crore", "9.35Cr accounts")

    st.divider()
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<p class="section-title">AUM Growth by Fund House (2022–2025)</p>',
                    unsafe_allow_html=True)
        pivot = (d["aum"].pivot_table(index="fund_house", columns=d["aum"]["date"].dt.year,
                                      values="aum_lakh_crore", aggfunc="max")
                         .sort_values(d["aum"]["date"].dt.year.max(), ascending=False))
        fig, ax = plt.subplots(figsize=(10, 5))
        x = np.arange(len(pivot)); w = 0.2
        colors = ["#1565C0","#00897B","#F4511E","#F9A825"]
        for i, yr in enumerate(pivot.columns):
            ax.bar(x + i*w, pivot[yr], width=w, label=str(yr), color=colors[i % 4], alpha=0.9)
        ax.set_xticks(x + w*1.5)
        ax.set_xticklabels(pivot.index, rotation=30, ha="right", fontsize=8)
        ax.set_ylabel("AUM (₹ Lakh Crore)"); ax.legend(title="Year")
        ax.set_facecolor("#F8FAFC"); ax.grid(axis="y", color="#E0E0E0")
        for spine in ["top","right"]: ax.spines[spine].set_visible(False)
        st.pyplot(fig); plt.close()

    with col2:
        st.markdown('<p class="section-title">Folio Count by Type (Latest)</p>',
                    unsafe_allow_html=True)
        latest = d["folio"].sort_values("month").iloc[-1]
        labels = ["Equity","Debt","Hybrid","Others"]
        vals   = [latest["equity_folios_crore"], latest["debt_folios_crore"],
                  latest["hybrid_folios_crore"], latest["others_folios_crore"]]
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(vals, labels=labels, autopct="%1.1f%%",
               colors=["#1565C0","#F4511E","#00897B","#F9A825"],
               startangle=140, wedgeprops=dict(width=0.55))
        ax.set_title(f"Total: {latest['total_folios_crore']:.2f} Crore", fontsize=10)
        st.pyplot(fig); plt.close()

    st.markdown('<p class="section-title">Folio Count Growth (2022–2025)</p>',
                unsafe_allow_html=True)
    fig, ax = plt.subplots(figsize=(14, 3.5))
    d["folio"].sort_values("month", inplace=True)
    ax.fill_between(d["folio"]["month"], d["folio"]["total_folios_crore"],
                    alpha=0.2, color="#1565C0")
    ax.plot(d["folio"]["month"], d["folio"]["total_folios_crore"],
            color="#1565C0", linewidth=2.5)
    ax.set_ylabel("Total Folios (Crore)"); ax.set_facecolor("#F8FAFC")
    for spine in ["top","right"]: ax.spines[spine].set_visible(False)
    st.pyplot(fig); plt.close()


# ════════════════════════════════════════════════════════════
# PAGE 2 — FUND PERFORMANCE
# ════════════════════════════════════════════════════════════
elif page == "📈 Fund Performance":
    st.title("📈 Fund Performance Analytics")

    # Sidebar filters
    st.sidebar.markdown("---")
    fund_houses = ["All"] + sorted(d["perf"]["fund_house"].unique().tolist())
    categories  = ["All"] + sorted(d["perf"]["category"].unique().tolist())
    sel_fh  = st.sidebar.selectbox("Fund House", fund_houses)
    sel_cat = st.sidebar.selectbox("Category", categories)
    sel_plan= st.sidebar.selectbox("Plan", ["All","Regular","Direct"])

    perf = d["perf"].copy()
    if sel_fh   != "All": perf = perf[perf["fund_house"] == sel_fh]
    if sel_cat  != "All": perf = perf[perf["category"] == sel_cat]
    if sel_plan != "All": perf = perf[perf["plan"] == sel_plan]

    st.markdown(f"**Showing {len(perf)} funds**")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-title">Risk vs Return Scatter</p>',
                    unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(7, 5))
        cats = perf["category"].unique()
        pal  = dict(zip(cats, sns.color_palette("Set1", len(cats))))
        for cat, grp in perf.groupby("category"):
            ax.scatter(grp["std_dev_ann_pct"], grp["return_3yr_pct"],
                       s=grp["aum_crore"]/500, c=[pal[cat]]*len(grp),
                       alpha=0.75, label=cat, edgecolors="white")
        ax.set_xlabel("Std Dev (%)"); ax.set_ylabel("3yr CAGR (%)")
        ax.legend(fontsize=8); ax.set_facecolor("#F8FAFC")
        for spine in ["top","right"]: ax.spines[spine].set_visible(False)
        st.pyplot(fig); plt.close()

    with col2:
        st.markdown('<p class="section-title">Top 10 by Sharpe Ratio</p>',
                    unsafe_allow_html=True)
        top10 = perf.nlargest(10, "sharpe_ratio")
        labels= top10["scheme_name"].str.split(" - ").str[0].str[:25]
        fig, ax = plt.subplots(figsize=(7,5))
        ax.barh(labels[::-1], top10["sharpe_ratio"][::-1], color="#1565C0", alpha=0.85)
        ax.axvline(1, color="red", linestyle="--", linewidth=1)
        ax.set_xlabel("Sharpe Ratio"); ax.set_facecolor("#F8FAFC")
        for spine in ["top","right"]: ax.spines[spine].set_visible(False)
        st.pyplot(fig); plt.close()

    st.markdown('<p class="section-title">Fund Scorecard Table</p>',
                unsafe_allow_html=True)
    cols = ["scheme_name","fund_house","category","plan",
            "return_1yr_pct","return_3yr_pct","return_5yr_pct",
            "sharpe_ratio","alpha","max_drawdown_pct","expense_ratio_pct","morningstar_rating"]
    st.dataframe(
        perf[cols].sort_values("sharpe_ratio", ascending=False).reset_index(drop=True),
        use_container_width=True,
        height=350,
    )

    st.markdown('<p class="section-title">NAV History — Select a Fund</p>',
                unsafe_allow_html=True)
    fund_options = d["fund"].set_index("amfi_code")["scheme_name"].to_dict()
    sel_code = st.selectbox("Fund", options=list(fund_options.keys()),
                            format_func=lambda x: fund_options[x])
    nav_sel = d["nav"][d["nav"]["amfi_code"] == sel_code].sort_values("date")
    bench_sel = d["bench"][d["bench"]["index_name"] == "NIFTY100"].sort_values("date")

    fig, ax = plt.subplots(figsize=(12, 4))
    ax2 = ax.twinx()
    ax.plot(nav_sel["date"], nav_sel["nav"], color="#1565C0", linewidth=2, label="NAV")
    ax2.plot(bench_sel["date"], bench_sel["close_value"],
             color="#F4511E", linewidth=1.5, linestyle="--", label="Nifty100")
    ax.set_ylabel("NAV (₹)", color="#1565C0")
    ax2.set_ylabel("Nifty 100", color="#F4511E")
    ax.set_title(fund_options[sel_code])
    ax.set_facecolor("#F8FAFC")
    for spine in ["top","right"]: ax.spines[spine].set_visible(False)
    st.pyplot(fig); plt.close()


# ════════════════════════════════════════════════════════════
# PAGE 3 — INVESTOR ANALYTICS
# ════════════════════════════════════════════════════════════
elif page == "👥 Investor Analytics":
    st.title("👥 Investor Analytics")

    st.sidebar.markdown("---")
    states = ["All"] + sorted(d["tx"]["state"].unique().tolist())
    ages   = ["All"] + sorted(d["tx"]["age_group"].unique().tolist())
    sel_state = st.sidebar.selectbox("State", states)
    sel_age   = st.sidebar.selectbox("Age Group", ages)
    sel_tier  = st.sidebar.selectbox("City Tier", ["All","T30","B30"])

    tx = d["tx"].copy()
    if sel_state != "All": tx = tx[tx["state"] == sel_state]
    if sel_age   != "All": tx = tx[tx["age_group"] == sel_age]
    if sel_tier  != "All": tx = tx[tx["city_tier"] == sel_tier]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Transactions", f"{len(tx):,}")
    c2.metric("Total Amount", f"₹{tx['amount_inr'].sum()/1e7:.0f} Cr")
    c3.metric("Unique Investors", f"{tx['investor_id'].nunique():,}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-title">Transaction Amount by State</p>',
                    unsafe_allow_html=True)
        state_agg = (tx.groupby("state")["amount_inr"]
                       .sum().sort_values() / 1e7)
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.barh(state_agg.index, state_agg.values, color="#00897B", alpha=0.85)
        ax.set_xlabel("Amount (₹ Crore)")
        ax.set_facecolor("#F8FAFC")
        for spine in ["top","right"]: ax.spines[spine].set_visible(False)
        st.pyplot(fig); plt.close()

    with col2:
        st.markdown('<p class="section-title">SIP / Lumpsum / Redemption Split</p>',
                    unsafe_allow_html=True)
        type_agg = tx.groupby("transaction_type")["amount_inr"].sum()
        fig, ax  = plt.subplots(figsize=(5.5, 5))
        ax.pie(type_agg, labels=type_agg.index, autopct="%1.1f%%",
               colors=["#1565C0","#00897B","#F4511E"], startangle=90)
        st.pyplot(fig); plt.close()

    st.markdown('<p class="section-title">Average SIP by Age Group</p>',
                unsafe_allow_html=True)
    sip_age = (tx[tx["transaction_type"]=="Sip"]
                 .groupby("age_group")["amount_inr"]
                 .mean()
                 .reindex(["18-25","26-35","36-45","46-55","56+"]))
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.bar(sip_age.index, sip_age.values, color="#1565C0", alpha=0.85)
    ax.set_ylabel("Avg SIP Amount (₹)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"₹{x:,.0f}"))
    ax.set_facecolor("#F8FAFC")
    for spine in ["top","right"]: ax.spines[spine].set_visible(False)
    st.pyplot(fig); plt.close()

    st.markdown('<p class="section-title">Monthly Transaction Volume</p>',
                unsafe_allow_html=True)
    tx["month"] = tx["transaction_date"].dt.to_period("M").dt.to_timestamp()
    monthly = tx.groupby(["month","transaction_type"])["amount_inr"].sum().reset_index()
    monthly["cr"] = monthly["amount_inr"] / 1e7
    fig, ax = plt.subplots(figsize=(12, 3))
    for ttype, grp in monthly.groupby("transaction_type"):
        ax.plot(grp["month"], grp["cr"], label=ttype, linewidth=1.8, marker="o", markersize=3)
    ax.set_ylabel("₹ Crore"); ax.legend(); ax.set_facecolor("#F8FAFC")
    for spine in ["top","right"]: ax.spines[spine].set_visible(False)
    st.pyplot(fig); plt.close()


# ════════════════════════════════════════════════════════════
# PAGE 4 — SIP & MARKET TRENDS
# ════════════════════════════════════════════════════════════
elif page == "📊 SIP & Market Trends":
    st.title("📊 SIP & Market Trends")

    sip   = d["sip"].sort_values("month")
    bench = d["bench"][d["bench"]["index_name"] == "NIFTY50"].sort_values("date")

    st.markdown('<p class="section-title">SIP Inflow (Bar) vs Nifty 50 (Line) — Dual Axis</p>',
                unsafe_allow_html=True)
    fig, ax1 = plt.subplots(figsize=(14, 4))
    ax2 = ax1.twinx()
    ax1.bar(sip["month"], sip["sip_inflow_crore"],
            color="#1565C0", alpha=0.7, width=20, label="SIP Inflow (₹ Cr)")
    ax2.plot(bench["date"], bench["close_value"],
             color="#F4511E", linewidth=2, label="Nifty 50")
    ax1.set_ylabel("SIP Inflow (₹ Crore)", color="#1565C0")
    ax2.set_ylabel("Nifty 50 Index", color="#F4511E")
    lines1, l1 = ax1.get_legend_handles_labels()
    lines2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, l1 + l2, loc="upper left")
    ax1.set_facecolor("#F8FAFC")
    for spine in ["top","right"]: ax1.spines[spine].set_visible(False)
    st.pyplot(fig); plt.close()

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<p class="section-title">Category Inflows Heatmap</p>',
                    unsafe_allow_html=True)
        ci = d["cat"].copy()
        pivot = ci.pivot_table(index="category", columns=ci["month"].dt.strftime("%b %y"),
                               values="net_inflow_crore", aggfunc="sum").fillna(0)
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.heatmap(pivot, cmap="RdYlGn", center=0, linewidths=0.4,
                    annot=True, fmt=".0f", annot_kws={"size": 6},
                    ax=ax, cbar_kws={"label": "Net Inflow (₹ Cr)"})
        ax.set_xlabel(""); ax.set_ylabel("")
        plt.xticks(rotation=45, ha="right", fontsize=7)
        plt.yticks(fontsize=8)
        st.pyplot(fig); plt.close()

    with col2:
        st.markdown('<p class="section-title">Top 5 Categories by Net Inflow FY25</p>',
                    unsafe_allow_html=True)
        top5 = (d["cat"].groupby("category")["net_inflow_crore"]
                        .sum().nlargest(5).sort_values())
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.barh(top5.index, top5.values, color="#1565C0", alpha=0.85)
        ax.set_xlabel("Net Inflow (₹ Crore)")
        ax.set_facecolor("#F8FAFC")
        for spine in ["top","right"]: ax.spines[spine].set_visible(False)
        st.pyplot(fig); plt.close()

    st.markdown('<p class="section-title">SIP Active Accounts & AUM Growth</p>',
                unsafe_allow_html=True)
    fig, ax1 = plt.subplots(figsize=(12, 3))
    ax2 = ax1.twinx()
    ax1.plot(sip["month"], sip["active_sip_accounts_crore"],
             color="#00897B", linewidth=2.2, label="Active Accounts (Cr)")
    ax2.plot(sip["month"], sip["sip_aum_lakh_crore"],
             color="#F9A825", linewidth=2, linestyle="--", label="SIP AUM (₹ Lakh Cr)")
    ax1.set_ylabel("Active SIP Accounts (Crore)", color="#00897B")
    ax2.set_ylabel("SIP AUM (₹ Lakh Crore)", color="#F9A825")
    lines1, l1 = ax1.get_legend_handles_labels()
    lines2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, l1 + l2)
    ax1.set_facecolor("#F8FAFC")
    for spine in ["top","right"]: ax1.spines[spine].set_visible(False)
    st.pyplot(fig); plt.close()

