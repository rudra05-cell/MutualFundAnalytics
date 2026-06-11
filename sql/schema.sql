-- ============================================================
-- Bluestock Fintech — Mutual Fund Analytics Capstone
-- sql/schema.sql  — Star Schema DDL
-- ============================================================

-- Drop tables if re-running (development convenience)
DROP TABLE IF EXISTS dim_fund;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS fact_nav;
DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS fact_performance;
DROP TABLE IF EXISTS fact_portfolio;
DROP TABLE IF EXISTS fact_aum;
DROP TABLE IF EXISTS fact_sip_industry;
DROP TABLE IF EXISTS fact_category_inflows;
DROP TABLE IF EXISTS fact_folio_count;
DROP TABLE IF EXISTS fact_benchmarks;

-- ── Dimension: Fund Master ──────────────────────────────────
CREATE TABLE dim_fund (
    amfi_code           INTEGER PRIMARY KEY,
    fund_house          TEXT    NOT NULL,
    scheme_name         TEXT    NOT NULL,
    category            TEXT,
    sub_category        TEXT,
    plan                TEXT    CHECK(plan IN ('Regular','Direct')),
    launch_date         TEXT,
    benchmark           TEXT,
    expense_ratio_pct   REAL    CHECK(expense_ratio_pct BETWEEN 0.05 AND 3.0),
    exit_load_pct       REAL,
    min_sip_amount      INTEGER,
    min_lumpsum_amount  INTEGER,
    fund_manager        TEXT,
    risk_category       TEXT,
    sebi_category_code  TEXT
);

-- ── Dimension: Date ─────────────────────────────────────────
CREATE TABLE dim_date (
    date        TEXT PRIMARY KEY,
    year        INTEGER,
    month       INTEGER,
    month_name  TEXT,
    quarter     INTEGER,
    day_of_week TEXT,
    is_weekday  INTEGER,
    fy_year     INTEGER
);

-- ── Fact: Daily NAV ─────────────────────────────────────────
CREATE TABLE fact_nav (
    amfi_code        INTEGER REFERENCES dim_fund(amfi_code),
    date             TEXT    REFERENCES dim_date(date),
    nav              REAL    NOT NULL CHECK(nav > 0),
    daily_return_pct REAL,
    PRIMARY KEY (amfi_code, date)
);
CREATE INDEX idx_nav_code ON fact_nav(amfi_code);
CREATE INDEX idx_nav_date ON fact_nav(date);

-- ── Fact: Investor Transactions ─────────────────────────────
CREATE TABLE fact_transactions (
    investor_id        TEXT,
    transaction_date   TEXT,
    amfi_code          INTEGER REFERENCES dim_fund(amfi_code),
    transaction_type   TEXT CHECK(transaction_type IN ('Sip','Lumpsum','Redemption')),
    amount_inr         INTEGER NOT NULL CHECK(amount_inr > 0),
    state              TEXT,
    city               TEXT,
    city_tier          TEXT    CHECK(city_tier IN ('T30','B30')),
    age_group          TEXT,
    gender             TEXT    CHECK(gender IN ('Male','Female')),
    annual_income_lakh REAL,
    payment_mode       TEXT,
    kyc_status         TEXT
);
CREATE INDEX idx_tx_investor ON fact_transactions(investor_id);
CREATE INDEX idx_tx_code     ON fact_transactions(amfi_code);
CREATE INDEX idx_tx_date     ON fact_transactions(transaction_date);

-- ── Fact: Scheme Performance Metrics ────────────────────────
CREATE TABLE fact_performance (
    amfi_code          INTEGER PRIMARY KEY REFERENCES dim_fund(amfi_code),
    scheme_name        TEXT,
    fund_house         TEXT,
    category           TEXT,
    plan               TEXT,
    return_1yr_pct     REAL,
    return_3yr_pct     REAL,
    return_5yr_pct     REAL,
    benchmark_3yr_pct  REAL,
    alpha              REAL,
    beta               REAL,
    sharpe_ratio       REAL,
    sortino_ratio      REAL,
    std_dev_ann_pct    REAL,
    max_drawdown_pct   REAL,
    aum_crore          INTEGER,
    expense_ratio_pct  REAL,
    morningstar_rating INTEGER,
    risk_grade         TEXT
);

-- ── Fact: Portfolio Holdings ─────────────────────────────────
CREATE TABLE fact_portfolio (
    amfi_code         INTEGER REFERENCES dim_fund(amfi_code),
    stock_symbol      TEXT,
    stock_name        TEXT,
    sector            TEXT,
    weight_pct        REAL,
    market_value_cr   REAL,
    current_price_inr REAL,
    portfolio_date    TEXT
);

-- ── Fact: AUM by Fund House ──────────────────────────────────
CREATE TABLE fact_aum (
    date           TEXT,
    fund_house     TEXT,
    aum_lakh_crore REAL,
    aum_crore      INTEGER,
    num_schemes    INTEGER,
    PRIMARY KEY (date, fund_house)
);

-- ── Fact: Monthly SIP Industry Stats ────────────────────────
CREATE TABLE fact_sip_industry (
    month                     TEXT PRIMARY KEY,
    sip_inflow_crore          INTEGER,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh     REAL,
    sip_aum_lakh_crore        REAL,
    yoy_growth_pct            REAL
);

-- ── Fact: Category Inflows ───────────────────────────────────
CREATE TABLE fact_category_inflows (
    month            TEXT,
    category         TEXT,
    net_inflow_crore REAL,
    PRIMARY KEY (month, category)
);

-- ── Fact: Industry Folio Count ───────────────────────────────
CREATE TABLE fact_folio_count (
    month               TEXT PRIMARY KEY,
    total_folios_crore  REAL,
    equity_folios_crore REAL,
    debt_folios_crore   REAL,
    hybrid_folios_crore REAL,
    others_folios_crore REAL
);

-- ── Fact: Benchmark Indices ──────────────────────────────────
CREATE TABLE fact_benchmarks (
    date             TEXT,
    index_name       TEXT,
    close_value      REAL,
    daily_return_pct REAL,
    PRIMARY KEY (date, index_name)
);
