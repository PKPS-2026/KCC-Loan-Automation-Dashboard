# KCC Loan Automation Dashboard

Automated loan application submission for [fasalrin.gov.in](https://fasalrin.gov.in) — Kisan Credit Card (KCC) portal.

---

## Project Structure

```
KCC-Loan-Automation-Dashboard/
├── src/
│   ├── PR_V4.py          # Selenium automation script
│   └── dashboard.py      # Flask web dashboard
├── config/
│   └── config.example.py # Template — copy to config.py and fill credentials
├── Dockerfile            # Docker + Chrome + noVNC setup
├── docker-compose.yml    # One-command Docker run
├── requirements.txt      # Python dependencies
└── README.md
```

---

## Run Locally (Windows)

```bash
# Install dependencies
pip install -r requirements.txt

# Start dashboard
cd src
python dashboard.py

# Open browser
http://localhost:5000
```

---

## Run via Docker (Linux / VPS)

```bash
# Clone repo
git clone https://github.com/PKPS-2026/KCC-Loan-Automation-Dashboard.git
cd KCC-Loan-Automation-Dashboard

# Start
docker-compose up -d

# Dashboard  → http://your-server-ip:5000
# VNC (Chrome browser) → http://your-server-ip:6080/vnc.html
```

---

## How It Works

1. Upload Excel file or paste data in dashboard
2. Click **Run Automation** — Chrome opens automatically
3. **Login manually** in Chrome (mobile + password + captcha)
4. Script auto-fills all KCC loan forms for each record
5. Watch live logs in dashboard

---

## Excel Format

| Aadhar Number | Loan Disbursal Date | Max Withdrawal Amount (INR) | Beneficiary Name |
|---|---|---|---|
| 123456789012 | 3/27/2026 | 53000 | Farmer Name |

---

## Config (Optional — for public URL via ngrok)

```bash
cp config/config.example.py config/config.py
# Edit config.py with your ngrok token and domain
```

---

## Ports

| Port | Service |
|------|---------|
| 5000 | Dashboard UI |
| 6080 | noVNC — view Chrome browser remotely |
