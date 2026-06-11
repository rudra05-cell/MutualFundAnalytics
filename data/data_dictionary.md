# Data Dictionary — Bluestock Fintech MF Analytics Capstone

> All datasets sourced from AMFI India, mfapi.in, NSE/BSE public data.

---

## 01 — dim_fund (40 rows)
| Column | Type | Description |
|--------|------|-------------|
| amfi_code | INTEGER PK | AMFI unique scheme code |
| fund_house | TEXT | AMC name (e.g. SBI Mutual Fund) |
| scheme_name | TEXT | Full official AMFI scheme name |
| category | TEXT | Equity / Debt / Hybrid |
| sub_category | TEXT | Large Cap / Mid Cap / Small Cap / Liquid etc. |
| plan | TEXT | Regular or Direct |
| launch_date | DATE | Fund launch date |
| benchmark | TEXT | Official benchmark index |
| expense_ratio_pct | REAL | Annual expense ratio % (0.05–3.0) |
| exit_load_pct | REAL | Exit load % |
| fund_manager | TEXT | Primary fund manager name |
| risk_category | TEXT | Low / Moderate / High / Very High |
| sebi_category_code | TEXT | EC01=LargeCap, EC03=SmallCap, DC01=Liquid |

## 02 — fact_nav (46,000 rows)
| Column | Type | Description |
|--------|------|-------------|
| amfi_code | INTEGER FK | Foreign key to dim_fund |
| date | DATE | Business date (weekends ffilled) |
| nav | REAL | NAV in ₹ (anchored to real mfapi.in values) |
| daily_return_pct | REAL | (nav_t / nav_t-1) - 1, annualised with √252 |

## 03 — fact_aum (90 rows)
| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Quarter end date |
| fund_house | TEXT | AMC name |
| aum_lakh_crore | REAL | AUM in ₹ Lakh Crore |
| aum_crore | INTEGER | AUM in ₹ Crore |
| num_schemes | INTEGER | Number of schemes managed |

## 04 — fact_sip_industry (48 rows)
| Column | Type | Description |
|--------|------|-------------|
| month | DATE | Month (YYYY-MM-01) |
| sip_inflow_crore | INTEGER | Total SIP inflows ₹ Crore |
| active_sip_accounts_crore | REAL | Active contributing SIP accounts in Crore |
| new_sip_accounts_lakh | REAL | New SIP registrations in Lakh |
| sip_aum_lakh_crore | REAL | Total SIP AUM in ₹ Lakh Crore |
| yoy_growth_pct | REAL | YoY growth % (computed, null for first 12 months) |

## 05 — fact_category_inflows (144 rows)
| Column | Type | Description |
|--------|------|-------------|
| month | DATE | Month |
| category | TEXT | Fund category |
| net_inflow_crore | REAL | Net inflow ₹ Crore (can be negative = outflow) |

## 06 — fact_folio_count (21 rows)
| Column | Type | Description |
|--------|------|-------------|
| month | DATE | Month |
| total_folios_crore | REAL | Industry total folios in Crore |
| equity_folios_crore | REAL | Equity segment folios |
| debt_folios_crore | REAL | Debt segment folios |
| hybrid_folios_crore | REAL | Hybrid segment folios |
| others_folios_crore | REAL | Other segment folios |

## 07 — fact_performance (40 rows)
| Column | Type | Description |
|--------|------|-------------|
| amfi_code | INTEGER PK | Foreign key to dim_fund |
| return_1yr_pct | REAL | 1-year absolute return % |
| return_3yr_pct | REAL | 3-year CAGR % |
| return_5yr_pct | REAL | 5-year CAGR % |
| benchmark_3yr_pct | REAL | Benchmark 3yr CAGR for comparison |
| alpha | REAL | Annualised alpha vs benchmark (OLS) |
| beta | REAL | Market sensitivity (1.0 = same as market) |
| sharpe_ratio | REAL | (Rp - Rf) / Std × √252, Rf = 6.5% |
| sortino_ratio | REAL | Sharpe using only downside std dev |
| std_dev_ann_pct | REAL | Annualised std dev of daily returns % |
| max_drawdown_pct | REAL | Worst peak-to-trough decline (negative) |
| aum_crore | INTEGER | Scheme AUM in ₹ Crore |
| expense_ratio_pct | REAL | Annual expense ratio % |
| morningstar_rating | INTEGER | 1–5 star (based on Sharpe) |

## 08 — fact_transactions (32,778 rows)
| Column | Type | Description |
|--------|------|-------------|
| investor_id | TEXT | Unique investor ID (INV000001–INV005000) |
| transaction_date | DATE | Date of transaction |
| amfi_code | INTEGER FK | Fund transacted in |
| transaction_type | TEXT | Sip / Lumpsum / Redemption |
| amount_inr | INTEGER | Transaction amount in ₹ |
| state | TEXT | Investor's state (12 states) |
| city | TEXT | Investor's city (24 cities) |
| city_tier | TEXT | T30 (Top 30 cities) or B30 |
| age_group | TEXT | 18-25 / 26-35 / 36-45 / 46-55 / 56+ |
| gender | TEXT | Male / Female |
| annual_income_lakh | REAL | Annual income ₹ Lakh |
| payment_mode | TEXT | UPI / Net Banking / Mandate / Cheque |
| kyc_status | TEXT | Verified (92%) / Pending (8%) |

## 09 — fact_portfolio (322 rows)
| Column | Type | Description |
|--------|------|-------------|
| amfi_code | INTEGER FK | Fund |
| stock_symbol | TEXT | NSE ticker symbol |
| stock_name | TEXT | Company name |
| sector | TEXT | Industry sector |
| weight_pct | REAL | Portfolio weight % |
| market_value_cr | REAL | Market value ₹ Crore |
| current_price_inr | REAL | Stock price as of portfolio date |
| portfolio_date | DATE | As-of date (Dec 2025) |

## 10 — fact_benchmarks (8,050 rows)
| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Trading date |
| index_name | TEXT | NIFTY50 / NIFTY100 / NIFTY_MIDCAP150 / BSE_SMALLCAP etc. |
| close_value | REAL | Index closing value |
| daily_return_pct | REAL | Daily return (pct_change) |

---
*Disclaimer: All data for educational purposes only. Not financial advice.*
