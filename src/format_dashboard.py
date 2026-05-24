"""
KCC Data Formatter Dashboard
Standalone tool — only for formatting farmer data.
No Chrome, no Selenium, no VNC needed.
Run: python src/format_dashboard.py
URL: http://localhost:5001
"""

import sys, os, secrets, datetime, io
import urllib.request, urllib.parse
from functools import wraps
from flask import Flask, render_template_string, request, jsonify, session, redirect, Response
import pandas as pd

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

DASHBOARD_PASSWORD  = os.environ.get("DASHBOARD_PASSWORD", "kcc@2026")
TELEGRAM_BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID    = os.environ.get("TELEGRAM_CHAT_ID", "")
OWNER_NAME          = "Kiran Karchi"

# ── Telegram ──────────────────────────────────────────────────────────────────
def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url  = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": msg,
                                       "parse_mode": "HTML"}).encode()
        urllib.request.urlopen(url, data, timeout=5)
    except Exception as e:
        print(f"Telegram failed: {e}")

import threading

# ── Login required ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────────────────────────────────────────
# HTML
# ─────────────────────────────────────────────────────────────────────────────
LOGIN_HTML = """
<!doctype html><html lang="en"><head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>KCC Formatter — Login</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"/>
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet"/>
<style>
body{background:linear-gradient(135deg,rgba(10,40,18,.75),rgba(20,100,55,.65)),
  url('https://images.unsplash.com/photo-1625246333195-78d9c38ad449?auto=format&fit=crop&w=1920&q=80')
  center/cover no-repeat fixed;
  min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;padding:20px;}
.card{border:none;border-radius:20px;box-shadow:0 16px 48px rgba(0,0,0,.3);width:100%;max-width:420px;overflow:hidden;}
.hdr{background:linear-gradient(135deg,#0f4c2a,#1a6b3c);color:#fff;text-align:center;padding:24px 20px 16px;}
.hdr .logo{font-size:2rem;} .hdr h4{font-weight:800;margin:0;}
.hdr .sub{opacity:.8;font-size:.8rem;margin-top:4px;}
.team-strip{background:#f8fdf9;border-bottom:1px solid #e0f0e8;padding:10px 16px;
  display:flex;gap:8px;flex-wrap:wrap;justify-content:center;}
.chip{display:inline-flex;align-items:center;gap:5px;background:#fff;border:1px solid #c8e6c9;
  border-radius:20px;padding:3px 10px;font-size:.72rem;color:#1a6b3c;font-weight:600;}
.chip .role{color:#888;font-weight:400;font-size:.68rem;}
.body{padding:20px;}
.form-select,.form-control{border-radius:10px;border:1.5px solid #dee2e6;padding:9px 12px;}
.form-select:focus,.form-control:focus{border-color:#2d9e5f;box-shadow:0 0 0 3px rgba(45,158,95,.15);}
.btn-login{background:linear-gradient(90deg,#1a6b3c,#2d9e5f);border:none;border-radius:10px;
  font-weight:700;padding:11px;}
.footer{text-align:center;color:rgba(255,255,255,.75);font-size:.75rem;margin-top:14px;line-height:1.8;}
.footer strong{color:#fff;}
.badge-tool{background:rgba(255,255,255,.15);border-radius:20px;padding:2px 10px;
  font-size:.7rem;letter-spacing:.5px;}
</style></head><body>
<div class="card">
  <div class="hdr">
    <div class="logo">📋</div>
    <h4>KCC Data Formatter</h4>
    <span class="badge-tool">FORMAT TOOL</span>
    <div class="sub mt-1">Kagwad Block · Belagavi · Karnataka</div>
  </div>
  <div class="team-strip">
    <span class="chip"><i class="bi bi-shield-fill-check text-success"></i>Kiran Karchi<span class="role ms-1">Owner</span></span>
    <span class="chip"><i class="bi bi-person-badge text-primary"></i>Mahanthesh Hiremath<span class="role ms-1">Manager</span></span>
    <span class="chip"><i class="bi bi-person text-secondary"></i>Mahadev Vadeyar<span class="role ms-1">Co-ordinator</span></span>
    <span class="chip"><i class="bi bi-person text-secondary"></i>Avinash Dugnavar<span class="role ms-1">Co-ordinator</span></span>
  </div>
  <div class="body">
    {% if error %}
    <div class="alert alert-danger py-2 text-center small mb-3">
      <i class="bi bi-exclamation-triangle-fill me-1"></i>{{ error }}
    </div>{% endif %}
    <form method="POST" action="/login">
      <div class="mb-3">
        <label class="form-label fw-semibold small text-muted"><i class="bi bi-person-circle me-1"></i>Select Your Name</label>
        <select name="username" class="form-select" required>
          <option value="" disabled selected>-- Select your name --</option>
          <option value="Kiran Karchi">👑 Kiran Karchi (Owner)</option>
          <option value="Mahanthesh Hiremath">🗂️ Mahanthesh Hiremath (Manager)</option>
          <option value="Mahadev Vadeyar">📋 Mahadev Vadeyar (Co-ordinator)</option>
          <option value="Avinash Dugnavar">📋 Avinash Dugnavar (Co-ordinator)</option>
        </select>
      </div>
      <div class="mb-4">
        <label class="form-label fw-semibold small text-muted"><i class="bi bi-lock-fill me-1"></i>Password</label>
        <input type="password" name="password" class="form-control" placeholder="Enter password" required/>
      </div>
      <button type="submit" class="btn btn-login text-white w-100">
        <i class="bi bi-box-arrow-in-right me-2"></i>Open Formatter
      </button>
    </form>
  </div>
</div>
<div class="footer"><strong>© 2026 Kiran Karchi</strong> &nbsp;|&nbsp; KCC Automation Project<br/>Kagwad Block &nbsp;·&nbsp; Belagavi &nbsp;·&nbsp; Karnataka</div>
</body></html>
"""

MAIN_HTML = r"""
<!doctype html><html lang="en"><head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>KCC Data Formatter</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"/>
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet"/>
<style>
body{
  background:linear-gradient(135deg,rgba(10,40,18,.55),rgba(20,100,55,.40)),
  url('https://images.unsplash.com/photo-1625246333195-78d9c38ad449?auto=format&fit=crop&w=1920&q=80')
  center/cover no-repeat fixed;
  font-family:'Segoe UI',sans-serif;min-height:100vh;}
.navbar{background:linear-gradient(90deg,#1a6b3c,#2d9e5f);}
.card{border:none;border-radius:14px;box-shadow:0 4px 20px rgba(0,0,0,.25);background:rgba(255,255,255,.95);}
.card-header{border-radius:14px 14px 0 0!important;font-weight:600;}
textarea{font-size:.82rem;resize:vertical;min-height:140px;}
.btn-clean{background:linear-gradient(90deg,#e6a817,#f5c842);border:none;font-weight:700;border-radius:10px;}
.btn-clean:hover{background:linear-gradient(90deg,#c8900f,#e6a817);}
.btn-load{background:linear-gradient(90deg,#1a6b3c,#2d9e5f);border:none;font-weight:700;border-radius:10px;}
.btn-copy{background:linear-gradient(90deg,#0d6efd,#4e9fff);border:none;font-weight:700;border-radius:10px;}
.btn-dl{background:linear-gradient(90deg,#198754,#2bc470);border:none;font-weight:700;border-radius:10px;}
#previewTable{font-size:.82rem;}
#previewTable thead th{background:#1a6b3c;color:#fff;position:sticky;top:0;z-index:1;}
.twrap{max-height:320px;overflow-y:auto;border-radius:0 0 10px 10px;}
.result-ok{background:#d1fae5;color:#065f46;border-radius:8px;padding:8px 14px;font-size:.85rem;font-weight:600;}
.result-err{background:#fee2e2;color:#991b1b;border-radius:8px;padding:8px 14px;font-size:.85rem;}
.step-badge{background:#1a6b3c;color:#fff;border-radius:50%;width:22px;height:22px;
  display:inline-flex;align-items:center;justify-content:center;font-size:.7rem;font-weight:700;margin-right:6px;}
</style></head>
<body>

<nav class="navbar navbar-dark px-4 py-2 mb-4">
  <span class="navbar-brand fw-bold fs-6">
    <i class="bi bi-table me-2"></i>KCC Data Formatter
    <span class="badge bg-warning text-dark ms-2" style="font-size:.62rem;vertical-align:middle;">FORMAT TOOL</span>
    <span class="text-white-50 ms-2" style="font-size:.7rem;font-weight:400;">by Kiran Karchi</span>
  </span>
  <span class="text-white-50 small d-flex align-items-center gap-3">
    <span><i class="bi bi-person-circle me-1"></i><span id="loggedName">—</span></span>
    <span class="opacity-25">|</span>
    <a href="/logout" class="text-white-50 text-decoration-none small"><i class="bi bi-box-arrow-right me-1"></i>Logout</a>
  </span>
</nav>

<div class="container" style="max-width:900px;">

  <!-- How to use -->
  <div class="card mb-4">
    <div class="card-header bg-white border-bottom">
      <i class="bi bi-info-circle-fill text-primary me-2"></i>How to Use
    </div>
    <div class="card-body py-3">
      <div class="d-flex gap-4 flex-wrap">
        <span><span class="step-badge">1</span>Paste raw data below (any format)</span>
        <span><span class="step-badge">2</span>Click <strong>Auto Clean & Format</strong></span>
        <span><span class="step-badge">3</span>Check preview table</span>
        <span><span class="step-badge">4</span><strong>Copy</strong> or <strong>Download Excel</strong></span>
        <span><span class="step-badge">5</span>Use in main Automation Dashboard</span>
      </div>
    </div>
  </div>

  <!-- Input card -->
  <div class="card mb-4">
    <div class="card-header bg-white border-bottom">
      <i class="bi bi-magic text-warning me-2"></i>Smart Data Formatter
    </div>
    <div class="card-body">
      <p class="text-muted small mb-2">
        Paste data in <strong>any format</strong> — WhatsApp message, Excel copy, space-separated, any date style.
        Supports: tabs, spaces, commas, pipes. Dates auto-converted to DD/MM/YYYY.
      </p>
      <textarea id="rawInput" class="form-control mb-3"
        placeholder="Paste your data here — examples:&#10;&#10;295381719280  3/27/2026  53000  Madagouda Siddappa Odeyar&#10;300915264220  27-03-2026  49000  Makhabhul K Mulla&#10;766129505616, 2026-03-27, 64000, Malleshi S Ganiger"></textarea>

      <button class="btn btn-clean text-dark w-100 py-2 mb-3" onclick="smartClean()">
        <i class="bi bi-magic me-2"></i>Auto Clean &amp; Format
      </button>

      <!-- Result -->
      <div id="resultMsg" class="d-none mb-3"></div>

      <!-- Preview -->
      <div id="previewSection" class="d-none">
        <div class="d-flex align-items-center justify-content-between mb-2">
          <span class="fw-semibold small text-success">
            <i class="bi bi-check-circle-fill me-1"></i>
            <span id="recCount">0</span> records formatted successfully
          </span>
          <div class="d-flex gap-2">
            <button class="btn btn-copy btn-sm text-white px-3" onclick="copyFormatted()">
              <i class="bi bi-clipboard-check me-1"></i>Copy (Tab Format)
            </button>
            <button class="btn btn-dl btn-sm text-white px-3" onclick="downloadExcel()">
              <i class="bi bi-file-earmark-excel-fill me-1"></i>Download Excel
            </button>
          </div>
        </div>

        <div class="twrap border rounded">
          <table class="table table-sm table-hover mb-0" id="previewTable">
            <thead>
              <tr>
                <th>#</th>
                <th>Aadhar Number</th>
                <th>Loan Disbursal Date</th>
                <th>Max Withdrawal Amount (INR)</th>
                <th>Beneficiary Name</th>
              </tr>
            </thead>
            <tbody id="previewBody"></tbody>
          </table>
        </div>

        <!-- Copy-ready text area (hidden) -->
        <div class="mt-3">
          <label class="form-label small fw-semibold text-muted">
            <i class="bi bi-clipboard me-1"></i>Tab-separated (paste directly into Automation Dashboard → Paste from Excel)
          </label>
          <textarea id="tsvOutput" class="form-control" rows="5" readonly
                    style="font-size:.75rem;font-family:monospace;background:#f8f9fa;"></textarea>
          <button class="btn btn-copy btn-sm text-white mt-2" onclick="copyTSV()">
            <i class="bi bi-copy me-1"></i>Copy to Clipboard
          </button>
          <span id="copyDone" class="text-success small ms-2 d-none">✅ Copied!</span>
        </div>
      </div>
    </div>
  </div>

</div><!-- /container -->

<script>
// ── whoami ────────────────────────────────────────────────────────────────
fetch('/whoami').then(r=>r.json()).then(d=>{
  const el = document.getElementById('loggedName');
  if(el && d.username) el.textContent = d.username;
}).catch(()=>{});

let formattedRows = [];

// ── Smart Format ──────────────────────────────────────────────────────────
function smartClean() {
  const raw = document.getElementById('rawInput').value.trim();
  const resDiv = document.getElementById('resultMsg');
  const prevSec = document.getElementById('previewSection');
  resDiv.className = 'd-none mb-3';
  prevSec.classList.add('d-none');

  if (!raw) {
    resDiv.className = 'result-err mb-3';
    resDiv.innerHTML = '<i class="bi bi-exclamation-triangle-fill me-1"></i>Please paste some data first.';
    resDiv.classList.remove('d-none'); return;
  }

  const lines = raw.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);
  if (lines.length < 1) {
    resDiv.className = 'result-err mb-3';
    resDiv.innerHTML = 'Need at least one data row.';
    resDiv.classList.remove('d-none'); return;
  }

  function splitLine(line) {
    if (line.includes('\t'))  return line.split('\t').map(s => s.trim());
    if (line.includes('|'))   return line.split('|').map(s => s.trim()).filter(s => s);
    if (/  +/.test(line))     return line.split(/  +/).map(s => s.trim());
    if (line.includes(','))   return line.split(',').map(s => s.trim());
    // Smart: Aadhar(10-12 digits) + date + amount + name
    const m = line.match(/^(\d{10,12})\s+(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}[\/\-]\d{2}[\/\-]\d{2})\s+(\d+)\s*(.+)?$/);
    if (m) return [m[1].trim(), m[2].trim(), m[3].trim(), (m[4]||'').trim()];
    return line.split(/\s+/).map(s => s.trim()).filter(s => s);
  }

  function fixDate(val) {
    val = (val||'').trim();
    if (!val) return val;
    if (/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(val)) {
      const p = val.split('/'); const a=parseInt(p[0]),b=parseInt(p[1]);
      if (b>12) return p[1].padStart(2,'0')+'/'+p[0].padStart(2,'0')+'/'+p[2];
      if (a>12) return p[0].padStart(2,'0')+'/'+p[1].padStart(2,'0')+'/'+p[2];
      return p[0].padStart(2,'0')+'/'+p[1].padStart(2,'0')+'/'+p[2];
    }
    if (/^\d{1,2}-\d{1,2}-\d{4}$/.test(val)) {
      const p = val.split('-'); const a=parseInt(p[0]),b=parseInt(p[1]);
      if (b>12) return p[1].padStart(2,'0')+'/'+p[0].padStart(2,'0')+'/'+p[2];
      if (a>12) return p[0].padStart(2,'0')+'/'+p[1].padStart(2,'0')+'/'+p[2];
      return p[0].padStart(2,'0')+'/'+p[1].padStart(2,'0')+'/'+p[2];
    }
    if (/^\d{4}-\d{2}-\d{2}$/.test(val)) {
      const p = val.split('-'); return p[2]+'/'+p[1]+'/'+p[0];
    }
    return val;
  }

  function mapHeader(h) {
    h = h.toLowerCase().replace(/[^a-z0-9]/g,' ').trim();
    if (/aadh|adh/.test(h))              return 'Aadhar Number';
    if (/date|disbursal|disb/.test(h))   return 'Loan Disbursal Date';
    if (/amount|amt|withdrawal|max|inr/.test(h)) return 'Max Withdrawal Amount (INR)';
    if (/name|beneficiary|farmer/.test(h)) return 'Beneficiary Name';
    if (/account|acc/.test(h))           return 'Account Number';
    if (/repay/.test(h))                 return 'Loan Repayment Date';
    return null;
  }

  const headerCols = splitLine(lines[0]);
  const colMap = headerCols.map(mapHeader);
  const hasHeader = colMap.some(c => c !== null);
  const fixedOrder = ['Aadhar Number','Loan Disbursal Date','Max Withdrawal Amount (INR)','Beneficiary Name'];
  const effectiveCols = hasHeader ? colMap : fixedOrder;
  const dataLines = hasHeader ? lines.slice(1) : lines;

  const rows = []; const errors = [];
  dataLines.forEach((line, i) => {
    if (!line.trim()) return;
    const cells = splitLine(line);
    const rec = {};
    effectiveCols.forEach((col, ci) => {
      if (!col) return;
      let val = (cells[ci]||'').trim();
      if (col==='Loan Disbursal Date'||col==='Loan Repayment Date') val = fixDate(val);
      if (col==='Max Withdrawal Amount (INR)') val = val.replace(/[^0-9.]/g,'');
      if (col==='Aadhar Number') val = val.replace(/[^0-9]/g,'');
      rec[col] = val;
    });
    if (!rec['Aadhar Number'] || rec['Aadhar Number'].length < 10) {
      errors.push('Row '+(i+1)+': Invalid Aadhar — '+line.substring(0,40)); return;
    }
    rows.push(rec);
  });

  if (rows.length === 0) {
    resDiv.className = 'result-err mb-3';
    resDiv.innerHTML = '<b>Could not parse data:</b><br>' + errors.join('<br>');
    resDiv.classList.remove('d-none'); return;
  }

  formattedRows = rows;

  // Build preview table
  const tbody = document.getElementById('previewBody');
  tbody.innerHTML = rows.map((r,i) => `
    <tr>
      <td class="text-muted">${i+1}</td>
      <td><code>${r['Aadhar Number']||'—'}</code></td>
      <td><span class="badge bg-success">${r['Loan Disbursal Date']||'—'}</span></td>
      <td>₹${Number(r['Max Withdrawal Amount (INR)']||0).toLocaleString('en-IN')}</td>
      <td>${r['Beneficiary Name']||'—'}</td>
    </tr>`).join('');

  document.getElementById('recCount').textContent = rows.length;

  // Build TSV output
  const cols = ['Aadhar Number','Loan Disbursal Date','Max Withdrawal Amount (INR)','Beneficiary Name'];
  const tsv = [cols.join('\t'), ...rows.map(r => cols.map(c => r[c]||'').join('\t'))].join('\n');
  document.getElementById('tsvOutput').value = tsv;

  prevSec.classList.remove('d-none');
  if (errors.length > 0) {
    resDiv.className = 'result-err mb-3';
    resDiv.innerHTML = '<b>⚠️ Skipped '+errors.length+' row(s):</b> '+errors.join('; ');
    resDiv.classList.remove('d-none');
  } else {
    resDiv.className = 'result-ok mb-3';
    resDiv.innerHTML = '<i class="bi bi-check-circle-fill me-1"></i>'+rows.length+' records formatted successfully ✅';
    resDiv.classList.remove('d-none');
  }
}

// ── Copy TSV ──────────────────────────────────────────────────────────────
function copyTSV() {
  const ta = document.getElementById('tsvOutput');
  ta.select(); document.execCommand('copy');
  const done = document.getElementById('copyDone');
  done.classList.remove('d-none');
  setTimeout(()=>done.classList.add('d-none'), 2500);
}

function copyFormatted() { copyTSV(); }

// ── Download Excel ────────────────────────────────────────────────────────
function downloadExcel() {
  if (formattedRows.length === 0) return;
  const tsv = document.getElementById('tsvOutput').value;
  fetch('/download', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({tsv: tsv})
  }).then(r => r.blob()).then(blob => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'kcc_formatted_' + new Date().toISOString().slice(0,10) + '.xlsx';
    a.click();
  });
}
</script>
</body></html>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        pwd      = request.form.get("password","")
        username = request.form.get("username","Unknown")
        ip       = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        ua       = request.headers.get("User-Agent","unknown")[:80]
        now      = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        if pwd == DASHBOARD_PASSWORD:
            session["authenticated"] = True
            session["username"]      = username
            msg = (f"📋 <b>KCC Formatter — Login</b>\n\n"
                   f"👤 Name   : <b>{username}</b>\n"
                   f"🕐 Time   : {now}\n"
                   f"🌐 IP     : {ip}\n"
                   f"📱 Device : {ua}\n\n"
                   f"🔑 Admin  : {OWNER_NAME}")
            threading.Thread(target=send_telegram, args=(msg,), daemon=True).start()
            return redirect("/")
        else:
            msg = (f"❌ <b>FAILED — Formatter Login</b>\n\n"
                   f"👤 Name   : {username}\n🕐 Time   : {now}\n🌐 IP     : {ip}")
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
    return render_template_string(MAIN_HTML)


@app.route("/whoami")
@login_required
def whoami():
    return {"username": session.get("username","—")}


@app.route("/download", methods=["POST"])
@login_required
def download():
    """Convert TSV to Excel and return as file download."""
    try:
        body = request.get_json(force=True) or {}
        tsv  = body.get("tsv","")
        df   = pd.read_csv(io.StringIO(tsv), sep="\t", dtype=str).fillna("")
        out  = io.BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="KCC Data")
        out.seek(0)
        return Response(
            out.read(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=kcc_formatted.xlsx"}
        )
    except Exception as e:
        return {"error": str(e)}, 400


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("FORMAT_PORT", 5001))
    print(f"  KCC Formatter running at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
