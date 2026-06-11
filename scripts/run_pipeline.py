"""
============================================================
Bluestock Fintech — Master Pipeline Runner
Run EVERYTHING with one command:
  python scripts/run_pipeline.py

Steps executed:
  1. Data Ingestion    — load & validate all 10 CSVs
  2. ETL Pipeline      — clean + load into SQLite (11 tables)
  3. Compute Metrics   — Sharpe, Alpha, Beta, VaR, Scorecard
  4. Advanced Analytics— cohort, SIP continuity, HHI
  5. Generate Charts   — 17 PNG charts
  6. Email Report      — HTML weekly summary (--html-only)
============================================================
"""

import sys, time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))


def run_step(name, fn):
    print(f"\n{'='*65}")
    print(f"  ▶  {name}")
    print("="*65)
    t0 = time.time()
    try:
        fn()
        print(f"\n  ✅  Done in {time.time()-t0:.1f}s")
    except Exception as e:
        print(f"\n  ❌  FAILED: {e}")
        raise


if __name__ == "__main__":
    from data_ingestion import run_ingestion
    from etl_pipeline    import run_etl
    from compute_metrics import run_metrics
    from recommender     import cohort_analysis, sip_continuity_analysis, sector_hhi
    from generate_charts import (chart_nav_trends, chart_aum_growth, chart_sip_inflows,
                                  chart_category_heatmap, chart_demographics,
                                  chart_geo_distribution, chart_folio_growth,
                                  chart_correlation, chart_sector_allocation,
                                  chart_risk_return, chart_scorecard,
                                  chart_rolling_sharpe, chart_benchmark_comparison,
                                  chart_max_drawdown, chart_transaction_volume)
    from email_report    import load_data, build_html
    from pathlib         import Path

    def all_charts():
        for fn in [chart_nav_trends, chart_aum_growth, chart_sip_inflows,
                   chart_category_heatmap, chart_demographics, chart_geo_distribution,
                   chart_folio_growth, chart_correlation, chart_sector_allocation,
                   chart_risk_return, chart_scorecard, chart_rolling_sharpe,
                   chart_benchmark_comparison, chart_max_drawdown, chart_transaction_volume]:
            fn()

    def advanced():
        cohort_analysis()
        sip_continuity_analysis()
        sector_hhi()

    def gen_email():
        import pandas as pd, numpy as np
        import sqlite3, warnings
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt; import seaborn as sns
        warnings.filterwarnings("ignore")
        # Monte Carlo
        DB  = BASE_DIR/"data/db/bluestock_mf.db"
        CHD = BASE_DIR/"reports/charts"
        conn = sqlite3.connect(DB)
        nav  = pd.read_sql("SELECT * FROM fact_nav", conn, parse_dates=["date"])
        fund = pd.read_sql("SELECT amfi_code, scheme_name FROM dim_fund", conn)
        conn.close()
        np.random.seed(42)
        sbi = nav[nav["amfi_code"]==119551].sort_values("date")
        ret = sbi["daily_return_pct"].dropna()
        mu, sigma, S0 = ret.mean(), ret.std(), sbi["nav"].iloc[-1]
        N, D = 1000, 252*5
        paths = np.zeros((D+1,N)); paths[0]=S0
        for t in range(1,D+1):
            Z=np.random.standard_normal(N)
            paths[t]=paths[t-1]*np.exp((mu-0.5*sigma**2)+sigma*Z)
        # EF
        sel=[119551,125497,120503,118632,119092]
        names=[fund.set_index("amfi_code").loc[c,"scheme_name"].split(" - ")[0][:18] for c in sel]
        wide=(nav[nav["amfi_code"].isin(sel)].pivot(index="date",columns="amfi_code",values="daily_return_pct").dropna())
        wide.columns=names
        mu_a=wide.mean()*252; cov_a=wide.cov()*252
        np.random.seed(42)
        p_ret,p_std,p_sr,p_wts=[],[],[],[]
        for _ in range(12000):
            w=np.random.dirichlet(np.ones(5))
            r=float(np.dot(w,mu_a)); s=float(np.sqrt(w@cov_a.values@w))
            p_ret.append(r); p_std.append(s); p_sr.append((r-0.065)/s); p_wts.append(w)
        p_ret=np.array(p_ret); p_std=np.array(p_std); p_sr=np.array(p_sr)
        # Save bonus charts
        BLUE="#1565C0"; TEAL="#00897B"; ORANGE="#F4511E"
        fig,(ax1,ax2)=plt.subplots(1,2,figsize=(14,5))
        ax1.plot(paths[:,:200],alpha=0.05,color=BLUE,lw=0.6)
        ax1.plot(np.median(paths,axis=1),color="red",lw=2.5,label=f"Median ₹{np.median(paths[-1]):,.0f}")
        ax1.plot(np.percentile(paths,10,axis=1),color=ORANGE,lw=1.8,ls="--",label=f"Bear ₹{np.percentile(paths[-1],10):,.0f}")
        ax1.plot(np.percentile(paths,90,axis=1),color=TEAL,lw=1.8,ls="--",label=f"Bull ₹{np.percentile(paths[-1],90):,.0f}")
        ax1.fill_between(range(D+1),np.percentile(paths,10,axis=1),np.percentile(paths,90,axis=1),alpha=0.1,color="green")
        ax1.set_title("SBI Bluechip — 5-Year Monte Carlo",fontweight="bold"); ax1.legend(fontsize=9)
        ax2.hist(paths[-1],bins=60,color=BLUE,alpha=0.8,edgecolor="white")
        ax2.axvline(np.median(paths[-1]),color="red",lw=2); ax2.set_title("NAV Distribution Year 5",fontweight="bold")
        for ax in [ax1,ax2]: ax.set_facecolor("#F8FAFC"); [ax.spines[s].set_visible(False) for s in ["top","right"]]
        plt.tight_layout(); plt.savefig(CHD/"B3_monte_carlo.png",dpi=130,bbox_inches="tight"); plt.close()
        mxs=p_sr.argmax()
        fig,(ax1,ax2)=plt.subplots(1,2,figsize=(14,6))
        sc=ax1.scatter(p_std*100,p_ret*100,c=p_sr,cmap="viridis",alpha=0.35,s=6)
        plt.colorbar(sc,ax=ax1,label="Sharpe")
        ax1.scatter(p_std[mxs]*100,p_ret[mxs]*100,c="red",s=250,zorder=6,marker="*",label=f"Max Sharpe {p_sr[mxs]:.2f}")
        ax1.set_title("Markowitz Efficient Frontier",fontweight="bold"); ax1.legend()
        wts=p_wts[mxs]
        colors=[BLUE,TEAL,ORANGE,"#F9A825","#7B1FA2"]
        bars=ax2.barh(names,wts*100,color=colors,alpha=0.85)
        for bar,v in zip(bars,wts*100): ax2.text(v+0.3,bar.get_y()+bar.get_height()/2,f"{v:.1f}%",va="center",fontsize=9)
        ax2.set_title("Max-Sharpe Portfolio Weights",fontweight="bold")
        for ax in [ax1,ax2]: ax.set_facecolor("#F8FAFC"); [ax.spines[s].set_visible(False) for s in ["top","right"]]
        plt.tight_layout(); plt.savefig(CHD/"B4_efficient_frontier.png",dpi=130,bbox_inches="tight"); plt.close()
        print("  ✅  B3_monte_carlo.png + B4_efficient_frontier.png")
        # HTML Email
        perf_d, sip_d, folio_d, metrics_d = load_data()
        html = build_html(perf_d, sip_d, folio_d, metrics_d)
        out  = BASE_DIR/"reports/weekly_report.html"
        out.write_text(html, encoding="utf-8")
        print(f"  ✅  weekly_report.html saved")

    run_step("1. Data Ingestion",      run_ingestion)
    run_step("2. ETL Pipeline",        run_etl)
    run_step("3. Performance Metrics", run_metrics)
    run_step("4. Advanced Analytics",  advanced)
    run_step("5. Generate Charts",     all_charts)
    run_step("6. Bonus + Email HTML",  gen_email)

    print(f"\n{'='*65}")
    print("  🎉  COMPLETE — Bluestock MF Capstone Pipeline Finished!")
    print(f"  DB      : {BASE_DIR/'data/db/bluestock_mf.db'}")
    print(f"  Charts  : {BASE_DIR/'reports/charts'}  (17 PNGs)")
    print(f"  Report  : {BASE_DIR/'reports/Final_Report.pdf'}")
    print(f"  Slides  : {BASE_DIR/'reports/Presentation.pptx'}")
    print(f"  Email   : {BASE_DIR/'reports/weekly_report.html'}")
    print(f"  Dashboard: streamlit run dashboard/app.py")
    print("="*65)
