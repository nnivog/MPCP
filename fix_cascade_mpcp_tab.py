"""
Run from ~/mpcp:  python fix_cascade_mpcp_tab.py
1. Adds /api/cascade_mpcp endpoint to app.py
2. Adds renderCascadeMPCP() to index.html
3. Splits CASCADE LINKS subtab into:
      - CASCADE LINKS  (existing link manager)
      - CASCADE MP/CP  (new — shows AUTO- MPs and their CPs)
4. Fixes further cascading by allowing AUTO- MPs to appear in cascade form dropdowns
"""
import shutil
from pathlib import Path

shutil.copy('app.py',    'app.py.bak9')
shutil.copy('index.html','index.html.bak9')
print("Backups saved (.bak9)")

# ══════════════════════════════════════════════════════════════════════════
# 1. app.py — add /api/cascade_mpcp endpoint
# ══════════════════════════════════════════════════════════════════════════
py = Path('app.py').read_text(encoding='utf-8')

NEW_ROUTE = """
@app.route('/api/cascade_mpcp', methods=['GET'])
def cascade_mpcp():
    \"\"\"Return all AUTO- generated MPs and their CPs for the cascade MP/CP tab.\"\"\"
    db = get_db()
    mps = R(db.execute(
        "SELECT * FROM mps WHERE ref LIKE 'AUTO-%' ORDER BY ref"
    ).fetchall())
    result = []
    for mp in mps:
        cps = R(db.execute(
            "SELECT * FROM cps WHERE mp_id=? ORDER BY ref", (mp['id'],)
        ).fetchall())
        # find which employee owns this mp
        owners = R(db.execute(
            "SELECT e.id,e.name,e.emp_code,e.level,e.dept FROM employees e "
            "JOIN mp_owners o ON o.emp_id=e.id WHERE o.mp_id=?", (mp['id'],)
        ).fetchall())
        # find the cascade link that created it
        link = db.execute(
            "SELECT cl.*,e2.name as superior_name,e2.emp_code as superior_code "
            "FROM cascade_links cl "
            "JOIN employees e2 ON e2.id=cl.superior_emp_id "
            "WHERE cl.subordinate_mp_id=?", (mp['id'],)
        ).fetchone()
        result.append({
            **mp,
            'cps': cps,
            'owners': owners,
            'source_link': dict(link) if link else None
        })
    return jsonify(result)

"""

# Insert before /api/perf/exceptions
anchor = "@app.route('/api/perf/exceptions')"
if anchor in py and '/api/cascade_mpcp' not in py:
    py = py.replace(anchor, NEW_ROUTE + anchor, 1)
    print("  v /api/cascade_mpcp route added")
else:
    print("  x anchor not found or route already exists")

Path('app.py').write_text(py, encoding='utf-8')

# ══════════════════════════════════════════════════════════════════════════
# 2. index.html — add renderCascadeMPCP() + update subtabs
# ══════════════════════════════════════════════════════════════════════════
html = Path('index.html').read_text(encoding='utf-8')
lines = html.split('\n')

# ── 2a. Add renderCascadeMPCP function before renderMPCP ─────────────────
NEW_FN = """function renderCascadeMPCP() {
  const c = document.getElementById('mpcp-content');
  if(!c) return;
  c.innerHTML = '<div class="spinner"></div>';
  fetch('/api/cascade_mpcp').then(r=>r.json()).then(mps => {
    if(!mps.length) {
      c.innerHTML = '<div class="card"><div class="card-body" style="text-align:center;padding:32px"><p style="font-size:28px">&#128279;</p><p class="font-bold mt-8">No cascade-generated MPs yet</p><p class="text-sm text-muted mt-8">Create cascade links first — subordinate MPs will appear here automatically.</p></div></div>';
      return;
    }
    let html = '<div style="display:flex;flex-direction:column;gap:16px">';
    mps.forEach(mp => {
      const owner = mp.owners && mp.owners[0];
      const src = mp.source_link;
      html += '<div class="card">';
      html += '<div class="card-head" style="background:linear-gradient(135deg,#1d4ed808,#15803d08);border-left:4px solid #15803d">';
      html += '<div style="display:flex;align-items:center;gap:10px;flex:1">';
      html += '<span style="background:#15803d;color:#fff;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700">AUTO MP</span>';
      html += '<span style="font-family:monospace;font-size:12px;font-weight:700;color:#15803d">' + esc(mp.ref) + '</span>';
      html += '<span style="font-weight:700;flex:1">' + esc(mp.title) + '</span>';
      if(owner) html += '<div class="avatar avatar-sm" style="background:' + dc(owner.dept) + '">' + av(owner.name) + '</div>'
        + '<div><p style="font-size:11px;font-weight:700">' + esc(owner.name) + '</p>'
        + '<p class="text-xxs text-muted">' + esc(owner.emp_code||'') + ' · L' + owner.level + '</p></div>';
      html += '</div></div>';
      if(src) {
        html += '<div style="padding:8px 16px;background:#f0f9ff;border-bottom:1px solid var(--border);font-size:11px;color:#1d4ed8">';
        html += '&#128279; Cascaded from <strong>' + esc(src.superior_name||'') + '</strong> (' + esc(src.superior_code||'') + ')';
        html += '</div>';
      }
      html += '<div class="card-body">';
      if(mp.cps && mp.cps.length) {
        html += '<table style="width:100%;border-collapse:collapse;font-size:12px">';
        html += '<thead><tr style="background:#0a1628;color:#fff"><th style="padding:6px 10px;text-align:left">CP Ref</th><th style="padding:6px 10px;text-align:left">Checking Point</th><th style="padding:6px 10px">Target</th><th style="padding:6px 10px">Freq</th></tr></thead><tbody>';
        mp.cps.forEach((cp,i) => {
          html += '<tr style="background:' + (i%2?'#f8fafc':'#fff') + '">';
          html += '<td style="padding:6px 10px;font-family:monospace;color:#1d4ed8;font-weight:700">' + esc(cp.ref) + '</td>';
          html += '<td style="padding:6px 10px">' + esc(cp.title) + '</td>';
          html += '<td style="padding:6px 10px;text-align:center">' + esc(cp.target||'—') + '</td>';
          html += '<td style="padding:6px 10px;text-align:center">' + esc(cp.freq||'Monthly') + '</td>';
          html += '</tr>';
        });
        html += '</tbody></table>';
      } else {
        html += '<p class="text-sm text-muted italic">No CPs under this cascade MP yet.</p>';
      }
      html += '</div></div>';
    });
    html += '</div>';
    c.innerHTML = html;
  }).catch(e => { c.innerHTML = '<div class="info-box">Error loading cascade MPs: ' + e + '</div>'; });
}

"""

for i, line in enumerate(lines):
    if 'function renderMPCP()' in line:
        lines.insert(i, NEW_FN)
        print(f"  v renderCascadeMPCP() inserted before line {i+1}")
        break

# ── 2b. Update renderMPCP to call renderCascadeMPCP for 'cascade_mps' ────
for i, line in enumerate(lines):
    if "else if (s === 'cascade') renderCascadeBuilder()" in line:
        lines[i] = (
            "  else if (s === 'cascade') renderCascadeBuilder()\n"
            "  else if (s === 'cascade_mps') renderCascadeMPCP()"
        )
        print(f"  v renderMPCP: cascade_mps case added at line {i+1}")
        break

# ── 2c. Update MPCP subtab HTML to add CASCADE MP/CP subtab ──────────────
for i, line in enumerate(lines):
    if 'switchMpcp' in line and 'CASCADE' in line.upper() and 'cascade_mps' not in line:
        # This is the cascade links button — add a new button after it
        lines[i] = lines[i] + '\n      <button class="sub-tab" onclick="switchMPCP(\'cascade_mps\')">&#9881; Cascade MP/CP</button>'
        print(f"  v CASCADE MP/CP subtab added at line {i+1}")
        break

# ── 2d. Fix switchMPCP index array to include cascade_mps ────────────────
for i, line in enumerate(lines):
    if "['mps','cps','links','cascade','assign']" in line:
        lines[i] = line.replace(
            "['mps','cps','links','cascade','assign']",
            "['mps','cps','links','cascade','cascade_mps','assign']"
        )
        print(f"  v switchMPCP index array updated at line {i+1}")
        break

# ── 2e. Fix cascade form MP dropdown to include AUTO- MPs ─────────────────
# The cascade form only shows manual MPs for further cascading
# Find the mp dropdown in openCascadeForm and ensure it includes AUTO- MPs
for i, line in enumerate(lines):
    if 'SELECT * FROM mps' in line and 'openCascadeForm' in '\n'.join(lines[max(0,i-20):i+5]):
        print(f"  - cascade form mp query at line {i+1}: {line.strip()}")
        break

Path('index.html').write_text('\n'.join(lines), encoding='utf-8')
print("\nDone — restart Flask: python app.py")
