#!/usr/bin/env bash
# apply_mpcp_tab.sh — Create MPCP Management tab consolidating MP/CP/Cascade/Assign/Links
# Run from MPCP repo root:  bash apply_mpcp_tab.sh
set -e

RED='\033[0;31m'; GRN='\033[0;32m'; YLW='\033[1;33m'; NC='\033[0m'
ok()  { echo -e "${GRN}[+]${NC} $*"; }
warn(){ echo -e "${YLW}[!]${NC} $*"; }
step(){ echo -e "\n${YLW}── $* ──${NC}"; }
die(){ echo -e "${RED}[ERR]${NC} $*"; exit 1; }

[ -f index.html ] || die "Run from MPCP repo root"

step "Backup"
cp index.html index.html.bak
ok "index.html.bak created"

# We'll build the full patched file via a Python one-liner (no .py file needed)
# All logic is inline in the heredoc string passed to python -c

python - << 'PYEOF'
import pathlib

raw  = pathlib.Path("index.html").read_bytes()
html = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n").decode("utf-8")

# ══════════════════════════════════════════════════════════════════════════════
# 1. NAV BAR — add MPCP Management button before Org Chart
# ══════════════════════════════════════════════════════════════════════════════
OLD = "    <button class=\"nav-tab tab-admin-only\" onclick=\"switchTab('org')\">&#127970; Org Chart</button>"
NEW = (
    "    <button class=\"nav-tab\" onclick=\"switchTab('mpcp')\">&#127919; MPCP Management</button>\n"
    "    <button class=\"nav-tab tab-admin-only\" onclick=\"switchTab('org')\">&#127970; Org Tree</button>"
)
assert OLD in html, "NAV: Org Chart button not found"
html = html.replace(OLD, NEW, 1)
print("[+] Nav: MPCP Management button added")

# ══════════════════════════════════════════════════════════════════════════════
# 2. MASTER SUB-TABS — remove MPs, CPs, Role Assignments, Cascade Links
#    Keep: Roles, Locations, Departments, Dashboard Builder
# ══════════════════════════════════════════════════════════════════════════════
OLD = (
    "    <div class=\"sub-tabs\" id=\"master-tabs\">\n"
    "      <button class=\"sub-tab active\" onclick=\"switchMaster('mps')\">Managing Points</button>\n"
    "      <button class=\"sub-tab\" onclick=\"switchMaster('cps')\">Checking Points</button>\n"
    "      <button class=\"sub-tab\" onclick=\"switchMaster('roles')\">Role Templates</button>\n"
    "      <button class=\"sub-tab\" onclick=\"switchMaster('links')\">Role Assignments</button>\n"
    "\t\t\t<button class=\"sub-tab\" onclick=\"switchMaster('locations')\">&#128205; Locations</button>\n"
    "      <button class=\"sub-tab master-admin-only\" onclick=\"switchMaster('departments')\">&#127970; Departments</button>\n"
    "      <button class=\"sub-tab\" onclick=\"switchMaster('dashboard_builder')\">&#128196; Dashboard Builder</button>\n"
    "      <button class=\"sub-tab\" onclick=\"switchMaster('cascade')\">&#128279; Cascade Links</button>\n"
    "    </div>"
)
NEW = (
    "    <div class=\"sub-tabs\" id=\"master-tabs\">\n"
    "      <button class=\"sub-tab active\" onclick=\"switchMaster('roles')\">Role Templates</button>\n"
    "      <button class=\"sub-tab\" onclick=\"switchMaster('locations')\">&#128205; Locations</button>\n"
    "      <button class=\"sub-tab master-admin-only\" onclick=\"switchMaster('departments')\">&#127970; Departments</button>\n"
    "      <button class=\"sub-tab\" onclick=\"switchMaster('dashboard_builder')\">&#128196; Dashboard Builder</button>\n"
    "    </div>"
)
assert OLD in html, "MASTER TABS: block not found — check tabs/whitespace"
html = html.replace(OLD, NEW, 1)
print("[+] Master sub-tabs: MP/CP/Links/Cascade removed; Roles/Locations/Departments/Builder kept")

# ══════════════════════════════════════════════════════════════════════════════
# 3. ORG SUB-TABS — remove Assign MP/CP (Org tab = tree only now)
# ══════════════════════════════════════════════════════════════════════════════
OLD = (
    "    <div class=\"sub-tabs\" id=\"org-tabs\">\n"
    "      <button class=\"sub-tab active\" onclick=\"switchOrg('tree')\">Live Org Tree</button>\n"
    "      <button class=\"sub-tab\" onclick=\"switchOrg('assign')\">Assign MP/CP</button>\n"
    "    </div>"
)
NEW = (
    "    <div class=\"sub-tabs\" id=\"org-tabs\">\n"
    "      <button class=\"sub-tab active\" onclick=\"switchOrg('tree')\">Live Org Tree</button>\n"
    "    </div>"
)
assert OLD in html, "ORG TABS: block not found"
html = html.replace(OLD, NEW, 1)
print("[+] Org sub-tabs: Assign MP/CP removed (tree only)")

# ══════════════════════════════════════════════════════════════════════════════
# 4. INJECT #tab-mpcp panel just before #tab-org
# ══════════════════════════════════════════════════════════════════════════════
OLD = "  <div id=\"tab-org\" class=\"tab-panel\">"
NEW = (
    "  <div id=\"tab-mpcp\" class=\"tab-panel\">\n"
    "    <div class=\"sub-tabs\" id=\"mpcp-tabs\">\n"
    "      <button class=\"sub-tab active\" onclick=\"switchMPCP('mps')\">&#127919; Managing Points</button>\n"
    "      <button class=\"sub-tab\" onclick=\"switchMPCP('cps')\">&#9989; Checking Points</button>\n"
    "      <button class=\"sub-tab\" onclick=\"switchMPCP('links')\">&#128203; Role Assignments</button>\n"
    "      <button class=\"sub-tab\" onclick=\"switchMPCP('cascade')\">&#128279; Cascade Links</button>\n"
    "      <button class=\"sub-tab\" onclick=\"switchMPCP('assign')\">&#128101; Assign MP/CP</button>\n"
    "    </div>\n"
    "    <div id=\"mpcp-content\"><div class=\"spinner\"></div></div>\n"
    "  </div>\n"
    "\n"
    "  <div id=\"tab-org\" class=\"tab-panel\">"
)
assert OLD in html, "#tab-org anchor not found"
html = html.replace(OLD, NEW, 1)
print("[+] #tab-mpcp panel injected before #tab-org")

# ══════════════════════════════════════════════════════════════════════════════
# 5. STATE OBJECT — add mpcpSub; fix masterSub default to 'roles'
#    Also fix duplicate authUser/activeDept
# ══════════════════════════════════════════════════════════════════════════════
OLD = "  locations:[], currentTab:'dashboard', teamView:'cards', masterSub:'mps', authUser:null, activeDept:null, authUser:null, activeDept:null,"
NEW = "  locations:[], currentTab:'dashboard', teamView:'cards', masterSub:'roles', mpcpSub:'mps', authUser:null, activeDept:null,"
assert OLD in html, "STATE: line not found"
html = html.replace(OLD, NEW, 1)
print("[+] State: mpcpSub added; masterSub→'roles'; duplicate keys cleaned")

# ══════════════════════════════════════════════════════════════════════════════
# 6. renderMaster() — add redirect guard + change default branch
#    Currently: else renderLinks()  →  change to else renderRoles()
#    Add guard at top to bounce mps/cps/cascade/links to mpcp tab
# ══════════════════════════════════════════════════════════════════════════════
OLD = (
    "function renderMaster() {\n"
    "  if(S.masterSub==='mps') renderMPs()\n"
    "  else if(S.masterSub==='cps') renderCPs()\n"
    "  else if(S.masterSub==='roles') renderRoles()\n"
    "  else if(S.masterSub==='locations') renderLocations()\n"
    "  else if(S.masterSub==='levels') renderLevels()\n"
    "  else if(S.masterSub==='users') renderUsers()\n"
    "  else if(S.masterSub==='departments') renderDepartments()\n"
    "  else if(S.masterSub==='cascade') { q('#master-content').innerHTML=''; renderCascadeBuilder() }\n"
    "  else if(S.masterSub==='sectors') renderSectors()\n"
    "  else if(S.masterSub==='dashboard_builder') renderDashboardBuilder()\n"
    "  else renderLinks()\n"
    "}"
)
NEW = (
    "function renderMaster() {\n"
    "  // MP/CP/Cascade/Links live in MPCP Management tab now\n"
    "  if(['mps','cps','cascade','links'].includes(S.masterSub)) {\n"
    "    S.mpcpSub = S.masterSub; S.masterSub = 'roles';\n"
    "    switchTab('mpcp'); return;\n"
    "  }\n"
    "  if(S.masterSub==='roles') renderRoles()\n"
    "  else if(S.masterSub==='locations') renderLocations()\n"
    "  else if(S.masterSub==='levels') renderLevels()\n"
    "  else if(S.masterSub==='users') renderUsers()\n"
    "  else if(S.masterSub==='departments') renderDepartments()\n"
    "  else if(S.masterSub==='sectors') renderSectors()\n"
    "  else if(S.masterSub==='dashboard_builder') renderDashboardBuilder()\n"
    "  else renderRoles()\n"
    "}"
)
assert OLD in html, "renderMaster(): body not found"
html = html.replace(OLD, NEW, 1)
print("[+] renderMaster(): guard added; default branch → renderRoles()")

# ══════════════════════════════════════════════════════════════════════════════
# 7. renderCurrent() — add mpcp branch
# ══════════════════════════════════════════════════════════════════════════════
OLD = "  else if(S.currentTab==='org') renderOrgTab()"
NEW = (
    "  else if(S.currentTab==='mpcp') renderMPCP()\n"
    "  else if(S.currentTab==='org') renderOrgTab()"
)
assert OLD in html, "renderCurrent(): org branch not found"
html = html.replace(OLD, NEW, 1)
print("[+] renderCurrent(): mpcp branch added")

# ══════════════════════════════════════════════════════════════════════════════
# 8. switchTab() — highlight nav button correctly for 'mpcp'
#    The current logic does: .find(el=>el.textContent.toLowerCase().includes(t.slice(0,4)))
#    'mpcp'.slice(0,4) = 'mpcp' which won't match '🎯 MPCP Management' reliably
#    Fix by replacing the nav highlight line with an explicit id-based approach
# ══════════════════════════════════════════════════════════════════════════════
OLD = "  qq('.nav-tab').find(el=>el.textContent.toLowerCase().includes(t.slice(0,4)))?.classList.add('active')"
NEW = (
    "  // highlight the nav button whose onclick contains the tab name\n"
    "  qq('.nav-tab').find(el=>el.getAttribute('onclick')?.includes(\"'\" + t + \"'\"))?.classList.add('active')"
)
assert OLD in html, "switchTab(): nav highlight line not found"
html = html.replace(OLD, NEW, 1)
print("[+] switchTab(): nav highlight fixed to use onclick attribute match")

# ══════════════════════════════════════════════════════════════════════════════
# 9. switchOrg() — remove 'assign' handling (stays in MPCP tab)
# ══════════════════════════════════════════════════════════════════════════════
OLD = (
    "function switchOrg(s){\n"
    "  orgSub=s\n"
    "  qq('#org-tabs .sub-tab').forEach(t=>t.classList.remove('active'))\n"
    "  event.target.classList.add('active')\n"
    "  renderOrgTab()\n"
    "}"
)
NEW = (
    "function switchOrg(s){\n"
    "  if(s==='assign'){ switchTab('mpcp'); switchMPCP('assign'); return; }\n"
    "  orgSub=s\n"
    "  qq('#org-tabs .sub-tab').forEach(t=>t.classList.remove('active'))\n"
    "  event.target.classList.add('active')\n"
    "  renderOrgTab()\n"
    "}"
)
assert OLD in html, "switchOrg(): body not found"
html = html.replace(OLD, NEW, 1)
print("[+] switchOrg(): assign redirect added")

# ══════════════════════════════════════════════════════════════════════════════
# 10. Inject switchMPCP() + renderMPCP() right after switchMaster() line
# ══════════════════════════════════════════════════════════════════════════════
OLD = "function switchMaster(s) { S.masterSub=s; qq('#master-tabs .sub-tab').forEach(t=>t.classList.remove('active')); event.target.classList.add('active'); renderMaster() }"
NEW = (
    "function switchMaster(s) { S.masterSub=s; qq('#master-tabs .sub-tab').forEach(t=>t.classList.remove('active')); event.target.classList.add('active'); renderMaster() }\n"
    "\n"
    "function switchMPCP(s) {\n"
    "  S.mpcpSub = s;\n"
    "  qq('#mpcp-tabs .sub-tab').forEach(t => t.classList.remove('active'));\n"
    "  const idx = ['mps','cps','links','cascade','assign'].indexOf(s);\n"
    "  const btns = qq('#mpcp-tabs .sub-tab');\n"
    "  if(idx >= 0 && btns[idx]) btns[idx].classList.add('active');\n"
    "  renderMPCP();\n"
    "}\n"
    "\n"
    "function renderMPCP() {\n"
    "  const s = S.mpcpSub || 'mps';\n"
    "  const c = q('#mpcp-content');\n"
    "  if(!c) return;\n"
    "  // Each branch calls the existing render function but targets #mpcp-content\n"
    "  // by temporarily aliasing the content div id\n"
    "  function withContent(realId, fn) {\n"
    "    const real = q('#' + realId);\n"
    "    if(!real) { fn(); return; }\n"
    "    real.id = '__hidden_' + realId;\n"
    "    c.id = realId;\n"
    "    try { fn(); } finally { c.id = 'mpcp-content'; real.id = realId; }\n"
    "  }\n"
    "  if      (s === 'mps')     withContent('master-content', renderMPs)\n"
    "  else if (s === 'cps')     withContent('master-content', renderCPs)\n"
    "  else if (s === 'links')   withContent('master-content', renderLinks)\n"
    "  else if (s === 'cascade') withContent('master-content', () => { q('#master-content').innerHTML=''; renderCascadeBuilder(); })\n"
    "  else if (s === 'assign')  withContent('org-content',    renderAssignPanel)\n"
    "}"
)
assert OLD in html, "switchMaster(): line not found"
html = html.replace(OLD, NEW, 1)
print("[+] switchMPCP() + renderMPCP() injected after switchMaster()")

# ══════════════════════════════════════════════════════════════════════════════
# 11. Fix renderMPCP's cascade branch — after id swap, q('#master-content')
#     now points to mpcp-content so the inner clear works fine.
#     But renderCascadeBuilder calls q('#master-content') too — already handled.
#     Also fix renderOrgTab() — it calls renderAssignPanel for 'assign' sub:
# ══════════════════════════════════════════════════════════════════════════════
OLD = "  if(S.orgSub==='tree'||!S.orgSub) renderOrgTree()\n  else renderAssignPanel()"
if OLD in html:
    NEW2 = "  if(S.orgSub==='tree'||!S.orgSub) renderOrgTree()\n  else renderOrgTree()"
    html = html.replace(OLD, NEW2, 1)
    print("[+] renderOrgTab(): assign branch replaced with tree (assign now in MPCP tab)")
else:
    # try alternate form
    OLD2 = "  if(orgSub==='tree'||!orgSub) renderOrgTree()\n  else renderAssignPanel()"
    if OLD2 in html:
        html = html.replace(OLD2, "  if(orgSub==='tree'||!orgSub) renderOrgTree()\n  else renderOrgTree()", 1)
        print("[+] renderOrgTab(): assign branch replaced (orgSub form)")
    else:
        print("[!] renderOrgTab() assign branch not matched — check manually")

# ══════════════════════════════════════════════════════════════════════════════
# 12. Update any hardcoded deep-links pointing to master+mps/cps/cascade/links
# ══════════════════════════════════════════════════════════════════════════════
swaps = [
    ("switchTab('master');switchMaster('mps')",      "switchTab('mpcp');switchMPCP('mps')"),
    ("switchTab('master');switchMaster('cps')",      "switchTab('mpcp');switchMPCP('cps')"),
    ("switchTab('master');switchMaster('cascade')",  "switchTab('mpcp');switchMPCP('cascade')"),
    ("switchTab('master');switchMaster('links')",    "switchTab('mpcp');switchMPCP('links')"),
    ("switchTab('master');switchMaster('dashboard_builder')", "switchTab('master');switchMaster('dashboard_builder')"),  # keep
    ("switchOrg('assign')",                          "switchTab('mpcp');switchMPCP('assign')"),
]
for old, new in swaps:
    if old in html and old != new:
        n = html.count(old)
        html = html.replace(old, new)
        print(f"[+] deep-link updated ({n}x): {old[:55]}")

# ══════════════════════════════════════════════════════════════════════════════
# Write
# ══════════════════════════════════════════════════════════════════════════════
pathlib.Path("index.html").write_bytes(html.encode("utf-8"))
print("\n[DONE] index.html written.")
PYEOF

step "Git commit"
git add index.html
git commit -m "feat(ui): MPCP Management tab — consolidate MP/CP/Cascade/Assign/Links

New top-level tab '🎯 MPCP Management' with 5 sub-tabs:
  • Managing Points
  • Checking Points
  • Role Assignments
  • Cascade Links
  • Assign MP/CP (moved from Org Chart tab)

Master Setup tab now contains: Role Templates, Locations,
  Departments, Dashboard Builder only.

Org Chart tab renamed 'Org Tree' — shows Live Org Tree only.

Routing:
  • switchMPCP(s) / renderMPCP() added
  • renderMaster() redirects legacy mps/cps/cascade/links calls to mpcp tab
  • switchOrg('assign') redirects to mpcp tab
  • switchTab() nav highlight fixed to use onclick attribute matching
  • renderCurrent() handles 'mpcp' tab
  • State: mpcpSub key added; masterSub default → 'roles'
  • All deep-links updated

No backend changes. All calculations/formulas untouched."

echo ""
echo -e "${GRN}Done!${NC}  Test:  python app.py"
echo "  Revert:  cp index.html.bak index.html && git checkout index.html"
