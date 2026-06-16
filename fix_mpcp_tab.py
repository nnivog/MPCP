"""
Run from ~/mpcp:  python fix_mpcp_tab.py
Fixes MPCP tab routing by patching specific line numbers.
"""
import shutil
from pathlib import Path

shutil.copy('index.html', 'index.html.bak8')
print("Backup saved: index.html.bak8")

lines = Path('index.html').read_text(encoding='utf-8').split('\n')
changes = 0

# Lines to patch (1-indexed from grep output):
# 1416: renderMPs output
# 1671: renderCPs output  
# 1736: renderRoles output
# 1801: renderLinks output
# 3296: renderAssignPanel or similar

TARGET_LINES = {
    1416: ("q('#master-content').innerHTML = html",
           "const _tMPs=S.currentTab==='mpcp'?document.getElementById('mpcp-content'):document.getElementById('master-content'); if(_tMPs)_tMPs.innerHTML=html"),
    1671: ("q('#master-content').innerHTML = html",
           "const _tCPs=S.currentTab==='mpcp'?document.getElementById('mpcp-content'):document.getElementById('master-content'); if(_tCPs)_tCPs.innerHTML=html"),
    1736: ("q('#master-content').innerHTML=html",
           "const _tRoles=S.currentTab==='mpcp'?document.getElementById('mpcp-content'):document.getElementById('master-content'); if(_tRoles)_tRoles.innerHTML=html"),
    1801: ("q('#master-content').innerHTML=html",
           "const _tLinks=S.currentTab==='mpcp'?document.getElementById('mpcp-content'):document.getElementById('master-content'); if(_tLinks)_tLinks.innerHTML=html"),
    3296: ("q('#master-content').innerHTML = html",
           "const _tAsgn=S.currentTab==='mpcp'?document.getElementById('mpcp-content'):document.getElementById('master-content'); if(_tAsgn)_tAsgn.innerHTML=html"),
}

for lineno, (expected, replacement) in TARGET_LINES.items():
    idx = lineno - 1
    if idx < len(lines) and expected in lines[idx]:
        lines[idx] = lines[idx].replace(expected, replacement)
        print(f"  v line {lineno}: patched")
        changes += 1
    else:
        # Search nearby +-3 lines
        found = False
        for offset in range(-3, 4):
            i = idx + offset
            if 0 <= i < len(lines) and expected in lines[i]:
                lines[i] = lines[i].replace(expected, replacement)
                print(f"  v line {lineno} (found at {i+1}): patched")
                changes += 1
                found = True
                break
        if not found:
            print(f"  x line {lineno}: not matched — actual: {lines[idx][:80] if idx < len(lines) else 'OUT OF RANGE'}")

# Fix renderCascadeBuilder target line — search by content
for i, line in enumerate(lines):
    if 'mpcpSub' in line and 'cascade' in line and 'master-content' in line and 'target' in line:
        lines[i] = "  var target=S.currentTab==='mpcp'?document.getElementById('mpcp-content'):(S.masterSub==='cascade'?document.getElementById('master-content'):document.getElementById('org-content'));"
        print(f"  v line {i+1}: renderCascadeBuilder target fixed")
        changes += 1
        break

# Fix renderMPCP callThenMove -> direct calls, search by content
start = end = -1
for i, line in enumerate(lines):
    if 'function renderMPCP()' in line:
        start = i
    if start != -1 and i > start and line.strip() == '}' and 'callThenMove' in '\n'.join(lines[start:i]):
        end = i
        break

if start != -1 and end != -1:
    new_block = [
        "function renderMPCP() {",
        "  const s = S.mpcpSub || 'mps';",
        "  const c = document.getElementById('mpcp-content');",
        "  if(!c) return;",
        "  c.innerHTML = '<div class=\"spinner\"></div>';",
        "  if      (s === 'mps')     renderMPs()",
        "  else if (s === 'cps')     renderCPs()",
        "  else if (s === 'links')   renderLinks()",
        "  else if (s === 'cascade') renderCascadeBuilder()",
        "  else if (s === 'assign')  renderAssignPanel()",
        "}",
    ]
    lines[start:end+1] = new_block
    print(f"  v renderMPCP() simplified (was lines {start+1}-{end+1})")
    changes += 1
else:
    print(f"  x renderMPCP() block not found (start={start}, end={end})")

# Ensure renderCurrent calls renderMPCP
for i, line in enumerate(lines):
    if "S.currentTab==='mpcp'" in line and 'renderMPCP' not in line:
        lines[i] = "  else if(S.currentTab==='mpcp') renderMPCP()"
        print(f"  v line {i+1}: renderCurrent mpcp case fixed")
        changes += 1
        break
    if "S.currentTab==='mpcp'" in line and 'renderMPCP' in line:
        print(f"  v renderCurrent mpcp already calls renderMPCP")
        break

Path('index.html').write_text('\n'.join(lines), encoding='utf-8')
print(f"\nDone — {changes} changes. Restart Flask: python app.py")
