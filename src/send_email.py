"""
Send KCC Formatter URL to team by email.
Called by formatter.yml workflow after tunnel URL is known.

Required env vars:
  GMAIL_USER         — sender Gmail address
  GMAIL_APP_PASSWORD — 16-char Gmail App Password
  FORMATTER_URL      — the trycloudflare.com URL to share
"""

import smtplib, ssl, os, sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sender   = os.environ.get("GMAIL_USER", "")
password = os.environ.get("GMAIL_APP_PASSWORD", "")
url      = os.environ.get("FORMATTER_URL", "")

if not sender or not password:
    print("Email skipped — GMAIL_USER or GMAIL_APP_PASSWORD not set")
    sys.exit(0)

if not url:
    print("Email skipped — FORMATTER_URL not set")
    sys.exit(0)

recipients = ["mahadevasw@gmail.com", "jkkiran06@gmail.com"]

# ── Plain text ────────────────────────────────────────────────────────────────
text = f"""KCC Data Formatter is READY!

Link     : {url}
Password : from GitHub Secrets
Valid for: 6 hours

Open this link from any device — phone, tablet or laptop.

— KCC Automation System
Kagwad Block, Belagavi, Karnataka"""

# ── HTML ──────────────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html><body style="font-family:Arial,sans-serif;max-width:520px;margin:auto;padding:20px;">
  <div style="background:linear-gradient(135deg,#0f4c2a,#1a6b3c);
              border-radius:12px 12px 0 0;padding:20px;text-align:center;">
    <h2 style="color:#fff;margin:0;">&#128203; KCC Data Formatter</h2>
    <p style="color:rgba(255,255,255,.8);margin:6px 0 0;font-size:13px;">
      Kagwad Block &middot; Belagavi &middot; Karnataka
    </p>
  </div>
  <div style="border:1px solid #e0f0e8;border-top:none;
              border-radius:0 0 12px 12px;padding:24px;">
    <p style="font-size:16px;color:#065f46;font-weight:bold;">
      &#9989; Formatter is READY!
    </p>
    <p style="margin:0 0 10px;color:#555;font-size:13px;">
      Click the button below to open from any device:
    </p>
    <a href="{url}"
       style="display:inline-block;background:linear-gradient(90deg,#1a6b3c,#2d9e5f);
              color:#fff;text-decoration:none;padding:13px 30px;border-radius:8px;
              font-weight:bold;font-size:15px;margin:6px 0;">
      &#128279; Open KCC Formatter
    </a>
    <table style="margin-top:22px;width:100%;border-collapse:collapse;font-size:13px;">
      <tr>
        <td style="padding:7px 0;color:#888;width:100px;">&#128273; Password</td>
        <td style="color:#1a1a1a;font-weight:600;">From GitHub Secrets</td>
      </tr>
      <tr>
        <td style="padding:7px 0;color:#888;">&#8987; Valid for</td>
        <td style="color:#1a1a1a;font-weight:600;">6 hours from now</td>
      </tr>
      <tr>
        <td style="padding:7px 0;color:#888;">&#128204; Direct URL</td>
        <td style="color:#1a6b3c;font-size:11px;word-break:break-all;">{url}</td>
      </tr>
    </table>
    <p style="margin-top:20px;font-size:11px;color:#bbb;
              border-top:1px solid #eee;padding-top:12px;">
      &copy; 2026 Kiran Karchi &nbsp;&middot;&nbsp; KCC Automation Project
    </p>
  </div>
</body></html>"""

# ── Build and send ────────────────────────────────────────────────────────────
msg = MIMEMultipart("alternative")
msg["Subject"] = "KCC Data Formatter is Ready - Open Link Inside"
msg["From"]    = f"KCC Automation <{sender}>"
msg["To"]      = ", ".join(recipients)
msg.attach(MIMEText(text, "plain"))
msg.attach(MIMEText(html, "html"))

try:
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
        server.login(sender, password)
        server.sendmail(sender, recipients, msg.as_string())
    print(f"Email sent to: {', '.join(recipients)} ✅")
except Exception as e:
    print(f"Email failed: {e}")
    sys.exit(1)
