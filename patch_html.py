with open('index.html','r',encoding='utf-8') as f: html=f.read()

changes=0

# ── A. State: add bsToday ────────────────────────────────────────────────────
old="  employees:[], mps:[], cps:[], roles:[], perf:[], cache:[], cascade:[],"
new="  employees:[], mps:[], cps:[], roles:[], perf:[], cache:[], cascade:[], bsToday:{},"
if old in html and 'bsToday' not in html: html=html.replace(old,new); changes+=1; print("A OK: bsToday state")
else: print("A SKIP")

# ── B. LoadAll: fetch bs_today ───────────────────────────────────────────────
old="    api.get('/api/locations'),\n    api.get('/api/cascade')\n  ])\n  S.employees=e; S.mps=m; S.cps=c; S.roles=r; S.perf=p; S.cache=ca; S.locations=locs; S.cascade=casc"
new="    api.get('/api/locations'),\n    api.get('/api/cascade'),\n    api.get('/api/bs_today')\n  ])\n  S.employees=e; S.mps=m; S.cps=c; S.roles=r; S.perf=p; S.cache=ca; S.locations=locs; S.cascade=casc; S.bsToday=bst"
if old in html: html=html.replace(old,new); changes+=1; print("B OK: loadAll")
else: print("B SKIP: loadAll")

old2="  const [e,m,c,r,p,ca,locs,casc] = await Promise.all(["
new2="  const [e,m,c,r,p,ca,locs,casc,bst] = await Promise.all(["
if old2 in html and 'bst' not in html: html=html.replace(old2,new2); changes+=1; print("B2 OK: destructure")
else: print("B2 SKIP")

# ── C. Nav tab: replace cascade with org ────────────────────────────────────
old='      <button class="nav-tab" onclick="switchTab(\'cascade\')">&#128279; Cascade</button>'
new='      <button class="nav-tab" onclick="switchTab(\'org\')">&#127970; Org &amp; Cascade</button>'
if old in html: html=html.replace(old,new); changes+=1; print("C OK: nav tab")
else:
    old2='      <button class="nav-tab" onclick="switchTab(\'cascade\')">&#128279;Cascade</button>'
    old3='Cascade</button>'
    if 'switchTab(\'cascade\')' in html:
        import re
        html=re.sub(r'<button class="nav-tab" onclick="switchTab\(\'cascade\'\)">[^<]*</button>',
                    '<button class="nav-tab" onclick="switchTab(\'org\')">&#127970; Org &amp; Cascade</button>',html)
        changes+=1; print("C OK: nav tab regex")
    else: print("C SKIP: cascade tab not found")

# ── D. Tab panel: replace cascade with org ───────────────────────────────────
if 'id="tab-cascade"' in html and 'id="tab-org"' not in html:
    import re
    html=re.sub(r'<div id="tab-cascade".*?</div>\s*\n',
        '<div id="tab-org" class="tab-panel">\n'
        '  <div class="sub-tabs" id="org-tabs">\n'
        '    <button class="sub-tab active" onclick="switchOrg(\'tree\')">Live Org Tree</button>\n'
        '    <button class="sub-tab" onclick="switchOrg(\'builder\')">Cascade Builder</button>\n'
        '    <button class="sub-tab" onclick="switchOrg(\'assign\')">Assign MP/CP</button>\n'
        '  </div>\n'
        '  <div id="org-content"><div class="spinner"></div></div>\n'
        '</div>\n',
        html, flags=re.DOTALL)
    changes+=1; print("D OK: org panel")
elif 'id="tab-org"' in html: print("D SKIP: already org")
else: print("D WARN: no cascade or org panel found")

# ── E. renderCurrent ─────────────────────────────────────────────────────────
for old,new in [
    ("  else if(S.currentTab==='cascade') renderCascadeTab()",
     "  else if(S.currentTab==='org') renderOrgTab()"),
    ("  else if(S.currentTab==='cascade') { renderCascadeTab(); return }",
     "  else if(S.currentTab==='org') renderOrgTab()"),
]:
    if old in html: html=html.replace(old,new); changes+=1; print("E OK: renderCurrent"); break
else:
    if "renderOrgTab" not in html:
        old2="  else if(S.currentTab==='reports') renderReport()"
        if old2 in html:
            html=html.replace(old2,old2+"\n  else if(S.currentTab==='org') renderOrgTab()")
            changes+=1; print("E OK: renderCurrent inject")
        else: print("E WARN: cannot find renderCurrent hook")
    else: print("E SKIP: already org")

# ── F. Add CSS for org tree ──────────────────────────────────────────────────
ORG_CSS = (
".org-node{background:#fff;border:2px solid var(--border);border-radius:12px;padding:12px 14px;"
"min-width:176px;max-width:210px;cursor:pointer;transition:.2s;position:relative;display:inline-flex;flex-direction:column}\n"
".org-node:hover{border-color:#60a5fa;box-shadow:0 4px 16px rgba(29,78,216,.12)}\n"
".org-node.selected{border-color:var(--blue);box-shadow:0 0 0 3px rgba(29,78,216,.15)}\n"
".rollup-bar{height:6px;border-radius:6px;background:#e2e8f0;overflow:hidden;margin-top:4px}\n"
".rollup-bar-fill{height:100%;border-radius:6px;transition:.6s}\n"
".level-badge{display:inline-block;font-size:9px;font-weight:900;padding:2px 7px;border-radius:20px;"
"font-family:'Syne',sans-serif;letter-spacing:.4px;text-transform:uppercase}\n"
".level-1{background:#0f2540;color:#fff}.level-2{background:#1d4ed8;color:#fff}\n"
".level-3{background:#6d28d9;color:#fff}.level-4{background:#047857;color:#fff}.level-5{background:#b45309;color:#fff}\n"
".bs-date-picker{display:flex;gap:6px;align-items:center;flex-wrap:wrap}\n"
".bs-date-picker select,.bs-date-picker input[type=number]{border:1.5px solid var(--border);"
"border-radius:8px;padding:6px 8px;font-size:12px;background:#f8fafc;font-family:'DM Sans',sans-serif}\n"
".bs-date-picker input[type=number]{width:58px;text-align:center}\n"
".assign-card{border:1.5px solid var(--border);border-radius:10px;padding:10px 12px;"
"cursor:pointer;transition:.15s;background:#fff;margin-bottom:6px}\n"
".assign-card:hover{border-color:#60a5fa;background:#f0f9ff}\n"
".assign-card.selected{border-color:var(--blue);background:#eff6ff}\n"
)
if ".org-node{" not in html:
    html=html.replace(".hidden{display:none!important}", ".hidden{display:none!important}\n"+ORG_CSS)
    changes+=1; print("F OK: CSS")
else: print("F SKIP: CSS already present")

# ── G. Inject JS before INIT ─────────────────────────────────────────────────
ANCHOR="// -- INIT ---"
if ANCHOR not in html:
    ANCHOR2="// ── INIT ─────────────────────────────────────────────────────────────────────"
    if ANCHOR2 in html: ANCHOR=ANCHOR2

if ANCHOR in html and "function renderOrgTab" not in html:
    ORG_JS = open('org_js.js').read()
    html=html.replace(ANCHOR, ORG_JS+"\n"+ANCHOR)
    changes+=1; print("G OK: org JS injected")
elif "function renderOrgTab" in html:
    print("G SKIP: org JS already present")
else:
    print("G WARN: INIT anchor not found")

with open('index.html','w',encoding='utf-8') as f: f.write(html)
print(f"\nindex.html done. {changes} changes.")

# Verify
for c in ["bsToday","tab-org","renderOrgTab","renderOrgTree","renderCascadeBuilder",
          "renderAssignPanel","bsDatePicker","LOC_COLORS","SECTOR_COLORS",
          "function loadOrgTree","rollup-bar","level-badge"]:
    print(("  OK  " if c in html else "  MISS  ")+c)
