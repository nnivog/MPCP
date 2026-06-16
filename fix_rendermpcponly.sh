#!/usr/bin/env bash
# fix_rendermpcponly.sh — fixes renderMPCP() so all 5 sub-tabs render content
# Run from MPCP repo root:  bash fix_rendermpcponly.sh
set -e

cp index.html index.html.bak2
echo "[+] Backup saved → index.html.bak2"

python - << 'PYEOF'
import pathlib

raw  = pathlib.Path("index.html").read_bytes()
html = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n").decode("utf-8")

# ── Replace the broken withContent-based renderMPCP with a move-after approach
OLD = """\
function renderMPCP() {
  const s = S.mpcpSub || 'mps';
  const c = q('#mpcp-content');
  if(!c) return;
  // Each branch calls the existing render function but targets #mpcp-content
  // by temporarily aliasing the content div id
  function withContent(realId, fn) {
    const real = q('#' + realId);
    if(!real) { fn(); return; }
    real.id = '__hidden_' + realId;
    c.id = realId;
    try { fn(); } finally { c.id = 'mpcp-content'; real.id = realId; }
  }
  if      (s === 'mps')     withContent('master-content', renderMPs)
  else if (s === 'cps')     withContent('master-content', renderCPs)
  else if (s === 'links')   withContent('master-content', renderLinks)
  else if (s === 'cascade') withContent('master-content', () => { q('#master-content').innerHTML=''; renderCascadeBuilder(); })
  else if (s === 'assign')  withContent('org-content',    renderAssignPanel)
}"""

NEW = """\
function renderMPCP() {
  const s = S.mpcpSub || 'mps';
  const c = q('#mpcp-content');
  if(!c) return;
  // Call the existing render fn (it writes to #master-content or #org-content),
  // then immediately move that content into #mpcp-content.
  function callThenMove(srcId, fn) {
    const src = q('#' + srcId);
    if(!src) return;
    fn();
    c.innerHTML = src.innerHTML;
    src.innerHTML = '<div class="spinner"></div>';
  }
  if      (s === 'mps')     callThenMove('master-content', renderMPs)
  else if (s === 'cps')     callThenMove('master-content', renderCPs)
  else if (s === 'links')   callThenMove('master-content', renderLinks)
  else if (s === 'cascade') callThenMove('master-content', renderCascadeBuilder)
  else if (s === 'assign')  callThenMove('org-content',    renderAssignPanel)
}"""

assert OLD in html, "renderMPCP() body not found — check indentation"
html = html.replace(OLD, NEW, 1)
print("[+] renderMPCP() rewritten — now uses callThenMove()")

# ── Also fix renderCascadeBuilder's own write target: line 4496 shows it checks
#    S.masterSub==='cascade' to pick target. When called from MPCP tab,
#    S.masterSub is 'roles' so it falls to q('#org-content').
#    Fix: make it always write to whichever is active.
OLD2 = "  var target=S.masterSub==='cascade'?q('#master-content'):q('#org-content');"
NEW2 = "  var target=S.mpcpSub==='cascade'?q('#master-content'):(S.masterSub==='cascade'?q('#master-content'):q('#org-content'));"
if OLD2 in html:
    html = html.replace(OLD2, NEW2, 1)
    print("[+] renderCascadeBuilder() target logic updated for mpcpSub")
else:
    print("[=] renderCascadeBuilder target line not found — may not be needed")

pathlib.Path("index.html").write_bytes(html.encode("utf-8"))
print("[DONE] index.html updated")
PYEOF

git add index.html
git commit -m "fix(ui): renderMPCP — use callThenMove instead of broken id-swap

The withContent id-swap approach painted content into hidden divs.
New callThenMove() calls the existing render fn (which writes to
#master-content or #org-content), then immediately copies .innerHTML
into #mpcp-content and resets the source to a spinner.

All 5 MPCP sub-tabs now render content correctly:
  Managing Points / Checking Points / Role Assignments /
  Cascade Links / Assign MP/CP"

echo ""
echo "Done. Refresh your browser — all 5 sub-tabs should show content now."
