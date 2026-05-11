"""
Run from ~/mpcp:  python patch_ui.py
Applies 3 changes to index.html + 1 change to app.py:
  1. hod-banner  → Sipradi red/white style
  2. employee card → red accent + photo support
  3. empAvatar helper → photo-aware
  4. app.py → photo column + 2 new routes
"""
import shutil
from pathlib import Path

# ── backup ────────────────────────────────────────────────────────────────
for f in ['index.html', 'app.py']:
    shutil.copy(f, f + '.bak2')
print("Backups saved (.bak2)")

# ══════════════════════════════════════════════════════════════════════════
# index.html patches
# ══════════════════════════════════════════════════════════════════════════
html = Path('index.html').read_text(encoding='utf-8')

# ── 1. hod-banner CSS → Sipradi red/white ────────────────────────────────
OLD_CSS = (
    '.hod-banner{background:linear-gradient(135deg,#0a1628 0%,#0f2540 100%);'
    'border-radius:16px;padding:22px 28px;display:flex;flex-wrap:wrap;'
    'align-items:center;gap:24px;margin-bottom:20px}\n'
    '.hod-stats{display:flex;gap:12px;flex-wrap:wrap;margin-left:auto}\n'
    '.hod-stat{background:rgba(255,255,255,.1);border-radius:10px;padding:10px 18px;text-align:center}\n'
    '.hod-stat .v{font-size:22px;font-weight:900;color:#fff;font-family:\'Syne\',sans-serif}\n'
    '.hod-stat .l{font-size:10px;color:var(--text);margin-top:2px;font-weight:600;letter-spacing:.4px;text-transform:uppercase}'
)
NEW_CSS = (
    '.hod-banner{background:#fff;border:1px solid #e5e5e5;border-left:5px solid #ED1C24;'
    'border-radius:16px;padding:18px 24px;display:flex;flex-wrap:wrap;'
    'align-items:center;gap:20px;margin-bottom:20px;box-shadow:0 2px 12px rgba(237,28,36,.06)}\n'
    '.hod-stats{display:flex;gap:8px;flex-wrap:wrap;margin-left:auto}\n'
    '.hod-stat{background:#f9f9f9;border:0.5px solid #e5e5e5;border-radius:10px;padding:8px 16px;text-align:center}\n'
    '.hod-stat .v{font-size:20px;font-weight:900;color:#0f1a2e;font-family:\'Syne\',sans-serif}\n'
    '.hod-stat .l{font-size:10px;color:#6b7a99;margin-top:2px;font-weight:600;letter-spacing:.4px;text-transform:uppercase}\n'
    '.hod-stat.hl{border-color:#ED1C24;background:#fff5f5}\n'
    '.hod-stat.hl .l{color:#ED1C24}'
)
if OLD_CSS in html:
    html = html.replace(OLD_CSS, NEW_CSS, 1)
    print("  ✓ hod-banner CSS updated")
else:
    print("  ✗ hod-banner CSS not found — check manually")

# ── 2. hod-banner HTML → red avatar ring + white text fix ────────────────
OLD_BANNER = (
    '  <div class="hod-banner">\n'
    '    <div class="avatar avatar-lg" style="background:${dc(hod.dept)}">${av(hod.name)}</div>\n'
    '    <div>\n'
    '      <p style="font-size:10px;color:var(--text);font-weight:700;text-transform:uppercase;letter-spacing:1px">Head of Department</p>\n'
    '      <p style="font-size:22px;font-weight:900;color:#fff;font-family:\'Syne\',sans-serif">${esc(hod.name)}</p>\n'
    '      <p style="font-size:12px;color:var(--text)">${esc(hod.role)}</p>\n'
    '    </div>\n'
    '    <div class="hod-stats">\n'
    '      ${[[\'MPs\',S.mps.length],[\'CPs\',S.cps.length],[\'Team\',S.employees.length-1],[\'Roles\',S.roles.length]].map(([l,v])=>`<div class="hod-stat"><div class="v">${v}</div><div class="l">${l}</div></div>`).join(\'\')}\n'
    '      <div class="hod-stat"><div class="v" style="color:${pc(Number(avgKPI))}">${avgKPI}%</div><div class="l">KPI Rate</div></div>\n'
    '      <div class="hod-stat"><div class="v" style="color:${pc(pct_c)}">${pct_c}%</div><div class="l">FY ${S.currentFY}</div></div>\n'
    '    </div>\n'
    '  </div>'
)
NEW_BANNER = (
    '  <div class="hod-banner">\n'
    '    <div style="position:relative;flex-shrink:0">${empAvatarHtml(hod,\'lg\')}</div>\n'
    '    <div>\n'
    '      <p style="font-size:10px;color:#ED1C24;font-weight:700;text-transform:uppercase;letter-spacing:1px">Head of Department</p>\n'
    '      <p style="font-size:20px;font-weight:900;color:#0f1a2e;font-family:\'Syne\',sans-serif">${esc(hod.name)}</p>\n'
    '      <p style="font-size:12px;color:#6b7a99">${esc(hod.role)}</p>\n'
    '    </div>\n'
    '    <div class="hod-stats">\n'
    '      ${[[\'MPs\',S.mps.length],[\'CPs\',S.cps.length],[\'Team\',S.employees.length-1],[\'Roles\',S.roles.length]].map(([l,v])=>`<div class="hod-stat"><div class="v">${v}</div><div class="l">${l}</div></div>`).join(\'\')}\n'
    '      <div class="hod-stat hl"><div class="v" style="color:${pc(Number(avgKPI))}">${avgKPI}%</div><div class="l">KPI Rate</div></div>\n'
    '      <div class="hod-stat hl"><div class="v" style="color:${pc(pct_c)}">${pct_c}%</div><div class="l">FY ${S.currentFY}</div></div>\n'
    '    </div>\n'
    '  </div>'
)
if OLD_BANNER in html:
    html = html.replace(OLD_BANNER, NEW_BANNER, 1)
    print("  ✓ hod-banner HTML updated")
else:
    print("  ✗ hod-banner HTML not found — check manually")

# ── 3. Employee card → red accent + photo avatar ─────────────────────────
OLD_CARD = (
    '      html += `<div class="card" style="padding:14px;border-left:3px solid ${empCardColor}">\n'
    '        <div class="flex gap-12">\n'
    '          <div class="avatar avatar-md" style="background:${dc(emp.dept)}">${av(emp.name)}</div>\n'
    '          <div class="flex-1" style="min-width:0">\n'
    '            <p class="font-bold truncate">${esc(emp.name)}</p>\n'
    '            <p class="text-xs text-muted truncate">${esc(emp.role)}</p>\n'
    '            <div class="mt-8"><span class="emp-code">${esc(emp.emp_code||\'—\')}</span></div>\n'
    '            ${mgr?`<p class="text-xxs text-muted mt-4">↑ ${esc(mgr.name.split(\' \')[0])}</p>`:\'\'}\n'
    '            <div class="flex gap-4 mt-8" style="flex-wrap:wrap">\n'
    '              ${deptBadge(emp.dept)}\n'
    '              <span class="badge badge-gray">${myMPs} MPs</span>\n'
    '              <span class="badge badge-gray">${myCPs} CPs</span>\n'
    '            </div>\n'
    '            ${eroles.length?`<div class="flex gap-4 mt-6" style="flex-wrap:wrap">${eroles.map(r=>`<span class="badge" style="background:${r.color};color:#fff">${esc(r.code)}</span>`).join(\'\')}</div>`:\'\'}\n'
    '          </div>\n'
    '        </div>\n'
    '        <div class="flex gap-6 mt-12" style="border-top:1px solid var(--border);padding-top:10px">\n'
    '          <input type="checkbox" class="emp-bulk-cb" value="${emp.id}" onchange="updateEmpBulkCount()" style="display:none;width:16px;height:16px;margin-right:4px;cursor:pointer">\n'
    '          <button class="btn btn-ghost btn-sm flex-1" onclick="openEmpForm(\'${emp.id}\')">Edit</button>\n'
    '          <button class="btn btn-ghost btn-sm flex-1" onclick="openProfile(\'${emp.id}\')">Profile</button>\n'
    '          <button class="btn btn-sm" style="background:#EFF6FF;color:#1D4ED8" onclick="openEmpTrendChart(\'${emp.emp_code}\',\'${emp.name}\')">📈 Trend</button>\n'
    '          <button class="btn btn-sm emp-single-del" style="background:#fee2e2;color:#b91c1c" onclick="delEmp(\'${emp.id}\')">Del</button>\n'
    '        </div>\n'
    '      </div>`'
)
NEW_CARD = (
    '      html += `<div class="card" style="padding:14px;border-left:3px solid #ED1C24">\n'
    '        <div class="flex gap-12">\n'
    '          <div style="position:relative;flex-shrink:0">\n'
    '            ${empAvatarHtml(emp,\'md\')}\n'
    '            <label title="Upload photo" style="position:absolute;bottom:-2px;right:-2px;width:18px;height:18px;background:#ED1C24;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;border:2px solid #fff">\n'
    '              <span style="color:#fff;font-size:10px;line-height:1">+</span>\n'
    '              <input type="file" accept="image/*" style="display:none" onchange="uploadEmpPhoto(\'${emp.id}\',this.files[0])">\n'
    '            </label>\n'
    '          </div>\n'
    '          <div class="flex-1" style="min-width:0">\n'
    '            <p class="font-bold truncate">${esc(emp.name)}</p>\n'
    '            <p class="text-xs text-muted truncate">${esc(emp.role)}</p>\n'
    '            <div class="mt-8"><span class="emp-code">${esc(emp.emp_code||\'—\')}</span></div>\n'
    '            ${mgr?`<p class="text-xxs text-muted mt-4">↑ ${esc(mgr.name.split(\' \')[0])}</p>`:\'\'}\n'
    '            <div class="flex gap-4 mt-8" style="flex-wrap:wrap">\n'
    '              ${deptBadge(emp.dept)}\n'
    '              <span class="badge badge-gray">${myMPs} MPs</span>\n'
    '              <span class="badge badge-gray">${myCPs} CPs</span>\n'
    '            </div>\n'
    '            ${eroles.length?`<div class="flex gap-4 mt-6" style="flex-wrap:wrap">${eroles.map(r=>`<span class="badge" style="background:${r.color};color:#fff">${esc(r.code)}</span>`).join(\'\')}</div>`:\'\'}\n'
    '          </div>\n'
    '        </div>\n'
    '        <div class="flex gap-6 mt-12" style="border-top:1px solid var(--border);padding-top:10px">\n'
    '          <input type="checkbox" class="emp-bulk-cb" value="${emp.id}" onchange="updateEmpBulkCount()" style="display:none;width:16px;height:16px;margin-right:4px;cursor:pointer">\n'
    '          <button class="btn btn-ghost btn-sm flex-1" onclick="openEmpForm(\'${emp.id}\')">Edit</button>\n'
    '          <button class="btn btn-ghost btn-sm flex-1" onclick="openProfile(\'${emp.id}\')">Profile</button>\n'
    '          <button class="btn btn-sm" style="background:#EFF6FF;color:#1D4ED8" onclick="openEmpTrendChart(\'${emp.emp_code}\',\'${emp.name}\')">📈 Trend</button>\n'
    '          <button class="btn btn-sm emp-single-del" style="background:#fee2e2;color:#b91c1c" onclick="delEmp(\'${emp.id}\')">Del</button>\n'
    '        </div>\n'
    '      </div>`'
)
if OLD_CARD in html:
    html = html.replace(OLD_CARD, NEW_CARD, 1)
    print("  ✓ Employee card updated")
else:
    print("  ✗ Employee card not found — check manually")

# ── 4. Inject empAvatarHtml + uploadEmpPhoto helpers before renderTeam ────
INJECT_BEFORE = 'function renderTeam() {'
HELPERS = '''\
function empAvatarHtml(emp, size) {
  const sz = size==='lg' ? 56 : size==='sm' ? 32 : 42
  const fs = size==='lg' ? 20 : size==='sm' ? 11 : 14
  const border = size==='lg' ? '3px' : '2px'
  if (emp && emp.photo) {
    return `<img src="${emp.photo}" style="width:${sz}px;height:${sz}px;border-radius:50%;object-fit:cover;border:${border} solid #ED1C24">`
  }
  const initials = emp ? emp.name.split(' ').slice(0,2).map(w=>w[0]).join('').toUpperCase() : '?'
  const bg = emp ? dc(emp.dept) : '#6b7a99'
  return `<div class="avatar" style="width:${sz}px;height:${sz}px;font-size:${fs}px;background:${bg}">${initials}</div>`
}

async function uploadEmpPhoto(eid, file) {
  if (!file) return
  if (file.size > 500000) { toast('Image too large — max 500 KB', 'error'); return }
  const reader = new FileReader()
  reader.onload = async e => {
    await fetch(`/api/employees/${eid}/photo`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({photo: e.target.result})
    })
    await loadAll()
    toast('Photo updated ✓')
  }
  reader.readAsDataURL(file)
}

async function deleteEmpPhoto(eid) {
  await fetch(`/api/employees/${eid}/photo`, {method:'DELETE'})
  await loadAll()
  toast('Photo removed')
}

'''
if INJECT_BEFORE in html and 'function empAvatarHtml' not in html:
    html = html.replace(INJECT_BEFORE, HELPERS + INJECT_BEFORE, 1)
    print("  ✓ empAvatarHtml + uploadEmpPhoto helpers injected")
else:
    print("  ✗ Helpers already present or anchor not found")

Path('index.html').write_text(html, encoding='utf-8')
print("\nindex.html saved.")

# ══════════════════════════════════════════════════════════════════════════
# app.py patches — add photo column + 2 routes
# ══════════════════════════════════════════════════════════════════════════
py = Path('app.py').read_text(encoding='utf-8')

# ── 5. Add photo column to SCHEMA ─────────────────────────────────────────
OLD_SCHEMA_EMP = 'name TEXT NOT NULL, role TEXT DEFAULT \'\', level INTEGER DEFAULT 3,\n        dept TEXT DEFAULT \'Ops\', manager_id TEXT, email TEXT DEFAULT \'\')'
NEW_SCHEMA_EMP = 'name TEXT NOT NULL, role TEXT DEFAULT \'\', level INTEGER DEFAULT 3,\n        dept TEXT DEFAULT \'Ops\', manager_id TEXT, email TEXT DEFAULT \'\', photo TEXT DEFAULT \'\')'

if OLD_SCHEMA_EMP in py:
    py = py.replace(OLD_SCHEMA_EMP, NEW_SCHEMA_EMP, 1)
    print("  ✓ photo column added to SCHEMA")
else:
    print("  ✗ SCHEMA employees block not found — add photo TEXT DEFAULT '' manually")

# ── 6. Add migrate block to init_db so existing DBs get the column ────────
OLD_INIT = 'def init_db():\n    with get_db() as db:\n        db.executescript(SCHEMA)'
NEW_INIT = (
    'def init_db():\n'
    '    with get_db() as db:\n'
    '        db.executescript(SCHEMA)\n'
    '        # migrate: add photo column if missing\n'
    '        cols = [r[1] for r in db.execute("PRAGMA table_info(employees)")]\n'
    '        if \'photo\' not in cols:\n'
    '            db.execute("ALTER TABLE employees ADD COLUMN photo TEXT DEFAULT \'\'")\n'
    '            db.commit()'
)
if OLD_INIT in py:
    py = py.replace(OLD_INIT, NEW_INIT, 1)
    print("  ✓ Migration block added to init_db")
else:
    print("  ✗ init_db anchor not found")

# ── 7. Add photo routes before the employees API route ───────────────────
PHOTO_ROUTES = '''
@app.route('/api/employees/<eid>/photo', methods=['POST','DELETE'])
def employee_photo(eid):
    db = get_db()
    if request.method == 'DELETE':
        db.execute("UPDATE employees SET photo='' WHERE id=?", (eid,))
        db.commit()
        return jsonify({'ok': True})
    data = request.json
    photo = data.get('photo','')
    if len(photo) > 700000:
        return jsonify({'error':'Image too large'}), 400
    db.execute("UPDATE employees SET photo=? WHERE id=?", (photo, eid))
    db.commit()
    return jsonify({'ok': True})

'''

if '/api/employees/<eid>/photo' not in py:
    # inject before the employee_api (PUT/DELETE) route
    anchor = "@app.route('/api/employees/<eid>',methods=['PUT','DELETE'])"
    if anchor in py:
        py = py.replace(anchor, PHOTO_ROUTES + anchor, 1)
        print("  ✓ Photo upload/delete routes added")
    else:
        print("  ✗ Anchor for photo routes not found — add manually")
else:
    print("  ✓ Photo routes already present")

Path('app.py').write_text(py, encoding='utf-8')
print("\napp.py saved.")
print("\nAll done! Restart Flask:  python app.py")
print("Note: existing employee photos will show initials until a photo is uploaded.")
