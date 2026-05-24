"""
KCC Loan Automation Dashboard
Run:  python dashboard.py
Opens automatically at http://localhost:5000  (or 5001 / 5002 if port busy)
"""

# ── dependency check ──────────────────────────────────────────────────────────
import sys, os

def _check(pkg, install_name=None):
    try:
        __import__(pkg)
    except ImportError:
        n = install_name or pkg
        print(f"  ⚠  Missing package '{n}'. Installing...")
        os.system(f'"{sys.executable}" -m pip install {n} -q')

_check("flask")
_check("pandas")
_check("openpyxl")

# ── imports ───────────────────────────────────────────────────────────────────
from flask import Flask, render_template_string, request, jsonify, Response, session, redirect, url_for
from functools import wraps
import pandas as pd
import subprocess, threading, queue, json, time, io, webbrowser, socket, re, tempfile, secrets
import urllib.request, urllib.parse, datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

# ── Owner info ────────────────────────────────────────────────────────────────
OWNER_NAME  = "Kiran Karchi"
OWNER_PHONE = os.environ.get("NOTIFY_PHONE", "9538775515")
OWNER_EMAIL = os.environ.get("NOTIFY_EMAIL", "jkkiranor@gmail.com")

# ── Password ──────────────────────────────────────────────────────────────────
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "kcc@2026")

# ── Telegram notification (set BOT_TOKEN + CHAT_ID in GitHub Secrets) ────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

def send_telegram(msg):
    """Send login notification via Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url  = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        }).encode()
        urllib.request.urlopen(url, data, timeout=5)
    except Exception as e:
        print(f"  Telegram notify failed: {e}")

# ── Login required decorator ──────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

# ── Login page HTML ───────────────────────────────────────────────────────────
LOGIN_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>KCC Login — Kiran Karchi</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"/>
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet"/>
<style>
*{box-sizing:border-box;}
body{
  background:
    linear-gradient(135deg,rgba(10,40,18,.72) 0%,rgba(15,76,42,.65) 50%,rgba(20,100,55,.60) 100%),
    url('https://images.unsplash.com/photo-1625246333195-78d9c38ad449?auto=format&fit=crop&w=1920&q=80')
    center center / cover no-repeat fixed;
  min-height:100vh;display:flex;align-items:center;justify-content:center;
  flex-direction:column;padding:20px;}

.login-card{border:none;border-radius:20px;box-shadow:0 16px 48px rgba(0,0,0,.3);
  width:100%;max-width:440px;overflow:hidden;}

/* Header */
.login-header{background:linear-gradient(135deg,#0f4c2a,#1a6b3c);
  color:#fff;text-align:center;padding:28px 24px 20px;}
.login-header .logo{font-size:2.5rem;margin-bottom:6px;}
.login-header h4{font-weight:800;margin:0;letter-spacing:.5px;}
.login-header .sub{opacity:.8;font-size:.85rem;margin-top:4px;}

/* Team strip */
.team-strip{background:#f8fdf9;border-bottom:1px solid #e0f0e8;
  padding:14px 20px;display:flex;gap:10px;flex-wrap:wrap;justify-content:center;}
.team-chip{display:inline-flex;align-items:center;gap:6px;
  background:#fff;border:1px solid #c8e6c9;border-radius:20px;
  padding:4px 12px;font-size:.75rem;color:#1a6b3c;font-weight:600;}
.team-chip .role{color:#888;font-weight:400;font-size:.7rem;}

/* Body */
.login-body{padding:24px;}
.form-select,.form-control{border-radius:10px;border:1.5px solid #dee2e6;
  padding:10px 14px;font-size:.95rem;}
.form-select:focus,.form-control:focus{border-color:#2d9e5f;
  box-shadow:0 0 0 3px rgba(45,158,95,.15);}
.btn-login{background:linear-gradient(90deg,#1a6b3c,#2d9e5f);border:none;
  border-radius:10px;font-weight:700;font-size:1rem;padding:12px;
  letter-spacing:.3px;transition:.2s;}
.btn-login:hover{background:linear-gradient(90deg,#0f4c2a,#1a6b3c);transform:translateY(-1px);}

/* Footer */
.login-footer{text-align:center;color:rgba(255,255,255,.75);
  font-size:.78rem;margin-top:18px;line-height:1.8;}
.login-footer strong{color:#fff;}
</style>
</head>
<body>

<div class="login-card">

  <!-- Header -->
  <div class="login-header">
    <div class="logo">🏦</div>
    <h4>KCC Loan Automation</h4>
    <div class="sub">Belagavi District &nbsp;|&nbsp; fasalrin.gov.in</div>
  </div>

  <!-- Team strip -->
  <div class="team-strip">
    <span class="team-chip">
      <i class="bi bi-shield-fill-check text-success"></i>
      Kiran Karchi <span class="role ms-1">Owner</span>
    </span>
    <span class="team-chip">
      <i class="bi bi-person-badge text-primary"></i>
      Mahanthesh Hiremath <span class="role ms-1">Manager</span>
    </span>
    <span class="team-chip">
      <i class="bi bi-person text-secondary"></i>
      Mahadev Vadeyar <span class="role ms-1">Co-ordinator</span>
    </span>
    <span class="team-chip">
      <i class="bi bi-person text-secondary"></i>
      Avinash Dugnavar <span class="role ms-1">Co-ordinator</span>
    </span>
  </div>

  <!-- Login form -->
  <div class="login-body">
    {% if error %}
    <div class="alert alert-danger py-2 text-center small mb-3">
      <i class="bi bi-exclamation-triangle-fill me-1"></i>{{ error }}
    </div>
    {% endif %}

    <form method="POST" action="/login">

      <!-- Name selector -->
      <div class="mb-3">
        <label class="form-label fw-semibold small text-muted">
          <i class="bi bi-person-circle me-1"></i>Select Your Name
        </label>
        <select name="username" class="form-select" required>
          <option value="" disabled selected>-- Select your name --</option>
          <option value="Kiran Karchi">👑 Kiran Karchi (Owner)</option>
          <option value="Mahanthesh Hiremath">🗂️ Mahanthesh Hiremath (Manager)</option>
          <option value="Mahadev Vadeyar">📋 Mahadev Vadeyar (Co-ordinator)</option>
          <option value="Avinash Dugnavar">📋 Avinash Dugnavar (Co-ordinator)</option>
        </select>
      </div>

      <!-- Password -->
      <div class="mb-4">
        <label class="form-label fw-semibold small text-muted">
          <i class="bi bi-lock-fill me-1"></i>Password
        </label>
        <input type="password" name="password" class="form-control"
               placeholder="Enter password" required/>
      </div>

      <button type="submit" class="btn btn-login text-white w-100">
        <i class="bi bi-box-arrow-in-right me-2"></i>Login to Dashboard
      </button>
    </form>
  </div>
</div>

<div class="login-footer">
  <strong>© 2026 Kiran Karchi</strong> &nbsp;|&nbsp; KCC Automation Project<br/>
  Kagwad Block &nbsp;·&nbsp; Belagavi &nbsp;·&nbsp; Karnataka
</div>

</body>
</html>
"""

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
# Save to a separate file so it never conflicts with loans.xlsx open in Excel
UPLOAD_PATH = os.path.join(BASE_DIR, "loans_upload.xlsx")
SCRIPT_PATH = os.path.join(BASE_DIR, "PR_V4.py")

# ── ngrok config — loaded from config/config.py (gitignored, stays local) ────
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))
    from config import NGROK_AUTH_TOKEN, NGROK_STATIC_DOMAIN
except ImportError:
    NGROK_AUTH_TOKEN    = ""
    NGROK_STATIC_DOMAIN = ""

REQUIRED_COLUMNS = [
    "Aadhar Number",
    "Loan Disbursal Date",
    "Max Withdrawal Amount (INR)",
]
OPTIONAL_COLUMNS = [
    "Account Number",
    "Loan Repayment Date",
    "Beneficiary Name",
]

state = {
    "records":   [],
    "running":   False,
    "process":   None,
    "statuses":  {},
    "log_queue": queue.Queue(),
    "log_buffer": [],          # replay buffer — last 500 messages for reconnects
    "summary":   {"total": 0, "success": 0, "failed": 0, "skipped": 0, "pending": 0},
}

# ─── HTML ────────────────────────────────────────────────────────────────────
HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>KCC Loan Dashboard</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"/>
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet"/>
<style>
body{
  background:
    linear-gradient(135deg,rgba(10,40,18,.55) 0%,rgba(15,76,42,.45) 50%,rgba(20,100,55,.40) 100%),
    url('https://images.unsplash.com/photo-1625246333195-78d9c38ad449?auto=format&fit=crop&w=1920&q=80')
    center center / cover no-repeat fixed;
  font-family:'Segoe UI',sans-serif;
  min-height:100vh;
}
.navbar{background:linear-gradient(90deg,#1a6b3c,#2d9e5f);}
.card{border:none;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.25);background:rgba(255,255,255,.93);}
.card-header{border-radius:12px 12px 0 0!important;font-weight:600;}

/* tabs */
.nav-tabs .nav-link{border:none;color:#555;padding:.45rem 1rem;}
.nav-tabs .nav-link.active{border-bottom:3px solid #2d9e5f;color:#1a6b3c;font-weight:700;background:transparent;}

/* drop zone */
#dropzone{border:2px dashed #2d9e5f;border-radius:10px;padding:30px 20px;
  text-align:center;cursor:pointer;transition:.2s;background:#fff;}
#dropzone:hover,.drag-over{background:#e8f8ef!important;border-color:#1a6b3c!important;}
#dropzone i{font-size:2.6rem;color:#2d9e5f;}

/* paste area */
#pasteArea{font-size:.8rem;resize:vertical;min-height:120px;}

/* column chips */
.chip{display:inline-flex;align-items:center;gap:4px;padding:3px 10px;
  border-radius:20px;font-size:.73rem;font-weight:600;margin:2px;}
.chip-ok{background:#d1fae5;color:#065f46;}
.chip-miss{background:#fee2e2;color:#991b1b;}

/* stat cards */
.sc{border-radius:12px;color:#fff;padding:16px 18px;}
.sc-total{background:linear-gradient(135deg,#2d9e5f,#1a6b3c);}
.sc-ok   {background:linear-gradient(135deg,#198754,#0f5132);}
.sc-fail {background:linear-gradient(135deg,#dc3545,#842029);}
.sc-pend {background:linear-gradient(135deg,#fd7e14,#9c4a00);}
.sc-skip {background:linear-gradient(135deg,#6c757d,#343a40);}
.sc .num{font-size:1.9rem;font-weight:700;line-height:1;}
.sc .lbl{font-size:.77rem;opacity:.85;margin-top:3px;}

/* run button pulse */
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(45,158,95,.55);}
  50%{box-shadow:0 0 0 12px rgba(45,158,95,0);}}
.btn-ready{animation:pulse 1.5s ease-in-out 5;}
.btn-go{background:#2d9e5f;border:none;font-size:1rem;}
.btn-go:hover{background:#1a6b3c;}
.btn-go:disabled{background:#9ec9b3;cursor:not-allowed;}
.btn-stop{background:#dc3545;border:none;}

/* table */
#recTable{font-size:.85rem;}
#recTable thead th{background:#1a6b3c;color:#fff;position:sticky;top:0;z-index:1;}
.twrap{max-height:350px;overflow-y:auto;border-radius:0 0 12px 12px;}
.bp {background:#fd7e14!important;}
.bpr{background:#0d6efd!important;animation:blink 1s infinite;}
.bs {background:#198754!important;}
.bf {background:#dc3545!important;}
.bsk{background:#6c757d!important;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}

/* log */
#logBox{background:#1e1e1e;color:#d4d4d4;font-family:'Consolas',monospace;
  font-size:.78rem;border-radius:8px;height:300px;overflow-y:auto;
  padding:10px;white-space:pre-wrap;word-break:break-all;}
.ls{color:#4ec9b0;}.le{color:#f44747;}.lw{color:#dcdcaa;}.li{color:#9cdcfe;}
</style>
</head>
<body>

<nav class="navbar navbar-dark px-4 py-2 mb-3">
  <span class="navbar-brand fw-bold fs-6">
    <i class="bi bi-bank2 me-2"></i>KCC Loan Automation
    <span class="badge bg-success ms-2" style="font-size:.65rem;vertical-align:middle;">V4</span>
    <span class="text-white-50 ms-2" style="font-size:.7rem;font-weight:400;">
      by Kiran Karchi
    </span>
  </span>
  <span class="text-white-50 small d-flex align-items-center gap-3">
    <span id="loggedUser">
      <i class="bi bi-person-circle me-1"></i>
      <span id="loggedName">—</span>
    </span>
    <span class="opacity-25">|</span>
    <a id="urlLink" href="#" class="text-white-50 text-decoration-none small"></a>
    <span class="opacity-25">|</span>
    <a href="/logout" class="text-white-50 text-decoration-none small">
      <i class="bi bi-box-arrow-right me-1"></i>Logout
    </a>
  </span>
</nav>

<div class="container-fluid px-4">

<!-- ── Row 1 : Input + Run ── -->
<div class="row g-3 mb-3">

  <!-- Input card (upload / paste + validation + RUN button all in one place) -->
  <div class="col-lg-5">
    <div class="card h-100">
      <div class="card-header bg-white p-0 border-bottom">
        <ul class="nav nav-tabs px-3 pt-2" id="inputTabs">
          <li class="nav-item">
            <button class="nav-link active" id="tab-file" onclick="switchTab('file')">
              <i class="bi bi-file-earmark-excel-fill text-success me-1"></i>Upload File
            </button>
          </li>
          <li class="nav-item">
            <button class="nav-link" id="tab-paste" onclick="switchTab('paste')">
              <i class="bi bi-clipboard-data text-primary me-1"></i>Paste from Excel
            </button>
          </li>
          <li class="nav-item">
            <button class="nav-link" id="tab-smart" onclick="switchTab('smart')">
              <i class="bi bi-magic text-warning me-1"></i>Smart Format
            </button>
          </li>
        </ul>
      </div>
      <div class="card-body d-flex flex-column">

        <!-- File pane -->
        <div id="pane-file">
          <div id="dropzone" onclick="document.getElementById('fileInput').click()">
            <i class="bi bi-cloud-upload-fill" id="dzIcon"></i>
            <p class="mt-2 mb-1 fw-semibold" id="dzText">Drag &amp; Drop or Click to Upload</p>
            <p class="text-muted small mb-0" id="dzSub">Supports .xlsx / .xls</p>
          </div>
          <input type="file" id="fileInput" accept=".xlsx,.xls"
                 class="d-none" onchange="uploadFile(this.files[0])"/>
        </div>

        <!-- Paste pane -->
        <div id="pane-paste" class="d-none">
          <p class="text-muted small mb-2">
            <i class="bi bi-info-circle-fill text-primary me-1"></i>
            In Excel: select all rows <strong>including the header row</strong>
            → <kbd>Ctrl+C</kbd> → click below → <kbd>Ctrl+V</kbd> → click <strong>Load Data</strong>
          </p>
          <textarea id="pasteArea" class="form-control"
            placeholder="Paste Excel data here (Ctrl+V)…"></textarea>
          <button class="btn btn-primary w-100 mt-2 fw-semibold py-2"
                  onclick="loadPaste()">
            <i class="bi bi-check2-circle me-1"></i>Load Data
          </button>
        </div>

        <!-- Smart Format pane -->
        <div id="pane-smart" class="d-none">
          <p class="text-muted small mb-2">
            <i class="bi bi-magic text-warning me-1"></i>
            Paste data in <strong>any format</strong> — WhatsApp, Excel, space-separated, any date style.
            Click <strong>Auto Clean</strong> and it fixes everything automatically.
          </p>
          <textarea id="smartArea" class="form-control" rows="5"
            style="font-size:.8rem;resize:vertical;"
            placeholder="Paste raw data here in any format...&#10;&#10;Example:&#10;295381719280  27/03/2026  53000  Madagouda Siddappa&#10;300915264220  3/27/2026   49000  Makhabhul K Mulla"></textarea>
          <button class="btn btn-warning w-100 mt-2 fw-semibold py-2 text-dark"
                  onclick="smartClean()">
            <i class="bi bi-magic me-1"></i>Auto Clean &amp; Format
          </button>
          <!-- Preview table -->
          <div id="smartPreview" class="d-none mt-3">
            <div class="d-flex align-items-center justify-content-between mb-2">
              <span class="fw-semibold small text-success">
                <i class="bi bi-check-circle-fill me-1"></i>
                <span id="smartCount"></span> records formatted
              </span>
              <button class="btn btn-success btn-sm fw-semibold"
                      onclick="loadSmart()">
                <i class="bi bi-check2-circle me-1"></i>Load to Automation
              </button>
            </div>
            <div style="max-height:160px;overflow-y:auto;border-radius:8px;border:1px solid #c8e6c9;">
              <table class="table table-sm table-hover mb-0" style="font-size:.75rem;">
                <thead style="background:#1a6b3c;color:#fff;position:sticky;top:0;">
                  <tr>
                    <th>#</th>
                    <th>Aadhar Number</th>
                    <th>Disbursal Date</th>
                    <th>Amount (INR)</th>
                    <th>Beneficiary Name</th>
                  </tr>
                </thead>
                <tbody id="smartTbody"></tbody>
              </table>
            </div>
            <!-- Formatted text (hidden, used for loadPaste) -->
            <textarea id="smartFormatted" class="d-none"></textarea>
          </div>
          <!-- Errors -->
          <div id="smartErrors" class="d-none mt-2 alert alert-danger py-2 px-3 small"></div>
        </div>

        <!-- Validation panel -->
        <div id="validPanel" class="mt-3 d-none">
          <hr class="my-2"/>
          <div class="d-flex align-items-center gap-2 mb-2 flex-wrap">
            <span id="vIcon" class="fs-5"></span>
            <span id="vTitle" class="fw-semibold small"></span>
            <span class="badge bg-secondary ms-auto" id="vRows"></span>
          </div>
          <div id="vChips"></div>
          <div id="vWarn" class="alert alert-warning py-2 px-3 small mt-2 d-none mb-0">
            <i class="bi bi-exclamation-triangle-fill me-1"></i>
            <span id="vWarnMsg"></span>
          </div>
        </div>

        <!-- ── RUN button lives right here, below the file ── -->
        <div class="mt-auto pt-3" id="runArea">
          <button id="btnRun"
                  class="btn btn-go text-white fw-bold w-100 py-3"
                  onclick="startAuto()" disabled
                  style="font-size:1.15rem;letter-spacing:.03em;">
            <i class="bi bi-play-circle-fill me-2"></i>Run Automation
          </button>
          <button id="btnStop"
                  class="btn btn-stop text-white fw-bold w-100 py-3 d-none"
                  onclick="stopAuto()"
                  style="font-size:1.15rem;">
            <i class="bi bi-stop-circle-fill me-2"></i>Stop Automation
          </button>
          <p id="runHint" class="text-muted small text-center mb-0 mt-2">
            <i class="bi bi-arrow-up-circle me-1"></i>Upload or paste data above to enable
          </p>
        </div>

      </div>
    </div>
  </div>

  <!-- Stats cards (right column — numbers only, no button) -->
  <div class="col-lg-7">
    <div class="row g-3">
      <div class="col-6 col-md-4"><div class="sc sc-total h-100">
        <div class="num" id="sT">0</div>
        <div class="lbl"><i class="bi bi-people-fill me-1"></i>Total</div>
      </div></div>
      <div class="col-6 col-md-4"><div class="sc sc-ok h-100">
        <div class="num" id="sS">0</div>
        <div class="lbl"><i class="bi bi-check-circle-fill me-1"></i>Successful</div>
      </div></div>
      <div class="col-6 col-md-4"><div class="sc sc-fail h-100">
        <div class="num" id="sF">0</div>
        <div class="lbl"><i class="bi bi-x-circle-fill me-1"></i>Failed</div>
      </div></div>
      <div class="col-6 col-md-4"><div class="sc sc-pend h-100">
        <div class="num" id="sP">0</div>
        <div class="lbl"><i class="bi bi-clock-fill me-1"></i>Pending</div>
      </div></div>
      <div class="col-6 col-md-4"><div class="sc sc-skip h-100">
        <div class="num" id="sSk">0</div>
        <div class="lbl"><i class="bi bi-skip-forward-fill me-1"></i>Skipped</div>
      </div></div>
      <div class="col-6 col-md-4"><div class="sc h-100" style="background:linear-gradient(135deg,#0d6efd,#084298);">
        <div class="num" id="sFail2">—</div>
        <div class="lbl"><i class="bi bi-activity me-1"></i>Running</div>
      </div></div>
    </div>
  </div>
</div>

<!-- ── Progress ── -->
<div class="mb-3">
  <div class="d-flex justify-content-between small text-muted mb-1">
    <span>Progress</span><span id="progTxt">0 / 0</span>
  </div>
  <div class="progress" style="height:9px;border-radius:8px;">
    <div id="progBar" class="progress-bar bg-success" style="width:0%;transition:width .4s;"></div>
  </div>
</div>

<!-- ── Row 2: Table + Log ── -->
<div class="row g-3 mb-4">
  <div class="col-lg-7">
    <div class="card">
      <div class="card-header bg-white d-flex justify-content-between align-items-center">
        <span><i class="bi bi-table me-2 text-success"></i>Records</span>
        <span class="badge bg-secondary" id="tblCnt">0 rows</span>
      </div>
      <div class="card-body p-0">
        <div class="twrap">
          <table class="table table-hover table-bordered mb-0" id="recTable">
            <thead><tr>
              <th>#</th><th>Beneficiary</th><th>Aadhaar</th>
              <th>Account</th><th>Amount</th><th>Disbursal</th><th>Status</th>
            </tr></thead>
            <tbody id="recBody">
              <tr><td colspan="7" class="text-center text-muted py-5">
                <i class="bi bi-inbox fs-3 d-block mb-2 text-muted"></i>
                Upload a file or paste Excel data to see records
              </td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <div class="col-lg-5">
    <div class="card h-100">
      <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
        <span><i class="bi bi-terminal-fill me-2"></i>Live Log</span>
        <button class="btn btn-outline-light btn-sm py-0 px-2" onclick="clearLog()">
          <i class="bi bi-trash3"></i> Clear
        </button>
      </div>
      <div class="card-body p-2">
        <div id="logBox">Waiting for automation to start…
</div>
      </div>
    </div>
  </div>
</div>

</div><!-- /container -->

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
// ── constants ─────────────────────────────────────────────────────────────
const RCOLS = [
  'Aadhar Number',
  'Loan Disbursal Date',
  'Max Withdrawal Amount (INR)'
];
const OCOLS = [
  'Account Number','Loan Repayment Date','Beneficiary Name'
];

// ── URL display ───────────────────────────────────────────────────────────
document.getElementById('urlLink').textContent = window.location.href;
document.getElementById('urlLink').href = window.location.href;

// ── Show logged-in user name in navbar ────────────────────────────────────
fetch('/whoami').then(r=>r.json()).then(d=>{
  const el = document.getElementById('loggedName');
  if(el && d.username) el.textContent = d.username;
});

// ── Tab switch ────────────────────────────────────────────────────────────
function switchTab(tab) {
  ['file','paste','smart'].forEach(t => {
    document.getElementById('pane-'+t).classList.toggle('d-none', t !== tab);
    document.getElementById('tab-'+t).classList.toggle('active',  t === tab);
  });
  document.getElementById('validPanel').classList.add('d-none');
}

// ── Drag & drop ───────────────────────────────────────────────────────────
const dz = document.getElementById('dropzone');
dz.addEventListener('dragover',  e => { e.preventDefault(); dz.classList.add('drag-over'); });
dz.addEventListener('dragleave', ()  => dz.classList.remove('drag-over'));
dz.addEventListener('drop', e => {
  e.preventDefault();
  dz.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f) uploadFile(f);
});

// ── Upload file ───────────────────────────────────────────────────────────
function uploadFile(file) {
  if (!file) return;
  document.getElementById('dzText').textContent = '⏳ Reading ' + file.name + '…';
  const form = new FormData();
  form.append('file', file);
  fetch('/upload', { method: 'POST', body: form })
    .then(r => r.json())
    .then(d => {
      if (d.error) {
        alert('❌ Upload error:\n' + d.error);
        document.getElementById('dzText').textContent = 'Drag & Drop or Click to Upload';
        return;
      }
      document.getElementById('dzIcon').className = 'bi bi-file-earmark-check-fill text-success';
      document.getElementById('dzText').textContent = '✅ ' + file.name;
      document.getElementById('dzSub').textContent  = d.rows + ' records loaded — click to change';
      applyResult(d, '📂 ' + file.name);
    })
    .catch(e => alert('Upload failed: ' + e));
}

// ── Paste from Excel ──────────────────────────────────────────────────────
function loadPaste() {
  const raw = document.getElementById('pasteArea').value.trim();
  if (!raw) {
    alert('Please paste Excel data first.\n\nIn Excel: select rows including header → Ctrl+C → click in the text area → Ctrl+V → click Load Data.');
    return;
  }
  fetch('/paste', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: raw })
  })
    .then(r => r.json())
    .then(d => {
      if (d.error) { alert('❌ Parse error:\n' + d.error); return; }
      applyResult(d, '📋 Pasted data');
    })
    .catch(e => alert('Paste failed: ' + e));
}

// ── Smart Format Cleaner ──────────────────────────────────────────────────
function smartClean() {
  const raw = document.getElementById('smartArea').value.trim();
  const errDiv  = document.getElementById('smartErrors');
  const prevDiv = document.getElementById('smartPreview');
  errDiv.classList.add('d-none');
  prevDiv.classList.add('d-none');

  if (!raw) { errDiv.textContent = '⚠️ Please paste some data first.'; errDiv.classList.remove('d-none'); return; }

  // ── Detect separator: tab > pipe > 2+ spaces > comma ─────────────────
  const lines = raw.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);
  if (lines.length < 1) { errDiv.textContent = '⚠️ Please paste at least one data row.'; errDiv.classList.remove('d-none'); return; }

  function splitLine(line) {
    // Tab (Excel copy-paste)
    if (line.includes('\t'))  return line.split('\t').map(s => s.trim());
    // Pipe separated
    if (line.includes('|'))   return line.split('|').map(s => s.trim()).filter(s => s);
    // 2+ spaces
    if (/  +/.test(line))     return line.split(/  +/).map(s => s.trim());
    // Comma separated
    if (line.includes(','))   return line.split(',').map(s => s.trim());

    // ── Smart single-space: Aadhar(10-12 digits) + date + amount + name ──
    // Handles: "295381719280 3/27/2026 53000 Madagouda Siddappa Odeyar"
    const m = line.match(/^(\d{10,12})\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}[\/\-]\d{2}[\/\-]\d{2})\s+(\d+)\s*(.+)?$/);
    if (m) return [m[1].trim(), m[2].trim(), m[3].trim(), (m[4]||'').trim()];

    // Fallback: split on any whitespace
    return line.split(/\s+/).map(s => s.trim()).filter(s => s);
  }

  // ── Auto-convert date to DD/MM/YYYY ──────────────────────────────────
  function fixDate(val) {
    val = val.trim();
    if (!val) return val;

    // Slash-separated: d/m/yyyy  or  m/d/yyyy
    if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(val)) {
      const p = val.split('/');
      const a = parseInt(p[0]), b = parseInt(p[1]);
      // b > 12  → b is definitely the DAY  → US format M/D/YYYY  e.g. 3/27/2026
      if (b > 12) return p[1].padStart(2,'0') + '/' + p[0].padStart(2,'0') + '/' + p[2];
      // a > 12  → a is definitely the DAY  → Indian DD/MM/YYYY  e.g. 27/03/2026
      if (a > 12) return p[0].padStart(2,'0') + '/' + p[1].padStart(2,'0') + '/' + p[2];
      // Both ≤ 12 → ambiguous → keep as-is (assume DD/MM/YYYY Indian format)
      return p[0].padStart(2,'0') + '/' + p[1].padStart(2,'0') + '/' + p[2];
    }
    // Hyphen-separated: d-m-yyyy  or  m-d-yyyy
    if (/^\d{1,2}-\d{1,2}-\d{4}$/.test(val)) {
      const p = val.split('-');
      const a = parseInt(p[0]), b = parseInt(p[1]);
      if (b > 12) return p[1].padStart(2,'0') + '/' + p[0].padStart(2,'0') + '/' + p[2];
      if (a > 12) return p[0].padStart(2,'0') + '/' + p[1].padStart(2,'0') + '/' + p[2];
      return p[0].padStart(2,'0') + '/' + p[1].padStart(2,'0') + '/' + p[2];
    }
    // ISO: YYYY-MM-DD
    if (/^\d{4}-\d{2}-\d{2}$/.test(val)) {
      const p = val.split('-'); return p[2] + '/' + p[1] + '/' + p[0];
    }
    return val; // unknown format — pass through as-is
  }

  // ── Map header names flexibly ─────────────────────────────────────────
  function mapHeader(h) {
    h = h.toLowerCase().replace(/[^a-z0-9]/g,' ').trim();
    if (/aadh|adh/.test(h))         return 'Aadhar Number';
    if (/date|disbursal|disb/.test(h)) return 'Loan Disbursal Date';
    if (/amount|amt|withdrawal|max|inr/.test(h)) return 'Max Withdrawal Amount (INR)';
    if (/name|beneficiary|farmer|benef/.test(h)) return 'Beneficiary Name';
    if (/account|acc/.test(h))       return 'Account Number';
    if (/repay|repayment/.test(h))   return 'Loan Repayment Date';
    return null;
  }

  // ── Parse header row ──────────────────────────────────────────────────
  const headerCols = splitLine(lines[0]);
  const colMap = headerCols.map(mapHeader);
  const hasHeader = colMap.some(c => c !== null);

  let dataLines = hasHeader ? lines.slice(1) : lines;
  // If no header detected, assume fixed order: Aadhar, Date, Amount, Name
  const fixedOrder = ['Aadhar Number','Loan Disbursal Date','Max Withdrawal Amount (INR)','Beneficiary Name'];
  const effectiveCols = hasHeader ? colMap : fixedOrder;

  const rows = [];
  const errors = [];

  dataLines.forEach((line, i) => {
    if (!line.trim()) return;
    const cells = splitLine(line);
    const rec = {};
    effectiveCols.forEach((col, ci) => {
      if (!col) return;
      let val = (cells[ci] || '').trim();
      if (col === 'Loan Disbursal Date' || col === 'Loan Repayment Date') val = fixDate(val);
      if (col === 'Max Withdrawal Amount (INR)') val = val.replace(/[^0-9.]/g,'');
      if (col === 'Aadhar Number') val = val.replace(/[^0-9]/g,'');
      rec[col] = val;
    });
    // Validate essentials
    if (!rec['Aadhar Number'] || rec['Aadhar Number'].length < 10) {
      errors.push('Row '+(i+1)+': Invalid Aadhar Number — '+line.substring(0,40));
      return;
    }
    rows.push(rec);
  });

  if (errors.length > 0 && rows.length === 0) {
    errDiv.innerHTML = '<b>⚠️ Could not parse data:</b><br>' + errors.join('<br>');
    errDiv.classList.remove('d-none'); return;
  }

  // ── Build preview table ───────────────────────────────────────────────
  const tbody = document.getElementById('smartTbody');
  tbody.innerHTML = rows.map((r,i) => `
    <tr>
      <td class="text-muted">${i+1}</td>
      <td><code>${r['Aadhar Number']||'—'}</code></td>
      <td>${r['Loan Disbursal Date']||'—'}</td>
      <td>₹${Number(r['Max Withdrawal Amount (INR)']||0).toLocaleString('en-IN')}</td>
      <td>${r['Beneficiary Name']||'—'}</td>
    </tr>`).join('');
  document.getElementById('smartCount').textContent = rows.length;

  // ── Build formatted TSV for loadPaste ────────────────────────────────
  const allCols = ['Aadhar Number','Loan Disbursal Date','Max Withdrawal Amount (INR)','Beneficiary Name','Account Number','Loan Repayment Date'];
  const usedCols = allCols.filter(c => rows.some(r => r[c]));
  const tsv = [usedCols.join('\t'), ...rows.map(r => usedCols.map(c => r[c]||'').join('\t'))].join('\n');
  document.getElementById('smartFormatted').value = tsv;

  prevDiv.classList.remove('d-none');
  if (errors.length > 0) {
    errDiv.innerHTML = '<b>⚠️ Skipped '+errors.length+' row(s):</b><br>' + errors.join('<br>');
    errDiv.classList.remove('d-none');
  }
}

// ── Load smart-formatted data into automation ─────────────────────────────
function loadSmart() {
  const tsv = document.getElementById('smartFormatted').value;
  if (!tsv) return;
  fetch('/paste', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: tsv })
  })
    .then(r => r.json())
    .then(d => {
      if (d.error) { alert('❌ Load error:\n' + d.error); return; }
      applyResult(d, '🧹 Smart formatted data');
      switchTab('file'); // go back to main view
    })
    .catch(e => alert('Load failed: ' + e));
}

// ── After successful load ─────────────────────────────────────────────────
function applyResult(d, label) {
  showValidation(d, label);
  renderTable(d.records);
  updateSummary(d.summary);
}

// ── Validation display ────────────────────────────────────────────────────
function showValidation(d, label) {
  const found = d.columns_found   || [];
  const miss  = d.columns_missing || [];
  document.getElementById('validPanel').classList.remove('d-none');
  document.getElementById('vRows').textContent = (d.rows || 0) + ' records';
  // Required columns (green=found, red=missing)
  const reqChips = RCOLS.map(c => {
    const ok = found.includes(c);
    return `<span class="chip ${ok ? 'chip-ok' : 'chip-miss'}">
      <i class="bi bi-${ok ? 'check-circle-fill' : 'x-circle-fill'}"></i>${c}</span>`;
  });
  // Optional columns (green=found, grey=not present — no error)
  const optChips = OCOLS.map(c => {
    const ok = found.includes(c);
    return ok ? `<span class="chip chip-ok">
      <i class="bi bi-check-circle-fill"></i>${c}</span>` : '';
  });
  document.getElementById('vChips').innerHTML = reqChips.join('') + optChips.join('');
  if (miss.length === 0) {
    document.getElementById('vIcon').textContent  = '✅';
    document.getElementById('vTitle').textContent = label + ' — Format OK!';
    document.getElementById('vWarn').classList.add('d-none');
    enableRunButton(d.rows);
  } else {
    document.getElementById('vIcon').textContent  = '⚠️';
    document.getElementById('vTitle').textContent = label + ' — Missing columns';
    document.getElementById('vWarn').classList.remove('d-none');
    document.getElementById('vWarnMsg').textContent = 'Missing: ' + miss.join(', ');
    // Still enable button (missing cols are non-fatal, script will handle them)
    enableRunButton(d.rows);
  }
}

function enableRunButton(rows) {
  const btn = document.getElementById('btnRun');
  btn.disabled = false;
  btn.innerHTML = '<i class="bi bi-play-circle-fill me-2"></i>▶  Run Automation  (' + (rows || 0) + ' records)';
  btn.classList.add('btn-ready');
  document.getElementById('runHint').innerHTML =
    '<i class="bi bi-check-circle-fill text-success me-1"></i>' +
    (rows || 0) + ' records ready &mdash; click the button above to start';
  document.getElementById('sFail2').textContent = 'Ready';
  setTimeout(() => btn.classList.remove('btn-ready'), 8000);
}

// ── Table ─────────────────────────────────────────────────────────────────
function renderTable(recs) {
  if (!recs || !recs.length) return;
  document.getElementById('tblCnt').textContent = recs.length + ' rows';
  document.getElementById('recBody').innerHTML = recs.map((r, i) => `
    <tr id="rw${i}">
      <td class="text-muted fw-bold">${i + 1}</td>
      <td>${r.name || '—'}</td>
      <td class="font-monospace small">${r.aadhaar || '—'}</td>
      <td>${r.account || '—'}</td>
      <td>${r.amount ? '₹' + Number(r.amount).toLocaleString('en-IN') : '—'}</td>
      <td>${r.disbursal || '—'}</td>
      <td id="st${i}"><span class="badge bp">Pending</span></td>
    </tr>`).join('');
}

function setRowStatus(i, s) {
  const el = document.getElementById('st' + i);
  if (!el) return;
  const map = {
    pending:    'bp Pending',
    processing: 'bpr Processing…',
    success:    'bs ✅ Done',
    failed:     'bf ❌ Failed',
    skipped:    'bsk ⏭ Skipped'
  };
  const [cls, ...rest] = (map[s] || 'bp ' + s).split(' ');
  el.innerHTML = `<span class="badge ${cls}">${rest.join(' ')}</span>`;
  if (s === 'processing')
    document.getElementById('rw' + i)
      ?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ── Summary ───────────────────────────────────────────────────────────────
function updateSummary(s) {
  if (!s) return;
  document.getElementById('sT').textContent  = s.total   || 0;
  document.getElementById('sS').textContent  = s.success || 0;
  document.getElementById('sF').textContent  = s.failed  || 0;
  document.getElementById('sP').textContent  = s.pending || 0;
  document.getElementById('sSk').textContent = s.skipped || 0;
  const done  = (s.success || 0) + (s.failed || 0) + (s.skipped || 0);
  const total = Math.max(s.total || 1, 1);
  document.getElementById('progBar').style.width = Math.round(done / total * 100) + '%';
  document.getElementById('progTxt').textContent = done + ' / ' + total;
}

// ── Log ───────────────────────────────────────────────────────────────────
let autoScroll = true;
const lb = document.getElementById('logBox');
lb.addEventListener('scroll', () => {
  autoScroll = lb.scrollTop + lb.clientHeight >= lb.scrollHeight - 30;
});
function appendLog(t) {
  const s = document.createElement('span');
  t = t || '';
  if      (/saved successfully|✅|✓|Selected '/.test(t))                  s.className = 'ls';
  else if (/ERROR on record|❌|Fatal|Browser connection lost/.test(t))     s.className = 'le';
  else if (/SKIPPED record/.test(t))                                        s.className = 'bsk'; // grey
  else if (/WARNING|⚠|manually|auto-continuing|auto-select failed/.test(t))s.className = 'lw';
  else if (/Record \d+\/\d+|─|RESIDENTIAL|Financial|Activity|PROCESSING/.test(t)) s.className = 'li';
  s.textContent = t + '\n';
  lb.appendChild(s);
  if (autoScroll) lb.scrollTop = lb.scrollHeight;
}
function clearLog() { lb.innerHTML = ''; }

// ── SSE stream ────────────────────────────────────────────────────────────
let es = null;
let streamDone = false;

function startStream() {
  if (es) { es.close(); es = null; }
  streamDone = false;
  es = new EventSource('/stream');

  es.onmessage = e => {
    try {
      const d = JSON.parse(e.data);
      if (d.type === 'heartbeat') return;   // keep-alive ping, ignore
      if (d.type === 'log')     appendLog(d.text);
      if (d.type === 'status')  setRowStatus(d.idx, d.status);
      if (d.type === 'summary') updateSummary(d.summary);
      if (d.type === 'done' && !streamDone) {
        streamDone = true;
        appendLog('\n══ Automation finished ══\n');
        const btn = document.getElementById('btnRun');
        btn.disabled = false;
        btn.classList.remove('d-none');
        document.getElementById('btnStop').classList.add('d-none');
        document.getElementById('runHint').innerHTML =
          '<i class="bi bi-check2-all text-success me-1"></i>Finished — click above to run again';
        document.getElementById('sFail2').textContent = 'Done';
      }
    } catch(err) {}
  };

  // ── Reconnect on error with backoff ──────────────────────────────────
  let reconnectDelay = 2000;
  es.onerror = () => {
    es.close(); es = null;
    appendLog('⚠️ Stream disconnected — reconnecting in ' + (reconnectDelay/1000) + 's…\n');
    setTimeout(() => {
      if (!streamDone) startStream();
    }, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, 15000); // max 15s backoff
  };
}

// ── Auto-connect on page load if run is already in progress ──────────────
window.addEventListener('DOMContentLoaded', () => {
  fetch('/status')
    .then(r => r.json())
    .then(d => {
      if (d.running) {
        // Show stop button
        document.getElementById('btnRun').classList.add('d-none');
        document.getElementById('btnStop').classList.remove('d-none');
        document.getElementById('runHint').innerHTML =
          '<i class="bi bi-hourglass-split me-1 text-warning"></i>Running — reconnected to live stream';
        appendLog('🔄 Reconnected to running automation…\n');
        // Restore statuses and summary
        if (d.statuses) Object.entries(d.statuses).forEach(([i,s]) => setRowStatus(Number(i), s));
        if (d.summary)  updateSummary(d.summary);
        startStream();
      }
    })
    .catch(() => {});
});

// ── Start / Stop ──────────────────────────────────────────────────────────
function startAuto() {
  clearLog();
  appendLog('🚀 Starting automation…\n');
  const btn  = document.getElementById('btnRun');
  const stop = document.getElementById('btnStop');
  btn.classList.add('d-none');
  stop.classList.remove('d-none');
  document.getElementById('runHint').innerHTML =
    '<i class="bi bi-hourglass-split me-1 text-warning"></i>Running — do not close this window';
  document.getElementById('sFail2').textContent = '●';
  fetch('/start', { method: 'POST' })
    .then(r => r.json())
    .then(d => {
      if (d.error) {
        alert('❌ ' + d.error);
        btn.disabled = false;
        btn.classList.remove('d-none');
        stop.classList.add('d-none');
        document.getElementById('runHint').innerHTML =
          '<i class="bi bi-exclamation-triangle-fill text-danger me-1"></i>' + d.error;
        return;
      }
      startStream();
    })
    .catch(e => {
      alert('Start failed: ' + e);
      btn.disabled = false;
      btn.classList.remove('d-none');
      stop.classList.add('d-none');
    });
}

function stopAuto() {
  if (!confirm('Stop the automation?')) return;
  fetch('/stop', { method: 'POST' }).then(() => {
    appendLog('\n⛔ Stopped by user.\n');
    document.getElementById('btnStop').classList.add('d-none');
    const btn = document.getElementById('btnRun');
    btn.disabled = false;
    btn.classList.remove('d-none');
    document.getElementById('runHint').innerHTML =
      '<i class="bi bi-stop-circle text-danger me-1"></i>Stopped — click above to run again';
    document.getElementById('sFail2').textContent = 'Stopped';
  });
}
</script>
</body>
</html>
"""

# ─── Helpers ─────────────────────────────────────────────────────────────────
def mask_aadhaar(a):
    s = str(a).replace(".0", "").strip()
    return "*" * (len(s) - 4) + s[-4:] if len(s) > 4 else s


def build_summary():
    st = state["statuses"]
    total = len(state["records"])
    ok  = sum(1 for v in st.values() if v == "success")
    fl  = sum(1 for v in st.values() if v == "failed")
    sk  = sum(1 for v in st.values() if v == "skipped")
    s = {"total": total, "success": ok, "failed": fl,
         "skipped": sk, "pending": max(total - ok - fl - sk, 0)}
    state["summary"] = s
    return s


def parse_df_to_records(df):
    cm = {
        "Aadhar Number":           "AadhaarNumber",
        "Account Number":          "AccountNumber",
        "Loan Disbursal Date":     "DisbursementDate",
        "Loan Repayment Date":     "RepaymentDate",
        "Max Withdrawal Amount (INR)": "LoanAmount",
        "Beneficiary Name":        "BeneficiaryName",
    }
    df2 = df.rename(columns={k: v for k, v in cm.items() if k in df.columns})
    recs = []
    for _, row in df2.iterrows():
        aad = str(row.get("AadhaarNumber", "")).replace(".0", "").strip()
        amt = ""
        try:
            raw = row.get("LoanAmount", "")
            if raw not in ("", "nan", None):
                amt = str(int(float(str(raw))))
        except:
            pass
        disb = row.get("DisbursementDate", "")
        if hasattr(disb, "strftime"):
            disb = disb.strftime("%d/%m/%Y")
        recs.append({
            "name":     str(row.get("BeneficiaryName", "")).strip() or "—",
            "aadhaar":  mask_aadhaar(aad) if aad else "—",
            "account":  str(row.get("AccountNumber", "")).replace(".0", "").strip() or "—",
            "amount":   amt,
            "disbursal": str(disb) if disb not in ("", "nan") else "—",
        })
    return recs


def validate_cols(df):
    all_known = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
    found   = [c for c in all_known if c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]  # only required matter
    return found, missing


def init_state_from_df(df):
    # Always write to a brand-new temp file in the OS temp directory.
    # This is guaranteed to never conflict with any Excel-locked file.
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx", prefix="kcc_loans_")
    os.close(tmp_fd)                          # close the raw fd; openpyxl will reopen
    df.to_excel(tmp_path, index=False, engine="openpyxl")

    # Clean up previous temp file if any
    old = state.get("save_path")
    if old and old != tmp_path:
        try: os.remove(old)
        except: pass

    state["save_path"] = tmp_path
    state["records"]   = parse_df_to_records(df)
    state["statuses"]  = {i: "pending" for i in range(len(state["records"]))}
    return build_summary()


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        pwd = request.form.get("password", "")
        ip  = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        ua  = request.headers.get("User-Agent", "unknown")[:80]
        now = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")

        username = request.form.get("username", "Unknown")
        if pwd == DASHBOARD_PASSWORD:
            session["authenticated"] = True
            session["username"]      = username
            # ── Notify owner on successful login ──────────────────────
            msg = (
                f"✅ <b>KCC Dashboard — Login</b>\n\n"
                f"👤 Name   : <b>{username}</b>\n"
                f"🕐 Time   : {now}\n"
                f"🌐 IP     : {ip}\n"
                f"📱 Device : {ua}\n\n"
                f"🔑 Admin  : {OWNER_NAME}"
            )
            threading.Thread(target=send_telegram, args=(msg,), daemon=True).start()
            return redirect("/")
        else:
            # ── Notify owner on failed login attempt ──────────────────
            msg = (
                f"❌ <b>FAILED Login Attempt</b>\n\n"
                f"👤 Name   : {username}\n"
                f"🕐 Time   : {now}\n"
                f"🌐 IP     : {ip}\n"
                f"📱 Device : {ua}"
            )
            threading.Thread(target=send_telegram, args=(msg,), daemon=True).start()
            error = "Wrong password — try again"
    return render_template_string(LOGIN_HTML, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
@login_required
def index():
    return render_template_string(HTML)


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file provided"})
    try:
        df = pd.read_excel(f, engine="openpyxl")
        found, missing = validate_cols(df)
        summary = init_state_from_df(df)
        return jsonify({
            "rows": len(df),
            "records": state["records"],
            "summary": summary,
            "columns_found": found,
            "columns_missing": missing,
        })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/paste", methods=["POST"])
@login_required
def paste():
    try:
        body = request.get_json(force=True) or {}
        raw  = (body.get("data") or "").strip()
        if not raw:
            return jsonify({"error": "No data received — paste Excel rows including header"})

        # TSV parse (Excel Ctrl+C produces tab-separated values)
        df = pd.read_csv(io.StringIO(raw), sep="\t", dtype=str,
                         engine="python").fillna("")

        # Try numeric conversion per column (non-destructive)
        for col in df.columns:
            try:
                converted = pd.to_numeric(df[col], errors="coerce")
                if converted.notna().mean() > 0.5:   # >50 % numeric → convert
                    df[col] = converted.where(converted.notna(), df[col])
            except:
                pass

        found, missing = validate_cols(df)
        summary = init_state_from_df(df)
        return jsonify({
            "rows": len(df),
            "records": state["records"],
            "summary": summary,
            "columns_found": found,
            "columns_missing": missing,
        })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/start", methods=["POST"])
@login_required
def start():
    if state["running"]:
        return jsonify({"error": "Already running — stop first"})
    if not state["records"]:
        return jsonify({"error": "No data loaded — upload a file or paste data first"})
    if not os.path.exists(SCRIPT_PATH):
        return jsonify({"error": f"Script not found: {SCRIPT_PATH}"})

    state["statuses"] = {i: "pending" for i in range(len(state["records"]))}
    state["running"]  = True

    # Flush log queue and clear buffer
    while not state["log_queue"].empty():
        try: state["log_queue"].get_nowait()
        except: pass
    state["log_buffer"] = []

    def _emit(msg):
        """Put message in live queue AND replay buffer."""
        state["log_queue"].put(msg)
        state["log_buffer"].append(msg)
        if len(state["log_buffer"]) > 500:
            state["log_buffer"] = state["log_buffer"][-500:]

    def _run():
        try:
            proc = subprocess.Popen(
                [sys.executable, "-u", SCRIPT_PATH, state.get("save_path", UPLOAD_PATH)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=BASE_DIR,
            )
            state["process"] = proc
            cur = [0]
            for line in iter(proc.stdout.readline, ""):
                line = line.rstrip()
                if not line:
                    continue
                _emit(json.dumps({"type": "log", "text": line}))

                # ── V3 log patterns ──────────────────────────────────────────
                # Record header:  "  Record 2/10  |  MALAPPA MADHAPPA HUDEDAR"
                m = re.search(r'Record\s+(\d+)/\d+', line)
                if m:
                    try:
                        idx = int(m.group(1)) - 1
                        cur[0] = idx
                        state["statuses"][idx] = "processing"
                        _emit(json.dumps({"type": "status", "idx": idx, "status": "processing"}))
                        _emit(json.dumps({"type": "summary", "summary": build_summary()}))
                    except:
                        pass

                # Success:  "  Record 2 saved successfully!"
                if "saved successfully" in line or "SUBMITTED" in line:
                    state["statuses"][cur[0]] = "success"
                    _emit(json.dumps({"type": "status", "idx": cur[0], "status": "success"}))
                    _emit(json.dumps({"type": "summary", "summary": build_summary()}))

                # Skipped:  "  SKIPPED record 2: Aadhaar …"
                ms = re.search(r'SKIPPED record\s+(\d+)', line)
                if ms:
                    try:
                        sidx = int(ms.group(1)) - 1
                        state["statuses"][sidx] = "skipped"
                        _emit(json.dumps({"type": "status", "idx": sidx, "status": "skipped"}))
                        _emit(json.dumps({"type": "summary", "summary": build_summary()}))
                    except:
                        pass

                # Error:    "  ERROR on record 2: …"
                me = re.search(r'ERROR on record\s+(\d+)', line)
                if me:
                    try:
                        eidx = int(me.group(1)) - 1
                        state["statuses"][eidx] = "failed"
                        _emit(json.dumps({"type": "status", "idx": eidx, "status": "failed"}))
                        _emit(json.dumps({"type": "summary", "summary": build_summary()}))
                    except:
                        pass
            proc.wait()
        except Exception as e:
            _emit(json.dumps({"type": "log", "text": f"❌ Runner error: {e}"}))
        finally:
            state["running"] = False
            state["process"] = None
            _emit(json.dumps({"type": "done"}))

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"ok": True})


@app.route("/stop", methods=["POST"])
@login_required
def stop():
    p = state.get("process")
    if p:
        try: p.terminate()
        except: pass
    state["running"] = False
    state["log_queue"].put(json.dumps({"type": "done"}))
    state["log_buffer"].append(json.dumps({"type": "done"}))
    return jsonify({"ok": True})


@app.route("/stream")
def stream():
    """SSE endpoint — no @login_required so EventSource works through Cloudflare tunnel.
    On connect: replay buffered messages first, then stream live updates."""
    def _gen():
        # ── 1. Replay buffer so reconnects / page refreshes get all past logs ──
        buf_snapshot = list(state["log_buffer"])
        for msg in buf_snapshot:
            yield f"data: {msg}\n\n"

        # ── 2. Stream live messages ───────────────────────────────────────────
        while True:
            try:
                msg = state["log_queue"].get(timeout=20)
                yield f"data: {msg}\n\n"
                # After 'done', keep connection alive for heartbeats (don't break)
            except queue.Empty:
                yield 'data: {"type":"heartbeat"}\n\n'

    return Response(
        _gen(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.route("/ping")
def ping():
    return jsonify({"ok": True})


@app.route("/status")
@login_required
def status():
    """Return current run state so page-load can auto-reconnect to stream."""
    return jsonify({
        "running":  state["running"],
        "statuses": state["statuses"],
        "summary":  state["summary"],
        "records":  state["records"],
        "buffered": len(state["log_buffer"]),
    })


@app.route("/whoami")
@login_required
def whoami():
    return jsonify({"username": session.get("username", "—")})


# ─── Entry point ─────────────────────────────────────────────────────────────
def _find_free_port(start=5000, tries=5):
    for p in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", p))
                return p
            except OSError:
                continue
    return start


def _get_local_ip():
    """Return the LAN IP of this machine (e.g. 192.168.x.x)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def _get_cloudflared_exe():
    """
    Return path to cloudflared.exe — auto-download on first run if missing.
    If download is blocked by firewall, user can manually place the file in the PRI folder.
    """
    import urllib.request, stat
    exe = os.path.join(BASE_DIR, "cloudflared.exe")
    if os.path.exists(exe):
        return exe

    print("  ⏳  Downloading cloudflared.exe (one-time, ~35 MB) ...")
    urls = [
        "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe",
        "https://objects.githubusercontent.com/github-production-release-asset-2e65be/232609078/cloudflared-windows-amd64.exe",
    ]
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
    opener.addheaders = [("User-Agent", "Mozilla/5.0")]
    urllib.request.install_opener(opener)

    for url in urls:
        try:
            urllib.request.urlretrieve(url, exe)
            if os.path.getsize(exe) > 1_000_000:   # must be > 1 MB to be valid
                os.chmod(exe, os.stat(exe).st_mode | stat.S_IEXEC)
                print("  ✅  cloudflared.exe downloaded")
                return exe
        except Exception as e:
            print(f"  ⚠  Download attempt failed: {e}")

    # Clean up partial download
    try: os.remove(exe)
    except: pass

    print()
    print("  ⚠  Auto-download blocked by network/firewall.")
    print("  👉  Manual fix — download this file on your MOBILE and transfer to PC:")
    print("      https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe")
    print(f"      Save it as:  {exe}")
    print("      Then restart dashboard.py")
    print()
    return None


def _start_cloudflared(port):
    """Cloudflare Quick Tunnel — most reliable free public tunnel."""
    exe = _get_cloudflared_exe()
    if not exe:
        return None
    result = {"url": None}

    def _run():
        try:
            proc = subprocess.Popen(
                [exe, "tunnel", "--url", f"http://localhost:{port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            state["tunnel_proc"] = proc
            for line in proc.stdout:
                m = re.search(r'https://[\w\-]+\.trycloudflare\.com', line)
                if m:
                    result["url"] = m.group(0)
                    return
        except Exception as e:
            print(f"  ⚠  cloudflared error: {e}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=30)
    return result["url"]


def _start_ngrok(port):
    """ngrok tunnel — uses static domain + auth token if configured."""
    try:
        from pyngrok import ngrok as _ngrok, conf as _conf
        if NGROK_AUTH_TOKEN:
            _conf.get_default().auth_token = NGROK_AUTH_TOKEN
        if NGROK_STATIC_DOMAIN:
            tunnel = _ngrok.connect(port, "http", hostname=NGROK_STATIC_DOMAIN)
        else:
            tunnel = _ngrok.connect(port, "http")
        return tunnel.public_url
    except ImportError:
        print("  ⚠  pyngrok not installed — run:  pip install pyngrok")
        return None
    except Exception as e:
        print(f"  ⚠  ngrok error: {e}")
        return None


if __name__ == "__main__":
    PORT     = _find_free_port(5000)
    LOCAL_IP = _get_local_ip()

    LOCAL_URL = f"http://localhost:{PORT}"
    LAN_URL   = f"http://{LOCAL_IP}:{PORT}"

    # ── 1. ngrok with static domain (permanent URL — configure above) ─────────
    if NGROK_AUTH_TOKEN and NGROK_STATIC_DOMAIN:
        print()
        print(f"  ⏳  Starting ngrok tunnel  →  https://{NGROK_STATIC_DOMAIN} ...")
        PUBLIC_URL = _start_ngrok(PORT)
    else:
        PUBLIC_URL = None

    # ── 2. Cloudflare Quick Tunnel (auto-downloads exe, random URL) ───────────
    if not PUBLIC_URL:
        print()
        print("  ⏳  Starting Cloudflare tunnel ...")
        PUBLIC_URL = _start_cloudflared(PORT)

    # ── 3. Last resort: ngrok without static domain ───────────────────────────
    if not PUBLIC_URL and NGROK_AUTH_TOKEN:
        print("  ⚠  Cloudflare failed — trying ngrok ...")
        PUBLIC_URL = _start_ngrok(PORT)

    print()
    print("=" * 68)
    print("  ✅  KCC LOAN AUTOMATION DASHBOARD  —  V3")
    print("=" * 68)
    print(f"  💻  This PC only      →  {LOCAL_URL}")
    print(f"  📡  Same WiFi / LAN   →  {LAN_URL}")
    if PUBLIC_URL:
        print(f"  🌍  Mobile / any net  →  {PUBLIC_URL}")
        print()
        print(f"       ↑  Open this on any phone or laptop — bookmark it!")
    else:
        print()
        print("  🌍  Tunnel failed. Check internet connection and restart.")
    print()
    print("  • Keep this terminal open while others are using the dashboard")
    print("  • Press Ctrl+C to stop")
    print("=" * 68)
    print()

    def _open():
        time.sleep(2)
        try:
            webbrowser.open(LOCAL_URL)
        except:
            pass

    threading.Thread(target=_open, daemon=True).start()

    # Bind to 0.0.0.0 so LAN + tunnel traffic can reach Flask
    app.run(debug=False, host="0.0.0.0", port=PORT, threaded=True)
