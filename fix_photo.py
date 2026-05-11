"""
Run from ~/mpcp:  python fix_photo.py
Fixes:
  1. enrich_emp strips photo from list API (perf) — serve via dedicated endpoint instead
  2. empAvatarHtml fetches photo from S.photos cache
  3. Adds remove (x) button on hover over photo
  4. Loads photos separately after loadAll so cards don't wait
"""
import shutil
from pathlib import Path

shutil.copy('app.py',    'app.py.bak3')
shutil.copy('index.html','index.html.bak3')
print("Backups saved (.bak3)\n")

# ══════════════════════════════════════════════════════════════════════════
# app.py  — strip photo from enrich_emp list, add /api/employees/photos
# ══════════════════════════════════════════════════════════════════════════
py = Path('app.py').read_text(encoding='utf-8')

# 1. Strip photo from list response (keep it in PUT/single GET, just not the bulk list)
OLD_ENRICH_END = (
    "    try:\n"
    "        r['loc_ids'] = [x[0] for x in db.execute(\"SELECT loc_id FROM emp_locations WHERE emp_id=? ORDER BY is_primary DESC\", (r['id'],)).fetchall()]\n"
    "    except Exception:\n"
    "        try:\n"
    "            r['loc_ids'] = [x[0] for x in db.execute(\"SELECT loc_id FROM loc_emps WHERE emp_id=?\", (r['id'],)).fetchall()]\n"
    "        except Exception:\n"
    "            r['loc_ids'] = []\n"
    "    return r"
)
NEW_ENRICH_END = (
    "    try:\n"
    "        r['loc_ids'] = [x[0] for x in db.execute(\"SELECT loc_id FROM emp_locations WHERE emp_id=? ORDER BY is_primary DESC\", (r['id'],)).fetchall()]\n"
    "    except Exception:\n"
    "        try:\n"
    "            r['loc_ids'] = [x[0] for x in db.execute(\"SELECT loc_id FROM loc_emps WHERE emp_id=?\", (r['id'],)).fetchall()]\n"
    "        except Exception:\n"
    "            r['loc_ids'] = []\n"
    "    r.pop('photo', None)  # served via /api/employees/photos to keep list payload small\n"
    "    return r"
)
if OLD_ENRICH_END in py:
    py = py.replace(OLD_ENRICH_END, NEW_ENRICH_END, 1)
    print("  ✓ photo stripped from enrich_emp list")
else:
    print("  ✗ enrich_emp end not found — add  r.pop('photo', None)  manually before return r")

# 2. Add /api/employees/photos endpoint — returns {emp_id: photo_dataurl}
PHOTOS_ROUTE = """
@app.route('/api/employees/photos', methods=['GET'])
def employees_photos():
    db = get_db()
    rows = db.execute("SELECT id, photo FROM employees WHERE photo != '' AND photo IS NOT NULL").fetchall()
    return jsonify({r['id']: r['photo'] for r in rows})

"""
if '/api/employees/photos' not in py:
    anchor = "@app.route('/api/employees/<eid>/photo', methods=['POST','DELETE'])"
    if anchor in py:
        py = py.replace(anchor, PHOTOS_ROUTE + anchor, 1)
        print("  ✓ /api/employees/photos route added")
    else:
        print("  ✗ photo route anchor not found")
else:
    print("  ✓ /api/employees/photos already present")

Path('app.py').write_text(py, encoding='utf-8')
print("  app.py saved\n")

# ══════════════════════════════════════════════════════════════════════════
# index.html
# ══════════════════════════════════════════════════════════════════════════
html = Path('index.html').read_text(encoding='utf-8')

# 3. Replace empAvatarHtml to use S.photos cache + add remove button logic
OLD_AVATAR_FN = (
    "function empAvatarHtml(emp, size) {\n"
    "  const sz = size==='lg' ? 56 : size==='sm' ? 32 : 42\n"
    "  const fs = size==='lg' ? 20 : size==='sm' ? 11 : 14\n"
    "  const border = size==='lg' ? '3px' : '2px'\n"
    "  if (emp && emp.photo) {\n"
    "    return `<img src=\"${emp.photo}\" style=\"width:${sz}px;height:${sz}px;border-radius:50%;object-fit:cover;border:${border} solid #ED1C24\">`\n"
    "  }\n"
    "  const initials = emp ? emp.name.split(' ').slice(0,2).map(w=>w[0]).join('').toUpperCase() : '?'\n"
    "  const bg = emp ? dc(emp.dept) : '#6b7a99'\n"
    "  return `<div class=\"avatar\" style=\"width:${sz}px;height:${sz}px;font-size:${fs}px;background:${bg}\">${initials}</div>`\n"
    "}"
)
NEW_AVATAR_FN = (
    "function empAvatarHtml(emp, size, showRemove) {\n"
    "  const sz = size==='lg' ? 56 : size==='sm' ? 32 : 42\n"
    "  const fs = size==='lg' ? 20 : size==='sm' ? 11 : 14\n"
    "  const border = size==='lg' ? '3px' : '2px'\n"
    "  const photo = emp && S.photos && S.photos[emp.id]\n"
    "  const removeBtn = (showRemove && photo)\n"
    "    ? `<button onclick=\"deleteEmpPhoto('${emp.id}')\" title=\"Remove photo\" `\n"
    "      +`style=\"position:absolute;top:-4px;right:-4px;width:16px;height:16px;background:#dc2626;`\n"
    "      +`border-radius:50%;border:2px solid #fff;color:#fff;font-size:9px;line-height:1;`\n"
    "      +`cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0\">✕</button>`\n"
    "    : ''\n"
    "  if (photo) {\n"
    "    return `<img src=\"${photo}\" style=\"width:${sz}px;height:${sz}px;border-radius:50%;object-fit:cover;border:${border} solid #ED1C24\">${removeBtn}`\n"
    "  }\n"
    "  const initials = emp ? emp.name.split(' ').slice(0,2).map(w=>w[0]).join('').toUpperCase() : '?'\n"
    "  const bg = emp ? dc(emp.dept) : '#6b7a99'\n"
    "  return `<div class=\"avatar\" style=\"width:${sz}px;height:${sz}px;font-size:${fs}px;background:${bg}\">${initials}</div>`\n"
    "}"
)
if OLD_AVATAR_FN in html:
    html = html.replace(OLD_AVATAR_FN, NEW_AVATAR_FN, 1)
    print("  ✓ empAvatarHtml updated with S.photos cache + remove button")
else:
    print("  ✗ empAvatarHtml not found — was it already modified?")

# 4. Add S.photos to the state object — find the S = { declaration
OLD_STATE = "  activeDept: null,"
NEW_STATE = "  activeDept: null,\n  photos: {},"
if OLD_STATE in html and "photos: {}," not in html:
    html = html.replace(OLD_STATE, NEW_STATE, 1)
    print("  ✓ S.photos added to state")
else:
    print("  ✓ S.photos already in state or anchor not found")

# 5. Load photos after loadAll — find the loadAll function's end where it calls render()
# We look for the last safeGet call inside loadAll and add photo fetch after assignment
OLD_LOAD = "  safeGet('/api/sectors', []),\n  ])"
NEW_LOAD = "  safeGet('/api/sectors', []),\n  ])\n  S.photos = await safeGet('/api/employees/photos', {})"
if OLD_LOAD in html and "S.photos = await safeGet('/api/employees/photos" not in html:
    html = html.replace(OLD_LOAD, NEW_LOAD, 1)
    print("  ✓ S.photos loaded after loadAll parallel fetch")
else:
    print("  ✗ loadAll anchor not found or already patched")

# 6. Update employee card to pass showRemove=true
OLD_CARD_AVATAR = (
    "          <div style=\"position:relative;flex-shrink:0\">\n"
    "            ${empAvatarHtml(emp,'md')}\n"
    "            <label title=\"Upload photo\" style=\"position:absolute;bottom:-2px;right:-2px;width:18px;height:18px;background:#ED1C24;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;border:2px solid #fff\">\n"
    "              <span style=\"color:#fff;font-size:10px;line-height:1\">+</span>\n"
    "              <input type=\"file\" accept=\"image/*\" style=\"display:none\" onchange=\"uploadEmpPhoto('${emp.id}',this.files[0])\">\n"
    "            </label>\n"
    "          </div>"
)
NEW_CARD_AVATAR = (
    "          <div style=\"position:relative;flex-shrink:0\">\n"
    "            ${empAvatarHtml(emp,'md',true)}\n"
    "            <label title=\"Upload photo\" style=\"position:absolute;bottom:-2px;right:-2px;width:18px;height:18px;background:#ED1C24;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;border:2px solid #fff;z-index:1\">\n"
    "              <span style=\"color:#fff;font-size:10px;line-height:1\">+</span>\n"
    "              <input type=\"file\" accept=\"image/*\" style=\"display:none\" onchange=\"uploadEmpPhoto('${emp.id}',this.files[0])\">\n"
    "            </label>\n"
    "          </div>"
)
if OLD_CARD_AVATAR in html:
    html = html.replace(OLD_CARD_AVATAR, NEW_CARD_AVATAR, 1)
    print("  ✓ Employee card avatar updated with showRemove=true")
else:
    print("  ✗ Card avatar block not found")

# 7. hod-banner avatar — pass showRemove=true too
OLD_HOD_AV = '    <div style="position:relative;flex-shrink:0">${empAvatarHtml(hod,\'lg\')}</div>'
NEW_HOD_AV = '    <div style="position:relative;flex-shrink:0">${empAvatarHtml(hod,\'lg\',true)}</div>'
if OLD_HOD_AV in html:
    html = html.replace(OLD_HOD_AV, NEW_HOD_AV, 1)
    print("  ✓ hod-banner avatar updated with showRemove=true")
else:
    print("  ✗ hod-banner avatar not found")

Path('index.html').write_text(html, encoding='utf-8')
print("  index.html saved\n")

print("All done! Restart Flask:  python app.py")
print("\nHow photos work now:")
print("  • Red + button  → click to upload (max 500 KB)")
print("  • Red ✕ button  → appears top-right of photo to remove it")
print("  • Photos load from /api/employees/photos after page load")
print("  • List API stays fast (no base64 in every response)")
