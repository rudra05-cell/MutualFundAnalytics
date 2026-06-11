# 📊 Bluestock Fintech — Mutual Fund Analytics Platform
### Capstone Project | Internship 2026

> **A full-stack Mutual Fund Analytics Platform** — ETL pipeline, relational database,
> Exploratory Data Analysis, risk-adjusted performance metrics, and an interactive
> Power BI dashboard — built on publicly available AMFI India data.

---

## 🏢 Company
**Bluestock Fintech Pvt. Ltd.** — Democratising investment analytics for retail and
institutional investors in India.

---

## 📌 Project Objectives

| # | Objective | Outcome |
|---|-----------|---------|
| O1 | ETL pipeline from raw AMFI data | Automated Python script |
| O2 | Normalised SQL schema | 5-table star schema (SQLite) |
| O3 | Comprehensive EDA | 15+ charts in Jupyter |
| O4 | Performance & risk metrics | Sharpe, Sortino, Alpha, Beta, VaR |
| O5 | Interactive BI dashboard | Power BI / Streamlit |
| O6 | Investor transaction analysis | Demographic & geographic insights |
| O7 | Benchmark comparison | Alpha / tracking error report |
| O8 | Documentation & presentation | PDF report + PPTX |

---

## 📁 Folder Structure

```
bluestock_mf_capstone/
├── data/
│   ├── raw/           ← Original downloaded files (never edited)
│   ├── processed/     ← Cleaned, merged CSVs
│   └── db/            ← bluestock_mf.db (SQLite) — gitignored
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_analysis.ipynb
│   ├── 04_performance_analytics.ipynb
│   └── 05_advanced_analytics.ipynb
├── scripts/
│   ├── data_ingestion.py      ← Day 1: load all CSVs, quality check
│   ├── live_nav_fetch.py      ← Day 1: fetch live NAV from mfapi.in
│   ├── etl_pipeline.py        ← Day 2: clean + load into SQLite
│   ├── compute_metrics.py     ← Day 4: Sharpe, Sortino, Alpha, Beta
│   └── recommender.py         ← Day 6: fund recommendation engine
├── sql/
│   ├── schema.sql             ← CREATE TABLE statements
│   └── queries.sql            ← 10 analytical queries
├── dashboard/
│   └── bluestock_mf.pbix      ← Power BI dashboard
├── reports/
│   ├── Final_Report.pdf
│   └── Presentation.pptx
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/bluestock-mf-capstone.git
cd bluestock-mf-capstone
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate       # Mac/Linux
venv\Scripts\activate          # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Day 1 ingestion
```bash
python scripts/data_ingestion.py
```

### 5. Fetch live NAV from mfapi.in
```bash
python scripts/live_nav_fetch.py
```

### 6. Run the full ETL pipeline (after Day 2)
```bash
python scripts/etl_pipeline.py
```

---

## 📊 Datasets

| File | Rows | Description |
|------|------|-------------|
| `01_fund_master.csv` | 40 | Master list of 40 fund schemes |
| `02_nav_history.csv` | ~46,000 | Daily NAV (Jan 2022 – May 2026) |
| `03_aum_by_fund_house.csv` | ~90 | Quarterly AUM per AMC |
| `04_monthly_sip_inflows.csv` | 48 | Monthly SIP inflow data |
| `05_category_inflows.csv` | ~144 | Net inflows by category |
| `06_industry_folio_count.csv` | 21 | Industry folio count |
| `07_scheme_performance.csv` | 40 | Risk-return metrics |
| `08_investor_transactions.csv` | ~32,000 | Investor transactions |
| `09_portfolio_holdings.csv` | ~320 | Top stock holdings per fund |
| `10_benchmark_indices.csv` | ~8,000 | Nifty 50, 100, BSE indices |

All data sourced from publicly available AMFI India, mfapi.in, NSE/BSE data.

---

## 🧮 Key Metrics Computed

- **CAGR** — 1yr, 3yr, 5yr compound annual growth rates
- **Sharpe Ratio** — Risk-adjusted return (Rf = 6.5%)
- **Sortino Ratio** — Downside-risk-adjusted return
- **Alpha & Beta** — OLS regression vs Nifty 100
- **Maximum Drawdown** — Worst peak-to-trough decline
- **VaR (95%)** — Value at Risk via historical simulation
- **CVaR** — Conditional VaR (Expected Shortfall)
- **Tracking Error** — Std dev of fund return minus benchmark return

---

## 📈 Dashboard Pages (Power BI)

| Page | Focus |
|------|-------|
| 1 | Industry Overview — AUM, SIP inflows, folio count |
| 2 | Fund Performance — Risk-return scatter, scorecard |
| 3 | Investor Analytics — Geography, demographics |
| 4 | SIP & Market Trends — Category inflows, Nifty correlation |

---

## 🗄️ Database Schema

```sql
dim_fund          -- 40 rows:  fund metadata
dim_date          -- 1,500 rows: date dimension
fact_nav          -- 46,000 rows: daily NAV
fact_transactions -- 32,000+ rows: investor transactions
fact_performance  -- 40 rows: risk-return metrics
fact_portfolio    -- 320 rows: stock holdings
fact_aum          -- 90 rows: quarterly AUM
fact_sip_industry -- 48 rows: monthly SIP stats
```

> ⚠️ **Note:** `*.db` files are in `.gitignore`. To recreate the database,
> run `python scripts/etl_pipeline.py` after cloning.

---

## 👤 Author

**[Your Name]**
Data Analyst Intern — Bluestock Fintech Pvt. Ltd.
Capstone Project — June 2026

---

## ⚠️ Disclaimer

All data is sourced from publicly available information (AMFI India, NSE, BSE, mfapi.in).
This project is for **educational purposes only** and does not constitute financial advice.
Mutual Fund investments are subject to market risks.
