-- ============================================================
-- Bluestock Fintech — Mutual Fund Analytics Capstone
-- sql/queries.sql — 10 Analytical SQL Queries
-- Run against: data/db/bluestock_mf.db
-- ============================================================

-- ── Q1: Top 10 funds by AUM (scheme-level) ──────────────────
SELECT
    fp.scheme_name,
    fp.fund_house,
    fp.category,
    fp.plan,
    ROUND(fp.aum_crore / 1000.0, 2)   AS aum_thousand_crore,
    fp.morningstar_rating,
    fp.sharpe_ratio
FROM fact_performance fp
ORDER BY fp.aum_crore DESC
LIMIT 10;

-- ── Q2: Average NAV per month per fund (top 5 funds) ────────
SELECT
    strftime('%Y-%m', n.date)          AS month,
    d.scheme_name,
    ROUND(AVG(n.nav), 2)               AS avg_nav,
    ROUND(MIN(n.nav), 2)               AS min_nav,
    ROUND(MAX(n.nav), 2)               AS max_nav
FROM fact_nav n
JOIN dim_fund d ON n.amfi_code = d.amfi_code
WHERE n.amfi_code IN (119551, 125497, 120503, 148567, 119092)
GROUP BY month, d.scheme_name
ORDER BY d.scheme_name, month;

-- ── Q3: SIP inflow YoY growth ───────────────────────────────
SELECT
    month,
    sip_inflow_crore,
    ROUND(yoy_growth_pct, 1)           AS yoy_growth_pct,
    ROUND(sip_aum_lakh_crore, 2)       AS sip_aum_lakh_crore,
    active_sip_accounts_crore
FROM fact_sip_industry
WHERE yoy_growth_pct IS NOT NULL
ORDER BY month;

-- ── Q4: Total transactions and amount by state ───────────────
SELECT
    t.state,
    COUNT(*)                           AS num_transactions,
    ROUND(SUM(t.amount_inr)/1e7, 2)   AS total_amount_crore,
    ROUND(AVG(t.amount_inr), 0)        AS avg_txn_amount,
    COUNT(DISTINCT t.investor_id)      AS unique_investors
FROM fact_transactions t
GROUP BY t.state
ORDER BY total_amount_crore DESC;

-- ── Q5: Funds with expense ratio below 1% (Direct plans) ────
SELECT
    d.scheme_name,
    d.fund_house,
    d.category,
    d.sub_category,
    d.expense_ratio_pct,
    fp.sharpe_ratio,
    fp.return_3yr_pct
FROM dim_fund d
JOIN fact_performance fp ON d.amfi_code = fp.amfi_code
WHERE d.expense_ratio_pct < 1.0
  AND d.plan = 'Direct'
ORDER BY d.expense_ratio_pct ASC;

-- ── Q6: Risk-return comparison — Sharpe > 1 performers ──────
SELECT
    fp.scheme_name,
    fp.fund_house,
    fp.category,
    fp.plan,
    ROUND(fp.return_3yr_pct, 2)        AS return_3yr,
    ROUND(fp.sharpe_ratio, 3)          AS sharpe,
    ROUND(fp.sortino_ratio, 3)         AS sortino,
    ROUND(fp.alpha, 2)                 AS alpha,
    ROUND(fp.beta, 3)                  AS beta,
    ROUND(fp.max_drawdown_pct, 2)      AS max_drawdown
FROM fact_performance fp
WHERE fp.sharpe_ratio > 1.0
ORDER BY fp.sharpe_ratio DESC;

-- ── Q7: SIP vs Lumpsum vs Redemption split by age group ─────
SELECT
    t.age_group,
    t.transaction_type,
    COUNT(*)                           AS num_txn,
    ROUND(SUM(t.amount_inr)/1e7, 2)   AS total_crore,
    ROUND(AVG(t.amount_inr), 0)        AS avg_amount
FROM fact_transactions t
GROUP BY t.age_group, t.transaction_type
ORDER BY t.age_group, t.transaction_type;

-- ── Q8: Top 10 stock holdings by total weight across funds ───
SELECT
    ph.stock_name,
    ph.sector,
    COUNT(DISTINCT ph.amfi_code)       AS num_funds_holding,
    ROUND(AVG(ph.weight_pct), 2)       AS avg_weight_pct,
    ROUND(MAX(ph.weight_pct), 2)       AS max_weight_pct,
    ROUND(SUM(ph.market_value_cr), 1)  AS total_market_value_cr
FROM fact_portfolio ph
GROUP BY ph.stock_name, ph.sector
ORDER BY num_funds_holding DESC, avg_weight_pct DESC
LIMIT 10;

-- ── Q9: Folio count growth (equity segment) ─────────────────
SELECT
    month,
    total_folios_crore,
    equity_folios_crore,
    ROUND(equity_folios_crore / total_folios_crore * 100, 1)
                                       AS equity_share_pct,
    ROUND(total_folios_crore - LAG(total_folios_crore)
          OVER (ORDER BY month), 2)    AS qoq_growth_crore
FROM fact_folio_count
ORDER BY month;

-- ── Q10: Fund performance vs benchmark (alpha ranking) ───────
SELECT
    fp.scheme_name,
    fp.fund_house,
    fp.category,
    fp.plan,
    ROUND(fp.return_3yr_pct, 2)        AS fund_3yr_cagr,
    ROUND(fp.benchmark_3yr_pct, 2)     AS benchmark_3yr_cagr,
    ROUND(fp.alpha, 2)                 AS alpha,
    ROUND(fp.beta, 3)                  AS beta,
    CASE
        WHEN fp.alpha > 2  THEN 'Strong Outperformer'
        WHEN fp.alpha > 0  THEN 'Outperformer'
        WHEN fp.alpha = 0  THEN 'In-line'
        ELSE 'Underperformer'
    END                                AS performance_label
FROM fact_performance fp
ORDER BY fp.alpha DESC;
