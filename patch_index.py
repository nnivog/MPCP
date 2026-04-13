"""
patch_index.py  —  Run this once in your MPCP folder:
    python patch_index.py
It reads index.html, applies all patches, saves patched_index.html,
then renames it to index.html.
"""

import re, shutil, os, datetime

SRC  = "index.html"
BACK = f"index.html.bak.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
OUT  = "index.html"

# ── Read ──────────────────────────────────────────────────────────────────
with open(SRC, "r", encoding="utf-8", errors="replace") as f:
    html = f.read()

shutil.copy(SRC, BACK)
print(f"✓ Backup saved: {BACK}")

applied = []

# ══════════════════════════════════════════════════════════════════════════
# PATCH 1 — Modal backdrop: prevent accidental close on outside click
# ══════════════════════════════════════════════════════════════════════════
old = 'onclick="closeModal(event)"'
new = 'onmousedown="handleBackdrop(event)"'
if old in html:
    html = html.replace(old, new)
    applied.append("✓ PATCH 1: Modal backdrop click fixed")
else:
    applied.append("⚠ PATCH 1: Modal backdrop - pattern not found (already patched?)")

# ══════════════════════════════════════════════════════════════════════════
# PATCH 2 — closeModal & handleBackdrop functions
#   Find the existing closeModal function and replace it
# ══════════════════════════════════════════════════════════════════════════
OLD_CLOSE = re.search(
    r'function closeModal\s*\(.*?\)\s*\{[^}]*\}',
    html, re.DOTALL
)
NEW_CLOSE = """function handleBackdrop(e) {
  // Only close if clicking the dark overlay itself, not the white card
  if (e.target === $('modal-overlay')) {
    const card = $('modal-box');
    card.style.transform = 'scale(1.015)';
    setTimeout(() => card.style.transform = '', 150);
  }
}
function closeModal(e) {
  // Only called from the × button
  $('modal-overlay').classList.add('hidden');
  $('modal-body').innerHTML = '';
  $('modal-foot').innerHTML = '';
}"""

if OLD_CLOSE:
    html = html[:OLD_CLOSE.start()] + NEW_CLOSE + html[OLD_CLOSE.end():]
    applied.append("✓ PATCH 2: closeModal + handleBackdrop added")
else:
    # Inject before </script> if not found
    html = html.replace('</script>', NEW_CLOSE + '\n</script>', 1)
    applied.append("✓ PATCH 2: closeModal injected (fallback)")

# ══════════════════════════════════════════════════════════════════════════
# PATCH 3 — FY auto-detection from date picker (new API utility)
# ══════════════════════════════════════════════════════════════════════════
FY_UTIL = """
// ── FY AUTO-DETECT ───────────────────────────────────────────────────────
async function fyFromDate(dateStr) {
  if (!dateStr) return null;
  try {
    const r = await fetch(`/api/fy_from_date?date=${dateStr}`);
    return await r.json();
  } catch(e) { return null; }
}
function todayISO() { return new Date().toISOString().split('T')[0]; }
"""
if 'fyFromDate' not in html:
    html = html.replace('</script>', FY_UTIL + '\n</script>', 1)
    applied.append("✓ PATCH 3: fyFromDate() utility added")
else:
    applied.append("⚠ PATCH 3: fyFromDate already present")

# ══════════════════════════════════════════════════════════════════════════
# PATCH 4 — Replace openQuickEntry / Quick Performance Entry modal
#   with dual-mode version (count mode OR percent mode)
# ══════════════════════════════════════════════════════════════════════════
NEW_QUICK_ENTRY = r"""
// ── QUICK PERF ENTRY (dual-mode) ─────────────────────────────────────────
let _qMode = 'count'; // 'count' | 'percent'
let _qFY = ''; let _qMonth = '';

async function openQuickEntry() {
  const today = todayISO();
  const fyData = await fyFromDate(today);
  _qFY    = fyData ? fyData.fy       : S.currentFY;
  _qMonth = fyData ? fyData.bs_month : '';

  const empOpts = S.employees.map(e =>
    `<option value="${esc(e.emp_code)}">${esc(e.name)} — ${esc(e.emp_code)}</option>`
  ).join('');

  const cpOpts = S.cps.map(c =>
    `<option value="${esc(c.ref)}">[${esc(c.ref)}] ${esc(c.title.slice(0,55))}${c.title.length>55?'…':''}</option>`
  ).join('');

  openModal('⚡ Quick Performance Entry', `
    <p class="text-xs text-muted mb-12">Fill 4 fields. FY, month &amp; status are auto-calculated.</p>

    <div class="form-grid-2">
      <div class="form-group">
        <label class="form-label">Date *</label>
        <input type="date" id="qe-date" class="form-input" value="${today}"
          onchange="qeUpdateFY(this.value)">
        <div id="qe-fy-pill" class="text-xs mt-8" style="color:#1d4ed8;font-weight:700">
          FY: ${_qFY} | ${_qMonth}
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Employee *</label>
        <select id="qe-emp" class="form-select"><option value="">— Select —</option>${empOpts}</select>
      </div>
    </div>

    <div class="form-group">
      <label class="form-label">Checking Point (CP) *</label>
      <select id="qe-cp" class="form-select" onchange="qeLoadTarget()">
        <option value="">— Select CP —</option>${cpOpts}
      </select>
      <div id="qe-target-info" class="info-box mt-8 hidden"></div>
    </div>

    <div class="form-group">
      <label class="form-label">Input Mode</label>
      <div style="display:flex;gap:8px">
        <button id="qe-btn-count" onclick="qeSetMode('count')"
          class="btn btn-primary btn-sm">📊 Count Mode</button>
        <button id="qe-btn-pct" onclick="qeSetMode('percent')"
          class="btn btn-ghost btn-sm">% Mode</button>
      </div>
      <p class="text-xs text-muted mt-8" id="qe-mode-hint">
        Count Mode: enter total done + how many were on-time/compliant
      </p>
    </div>

    <div id="qe-inputs">
      <div class="form-grid-2">
        <div class="form-group">
          <label class="form-label" id="qe-lbl-total">Total Units Done *</label>
          <input type="number" id="qe-total" class="form-input" min="1"
            placeholder="e.g. 250" oninput="qeAutoCalc()">
        </div>
        <div class="form-group">
          <label class="form-label" id="qe-lbl-b">Compliant / On-Time *</label>
          <input type="number" id="qe-valb" class="form-input" min="0"
            placeholder="e.g. 240" oninput="qeAutoCalc()">
        </div>
      </div>
    </div>

    <div id="qe-calc-display" class="hidden" style="background:#f8fafc;border:1px solid #e2e6ef;
      border-radius:10px;padding:12px 16px;margin-bottom:14px">
    </div>

    <div class="form-group">
      <label class="form-label">Actual Value (optional)</label>
      <input type="number" step="0.01" id="qe-actual" class="form-input"
        placeholder="e.g. 2.3 days">
    </div>

    <div class="form-group">
      <label class="form-label">Remarks</label>
      <input type="text" id="qe-notes" class="form-input" placeholder="Optional notes">
    </div>
  `, [
    {label:'Cancel', cls:'btn-ghost', fn:'closeModal()'},
    {label:'💾 Save Entry', cls:'btn-primary', fn:'qeSave()'},
  ]);
}

function qeSetMode(mode) {
  _qMode = mode;
  const isCount = mode === 'count';
  $('qe-btn-count').className = isCount ? 'btn btn-primary btn-sm' : 'btn btn-ghost btn-sm';
  $('qe-btn-pct').className   = isCount ? 'btn btn-ghost btn-sm'   : 'btn btn-primary btn-sm';
  $('qe-lbl-b').textContent   = isCount ? 'Compliant / On-Time *'  : '% Achieved (0–100) *';
  $('qe-valb').placeholder    = isCount ? 'e.g. 240'               : 'e.g. 96.5';
  $('qe-mode-hint').textContent = isCount
    ? 'Count Mode: enter total done + how many were on-time/compliant'
    : 'Percent Mode: enter total done + overall % achieved';
  qeAutoCalc();
}

async function qeUpdateFY(dateVal) {
  const d = await fyFromDate(dateVal);
  if (d) {
    _qFY = d.fy; _qMonth = d.bs_month;
    $('qe-fy-pill').textContent = `FY: ${d.fy} | ${d.bs_month} | ${d.quarter}`;
  }
}

function qeLoadTarget() {
  const ref = $('qe-cp').value;
  const cp  = S.cps.find(c => c.ref === ref);
  const box = $('qe-target-info');
  if (cp && cp.target) {
    box.classList.remove('hidden');
    box.innerHTML = `<p>Target for <strong>${esc(ref)}</strong>: 
      <strong style="color:#1d4ed8">${esc(cp.target)}</strong> — enter the actual value achieved</p>`;
  } else {
    box.classList.add('hidden');
  }
}

function qeAutoCalc() {
  const total = parseInt($('qe-total')?.value || 0);
  const display = $('qe-calc-display');
  if (!display || !total || total <= 0) { display?.classList.add('hidden'); return; }

  let compliant, nc, pctC;
  const valB = parseFloat($('qe-valb')?.value || 0);

  if (_qMode === 'count') {
    compliant = Math.floor(valB);
    if (compliant > total) {
      display.classList.remove('hidden');
      display.innerHTML = '<span style="color:#dc2626;font-weight:700">⚠ Compliant cannot exceed total</span>';
      return;
    }
    nc   = total - compliant;
    pctC = (compliant / total * 100).toFixed(2);
  } else {
    if (valB < 0 || valB > 100) {
      display.classList.remove('hidden');
      display.innerHTML = '<span style="color:#dc2626;font-weight:700">⚠ % must be between 0 and 100</span>';
      return;
    }
    compliant = Math.round(total * valB / 100);
    nc   = total - compliant;
    pctC = parseFloat(valB).toFixed(2);
  }

  const isC     = parseFloat(pctC) >= 95;
  const statClr = isC ? '#16a34a' : '#dc2626';
  const statLbl = isC ? '✓ Compliant' : '✗ Non-Compliant';

  display.classList.remove('hidden');
  display.innerHTML = `
    <div style="display:flex;gap:20px;flex-wrap:wrap;font-size:12px">
      <span>Total: <strong>${total.toLocaleString()}</strong></span>
      <span style="color:#16a34a">✓ Compliant: <strong>${compliant.toLocaleString()}</strong></span>
      <span style="color:#dc2626">✗ NC: <strong>${nc.toLocaleString()}</strong></span>
      <span>Rate: <strong>${pctC}%</strong></span>
      <span style="color:${statClr};font-weight:700">${statLbl}</span>
    </div>`;

  window._qPayload = { total, compliant, nc, pct_c: parseFloat(pctC) };
}

async function qeSave(overwrite = false) {
  const date    = $('qe-date')?.value;
  const empCode = $('qe-emp')?.value;
  const cpRef   = $('qe-cp')?.value;
  const actual  = parseFloat($('qe-actual')?.value || 0);
  const notes   = $('qe-notes')?.value || '';

  if (!date || !empCode || !cpRef) { toast('Fill Date, Employee and CP', 'err'); return; }
  if (!window._qPayload)           { toast('Enter total and compliant/% values', 'err'); return; }
  if (!_qFY)                       { toast('FY not detected — check date', 'err'); return; }

  const { total, compliant, pct_c } = window._qPayload;
  const body = {
    date, emp_code: empCode, cp_ref: cpRef,
    total, compliant,
    mode: _qMode,
    pct_achieved: pct_c,
    actual_val: actual,
    notes, fy: _qFY, bs_month: _qMonth,
    overwrite
  };

  const r    = await fetch('/api/perf/quick', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const data = await r.json();

  if (r.status === 409 && data.warning === 'duplicate') {
    if (confirm(`⚠ ${data.message}\n\nOverwrite existing record?`)) {
      return qeSave(true);
    }
    return;
  }
  if (!r.ok) { toast(data.error || 'Save failed', 'err'); return; }

  toast(`✓ Saved — ${data.bs_month} ${data.fy} | ${data.pct_compliant}% compliant`, 'ok');
  closeModal();
  S.perf.push(data);
  updateHeader();
}
"""

if 'openQuickEntry' in html:
    # Replace existing function
    pattern = re.compile(
        r'(async\s+)?function\s+openQuickEntry\s*\(.*?\{.*?(?=\n(?:async\s+)?function\s+\w|\n//\s*──|\Z)',
        re.DOTALL
    )
    m = pattern.search(html)
    if m:
        html = html[:m.start()] + NEW_QUICK_ENTRY + html[m.end():]
        applied.append("✓ PATCH 4: openQuickEntry replaced with dual-mode version")
    else:
        html = html.replace('</script>', NEW_QUICK_ENTRY + '\n</script>', 1)
        applied.append("✓ PATCH 4: openQuickEntry injected (pattern fallback)")
else:
    html = html.replace('</script>', NEW_QUICK_ENTRY + '\n</script>', 1)
    applied.append("✓ PATCH 4: openQuickEntry injected (new)")

# ══════════════════════════════════════════════════════════════════════════
# PATCH 5 — openModal helper: ensure it exists and is standard
# ══════════════════════════════════════════════════════════════════════════
OPEN_MODAL = """
// ── MODAL HELPER ─────────────────────────────────────────────────────────
function openModal(title, bodyHTML, buttons=[]) {
  $('modal-title').textContent = title;
  $('modal-body').innerHTML    = bodyHTML;
  $('modal-foot').innerHTML    = buttons.map(b =>
    `<button class="btn ${b.cls}" onclick="${b.fn}">${b.label}</button>`
  ).join('');
  $('modal-overlay').classList.remove('hidden');
  // Transition
  const box = $('modal-box');
  box.style.transform = 'scale(0.97)';
  requestAnimationFrame(() => {
    box.style.transition = 'transform .15s';
    box.style.transform  = 'scale(1)';
  });
}
"""
if 'function openModal' not in html:
    html = html.replace('</script>', OPEN_MODAL + '\n</script>', 1)
    applied.append("✓ PATCH 5: openModal helper added")
else:
    applied.append("⚠ PATCH 5: openModal already exists")

# ══════════════════════════════════════════════════════════════════════════
# PATCH 6 — Ensure cascade links API calls use correct endpoint
# ══════════════════════════════════════════════════════════════════════════
# Fix any wrong endpoint references
if '/api/cascade-links' in html:
    html = html.replace('/api/cascade-links', '/api/cascade_links')
    applied.append("✓ PATCH 6: Fixed cascade_links endpoint URL (hyphen→underscore)")
else:
    applied.append("⚠ PATCH 6: cascade-links URL — already correct or not found")

# ══════════════════════════════════════════════════════════════════════════
# PATCH 7 — UTF-8 meta charset (ensure it's the FIRST meta tag)
# ══════════════════════════════════════════════════════════════════════════
if 'charset="UTF-8"' in html or "charset='UTF-8'" in html:
    applied.append("⚠ PATCH 7: charset=UTF-8 already present")
else:
    html = html.replace('<head>', '<head>\n<meta charset="UTF-8">', 1)
    applied.append("✓ PATCH 7: UTF-8 charset meta added")

# ── Write output ──────────────────────────────────────────────────────────
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n{'='*55}")
print(f"  MPCP index.html Patcher")
print(f"{'='*55}")
for msg in applied:
    print(f"  {msg}")
print(f"{'='*55}")
print(f"\n✅ Done! index.html patched and saved.")
print(f"   Backup: {BACK}")
print(f"\nNext steps:")
print(f"  git add index.html app.py")
print(f'  git commit -m "patch: dual-mode perf entry, modal fix, FY detect, cascade links"')
print(f"  git push origin main")
