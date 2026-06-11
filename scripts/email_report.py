"""
Bluestock Fintech — Bonus B5: Automated HTML Email Report Generator
Generates a weekly mutual fund performance summary as a styled HTML email
and optionally sends it via Gmail SMTP.

HOW TO GENERATE HTML (no email):
  python scripts/email_report.py --html-only

HOW TO SEND EMAIL:
  1. Set environment variables:
       export EMAIL_FROM="your_gmail@gmail.com"
       export EMAIL_PASS="your_app_password"      # Gmail App Password
       export EMAIL_TO="recipient@example.com"
  2. Run: python scripts/email_report.py

GMAIL APP PASSWORD:
  Google Account → Security → 2-Step Verification → App Passwords
  Create one for "Mail" and use it as EMAIL_PASS (NOT your Gmail login password)
"""

import os, sqlite3, smtplib, sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / "data" / "db" / "bluestock_mf.db"
OUT_HTML = BASE_DIR / "reports" / "weekly_report.html"


def load_data():
    conn  = sqlite3.connect(DB_PATH)
    perf  = pd.read_sql("SELECT * FROM fact_performance ORDER BY sharpe_ratio DESC", conn)
    sip   = pd.read_sql("SELECT * FROM fact_sip_industry ORDER BY month DESC LIMIT 3", conn)
    folio = pd.read_sql("SELECT * FROM fact_folio_count  ORDER BY month DESC LIMIT 1", conn)
    conn.close()
    metrics = pd.read_csv(BASE_DIR/"data/processed/computed_metrics.csv")
    return perf, sip, folio, metrics


def build_html(perf, sip, folio, metrics) -> str:
    top5    = metrics.head(5)
    latest  = sip.iloc[0]
    fl      = folio.iloc[0]
    today   = datetime.today().strftime("%d %B %Y")

    def rows(df, cols, fmt=None):
        out = ""
        for i, row in enumerate(df.itertuples()):
            bg = "#F1F5F9" if i % 2 == 0 else "#FFFFFF"
            cells = ""
            for c in cols:
                v = getattr(row, c)
                if fmt and c in fmt: v = fmt[c](v)
                cells += f"<td style='padding:8px 12px;border-bottom:1px solid #E2E8F0'>{v}</td>"
            out += f"<tr style='background:{bg}'>{cells}</tr>"
        return out

    top5_rows = rows(
        top5, ["scheme_name","cagr_3yr","sharpe_ratio","alpha","composite_score"],
        fmt={"scheme_name": lambda v: str(v)[:35],
             "cagr_3yr":    lambda v: f"{v:.1f}%",
             "sharpe_ratio":lambda v: f"{v:.3f}",
             "alpha":       lambda v: f"{v:.3f}",
             "composite_score":lambda v: f"<b>{v:.0f}/100</b>"})

    perf_top = perf.head(5)
    perf_rows = rows(
        perf_top, ["scheme_name","return_1yr_pct","return_3yr_pct","sharpe_ratio","max_drawdown_pct"],
        fmt={"scheme_name":     lambda v: str(v)[:35],
             "return_1yr_pct":  lambda v: f"<span style='color:{'#16A34A' if v>0 else '#DC2626'}'>{v:.1f}%</span>",
             "return_3yr_pct":  lambda v: f"<span style='color:{'#16A34A' if v>0 else '#DC2626'}'>{v:.1f}%</span>",
             "sharpe_ratio":    lambda v: f"{v:.3f}",
             "max_drawdown_pct":lambda v: f"<span style='color:#DC2626'>{v:.1f}%</span>"})

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8">
<style>
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#F8FAFC;margin:0;padding:20px;color:#1E293B}}
  .wrap{{max-width:780px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08)}}
  .hdr{{background:linear-gradient(135deg,#0D2137,#1565C0);padding:32px 36px;color:#fff}}
  .hdr h1{{margin:0 0 6px;font-size:26px;letter-spacing:0.5px}}
  .hdr p{{margin:0;opacity:0.75;font-size:13px}}
  .kpi-row{{display:flex;gap:0;border-bottom:3px solid #1565C0}}
  .kpi{{flex:1;text-align:center;padding:18px 8px;border-right:1px solid #E2E8F0;background:#F1F5F9}}
  .kpi:last-child{{border-right:none}}
  .kpi .val{{font-size:22px;font-weight:700;color:#1565C0}}
  .kpi .lbl{{font-size:10px;color:#64748B;margin-top:3px;text-transform:uppercase;letter-spacing:0.5px}}
  .sec{{padding:24px 32px;border-bottom:1px solid #E2E8F0}}
  .sec h2{{color:#0D2137;font-size:15px;margin:0 0 14px;border-left:4px solid #1565C0;padding-left:10px}}
  table{{width:100%;border-collapse:collapse;font-size:12.5px}}
  th{{background:#1565C0;color:#fff;padding:9px 12px;text-align:left;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.4px}}
  .insight{{background:#EFF6FF;border-left:4px solid #1565C0;padding:12px 16px;border-radius:0 6px 6px 0;font-size:13px;margin-bottom:10px}}
  .insight b{{color:#1565C0}}
  .ftr{{background:#0D2137;color:#94A3B8;padding:18px 32px;font-size:11px;text-align:center}}
  .badge{{display:inline-block;background:#DCFCE7;color:#16A34A;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600}}
  .badge.red{{background:#FEE2E2;color:#DC2626}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <h1>📊 Bluestock Fintech — Weekly MF Report</h1>
    <p>Mutual Fund Analytics Platform  |  Generated: {today}</p>
  </div>

  <div class="kpi-row">
    <div class="kpi"><div class="val">₹81 L Cr</div><div class="lbl">Industry AUM</div></div>
    <div class="kpi"><div class="val">₹{latest['sip_inflow_crore']:,} Cr</div><div class="lbl">Latest SIP Inflow</div></div>
    <div class="kpi"><div class="val">{fl['total_folios_crore']:.2f} Cr</div><div class="lbl">Total Folios</div></div>
    <div class="kpi"><div class="val">{latest['active_sip_accounts_crore']:.2f} Cr</div><div class="lbl">Active SIP Accounts</div></div>
    <div class="kpi"><div class="val">{(perf['sharpe_ratio']>1).sum()}</div><div class="lbl">Funds Sharpe &gt; 1</div></div>
  </div>

  <div class="sec">
    <h2>🏆 Top 5 Funds — Composite Scorecard</h2>
    <table>
      <tr><th>Fund</th><th>3yr CAGR</th><th>Sharpe</th><th>Alpha</th><th>Score/100</th></tr>
      {top5_rows}
    </table>
  </div>

  <div class="sec">
    <h2>📈 Risk-Return Summary — Top 5 by Sharpe</h2>
    <table>
      <tr><th>Fund</th><th>1yr Return</th><th>3yr CAGR</th><th>Sharpe</th><th>Max DD</th></tr>
      {perf_rows}
    </table>
  </div>

  <div class="sec">
    <h2>💡 Key Insights This Week</h2>
    <div class="insight">
      <b>SIP Momentum:</b> Latest monthly SIP inflow was ₹{latest['sip_inflow_crore']:,} Cr.
      Active SIP accounts stand at {latest['active_sip_accounts_crore']:.2f} crore, reflecting sustained retail participation.
    </div>
    <div class="insight">
      <b>Top Performer:</b> {str(metrics.iloc[0]['scheme_name'])[:40]} leads with composite score
      <b>{metrics.iloc[0]['composite_score']:.0f}/100</b> (Sharpe: {metrics.iloc[0]['sharpe_ratio']:.3f},
      3yr CAGR: {metrics.iloc[0]['cagr_3yr']:.1f}%).
    </div>
    <div class="insight">
      <b>Industry Folios:</b> Total folios reached {fl['total_folios_crore']:.2f} crore
      (Equity: {fl['equity_folios_crore']:.2f}Cr · Debt: {fl['debt_folios_crore']:.2f}Cr ·
      Hybrid: {fl['hybrid_folios_crore']:.2f}Cr).
    </div>
    <div class="insight">
      <b>Alpha Leaders:</b> {(perf['alpha']>0).sum() if 'alpha' in perf.columns else 'N/A'} funds
      generated positive alpha vs benchmark — strong active management performance.
    </div>
  </div>

  <div class="ftr">
    <p>Bluestock Fintech Pvt. Ltd. | Mutual Fund Analytics Capstone 2026</p>
    <p>Data sourced from AMFI India, mfapi.in, NSE/BSE. For educational purposes only. Not financial advice.</p>
    <p>To unsubscribe or change report frequency, contact your Bluestock dashboard administrator.</p>
  </div>
</div>
</body>
</html>"""
    return html


def send_email(html: str, subject: str):
    """Send HTML email via Gmail SMTP using environment variables."""
    from_addr = os.environ.get("EMAIL_FROM")
    password  = os.environ.get("EMAIL_PASS")
    to_addr   = os.environ.get("EMAIL_TO")

    if not all([from_addr, password, to_addr]):
        print("⚠  EMAIL_FROM / EMAIL_PASS / EMAIL_TO not set in environment.")
        print("   HTML report saved to reports/weekly_report.html")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = from_addr
    msg["To"]      = to_addr
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_addr, password)
        server.sendmail(from_addr, to_addr, msg.as_string())
    print(f"✅ Email sent to {to_addr}")
    return True


if __name__ == "__main__":
    perf, sip, folio, metrics = load_data()
    html    = build_html(perf, sip, folio, metrics)
    today   = datetime.today().strftime("%d %B %Y")
    subject = f"Bluestock MF Weekly Report — {today}"

    # Always save HTML locally
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"✅ HTML report saved → {OUT_HTML}")
    print(f"   Size: {OUT_HTML.stat().st_size // 1024} KB")

    # Try email unless --html-only flag
    if "--html-only" not in sys.argv:
        send_email(html, subject)
