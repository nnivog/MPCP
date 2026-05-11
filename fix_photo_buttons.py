"""
Run from ~/mpcp:  python fix_photo_buttons.py
Fixes:
  1. empAvatarHtml — removes inline remove button, keeps it clean
  2. Employee card — + and X buttons side by side below avatar
  3. deleteEmpPhoto — adds confirm dialog
  4. hod-banner — removes showRemove arg
"""
import shutil
from pathlib import Path

shutil.copy('index.html', 'index.html.bak4')
print("Backup saved: index.html.bak4")

html = Path('index.html').read_text(encoding='utf-8')
changes = 0

# ── 1. Clean empAvatarHtml — no remove button inside it ──────────────────
old1 = """function empAvatarHtml(emp, size, showRemove) {
  const sz = size==='lg' ? 56 : size==='sm' ? 32 : 42
  const fs = size==='lg' ? 20 : size==='sm' ? 11 : 14
  const border = size==='lg' ? '3px' : '2px'
  const photo = emp && S.photos && S.photos[emp.id]
  const removeBtn = (showRemove && photo)
    ? `<button onclick="deleteEmpPhoto('${emp.id}')" title="Remove photo" `
      +`style="position:absolute;top:-4px;right:-4px;width:16px;height:16px;background:#dc2626;`
      +`border-radius:50%;border:2px solid #fff;color:#fff;font-size:9px;line-height:1;`
      +`cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0">✕</button>`
    : ''
  if (photo) {
    return `<img src="${photo}" style="width:${sz}px;height:${sz}px;border-radius:50%;object-fit:cover;border:${border} solid #ED1C24">${removeBtn}`
  }
  const initials = emp ? emp.name.split(' ').slice(0,2).map(w=>w[0]).join('').toUpperCase() : '?'
  const bg = emp ? dc(emp.dept) : '#6b7a99'
  return `<div class="avatar" style="width:${sz}px;height:${sz}px;font-size:${fs}px;background:${bg}">${initials}</div>`
}"""

new1 = """function empAvatarHtml(emp, size) {
  const sz = size==='lg' ? 56 : size==='sm' ? 32 : 42
  const fs = size==='lg' ? 20 : size==='sm' ? 11 : 14
  const border = size==='lg' ? '3px' : '2px'
  const photo = emp && S.photos && S.photos[emp.id]
  if (photo) {
    return `<img src="${photo}" style="width:${sz}px;height:${sz}px;border-radius:50%;object-fit:cover;border:${border} solid #ED1C24">`
  }
  const initials = emp ? emp.name.split(' ').slice(0,2).map(w=>w[0]).join('').toUpperCase() : '?'
  const bg = emp ? dc(emp.dept) : '#6b7a99'
  return `<div class="avatar" style="width:${sz}px;height:${sz}px;font-size:${fs}px;background:${bg}">${initials}</div>`
}"""

if old1 in html:
    html = html.replace(old1, new1, 1); changes += 1
    print("  v empAvatarHtml cleaned")
else:
    print("  x empAvatarHtml not matched")

# ── 2. Replace card avatar block with avatar + [+] [X] buttons below ─────
old2 = """          <div style="flex-shrink:0;display:flex;flex-direction:column;align-items:center;gap:6px">
            ${empAvatarHtml(emp,'md')}
            <div style="display:flex;gap:4px">
              <label title="Upload photo" style="width:22px;height:22px;background:#ED1C24;border-radius:6px;display:flex;align-items:center;justify-content:center;cursor:pointer;border:none">
                <span style="color:#fff;font-size:13px;line-height:1;margin-top:-1px">+</span>
                <input type="file" accept="image/*" style="display:none" onchange="uploadEmpPhoto('${emp.id}',this.files[0])">
              </label>
              ${S.photos&&S.photos[emp.id]
                ? `<button onclick="deleteEmpPhoto('${emp.id}')" title="Remove photo" style="width:22px;height:22px;background:#fee2e2;color:#b91c1c;border:none;border-radius:6px;cursor:pointer;font-size:12px;font-weight:700">✕</button>`
                : ''}
            </div>
          </div>"""

new2 = """          <div style="flex-shrink:0;display:flex;flex-direction:column;align-items:center;gap:5px">
            ${empAvatarHtml(emp,'md')}
            <div style="display:flex;gap:3px">
              <label title="Upload photo" style="width:20px;height:20px;background:#ED1C24;border-radius:5px;display:flex;align-items:center;justify-content:center;cursor:pointer">
                <span style="color:#fff;font-size:14px;line-height:1;margin-top:-1px">+</span>
                <input type="file" accept="image/*" style="display:none" onchange="uploadEmpPhoto('${emp.id}',this.files[0])">
              </label>
              ${S.photos&&S.photos[emp.id]
                ? `<button onclick="deleteEmpPhoto('${emp.id}')" title="Remove photo" style="width:20px;height:20px;background:#fee2e2;color:#b91c1c;border:1px solid #fecaca;border-radius:5px;cursor:pointer;font-size:11px;font-weight:700;padding:0">✕</button>`
                : ''}
            </div>
          </div>"""

if old2 in html:
    html = html.replace(old2, new2, 1); changes += 1
    print("  v Card avatar + buttons updated")
else:
    # try the original patch_ui version
    old2b = """          <div style="position:relative;flex-shrink:0">
            ${empAvatarHtml(emp,'md',true)}
            <label title="Upload photo" style="position:absolute;bottom:-2px;right:-2px;width:18px;height:18px;background:#ED1C24;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;border:2px solid #fff;z-index:1">
              <span style="color:#fff;font-size:10px;line-height:1">+</span>
              <input type="file" accept="image/*" style="display:none" onchange="uploadEmpPhoto('${emp.id}',this.files[0])">
            </label>
          </div>"""
    new2b = """          <div style="flex-shrink:0;display:flex;flex-direction:column;align-items:center;gap:5px">
            ${empAvatarHtml(emp,'md')}
            <div style="display:flex;gap:3px">
              <label title="Upload photo" style="width:20px;height:20px;background:#ED1C24;border-radius:5px;display:flex;align-items:center;justify-content:center;cursor:pointer">
                <span style="color:#fff;font-size:14px;line-height:1;margin-top:-1px">+</span>
                <input type="file" accept="image/*" style="display:none" onchange="uploadEmpPhoto('${emp.id}',this.files[0])">
              </label>
              ${S.photos&&S.photos[emp.id]
                ? `<button onclick="deleteEmpPhoto('${emp.id}')" title="Remove photo" style="width:20px;height:20px;background:#fee2e2;color:#b91c1c;border:1px solid #fecaca;border-radius:5px;cursor:pointer;font-size:11px;font-weight:700;padding:0">✕</button>`
                : ''}
            </div>
          </div>"""
    if old2b in html:
        html = html.replace(old2b, new2b, 1); changes += 1
        print("  v Card avatar + buttons updated (alt match)")
    else:
        print("  x Card avatar block not matched — check manually")

# ── 3. deleteEmpPhoto — add confirm dialog ────────────────────────────────
old3 = """async function deleteEmpPhoto(eid) {
  await fetch(`/api/employees/${eid}/photo`, {method:'DELETE'})
  await loadAll()
  toast('Photo removed')
}"""

new3 = """async function deleteEmpPhoto(eid) {
  if (!confirm('Remove this employee photo? This cannot be undone.')) return
  await fetch(`/api/employees/${eid}/photo`, {method:'DELETE'})
  await loadAll()
  toast('Photo removed')
}"""

if old3 in html:
    html = html.replace(old3, new3, 1); changes += 1
    print("  v deleteEmpPhoto confirm added")
else:
    print("  x deleteEmpPhoto not matched — add confirm() manually")

# ── 4. hod-banner — remove showRemove arg ────────────────────────────────
old4 = """    <div style="position:relative;flex-shrink:0">${empAvatarHtml(hod,'lg',true)}</div>"""
new4 = """    <div style="flex-shrink:0">${empAvatarHtml(hod,'lg')}</div>"""
if old4 in html:
    html = html.replace(old4, new4, 1); changes += 1
    print("  v hod-banner avatar fixed")
else:
    print("  x hod-banner avatar not matched (may already be clean)")

Path('index.html').write_text(html, encoding='utf-8')
print(f"\nDone — {changes} changes applied. Restart Flask: python app.py")
