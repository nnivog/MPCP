"""
diagnose_structure.py — dumps exact HTML of nav bar, all tab panels,
master sub-tabs block, and org sub-tabs block.
Run from MPCP root:  python diagnose_structure.py
"""
import pathlib, re

raw  = pathlib.Path("index.html").read_bytes()
html = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n").decode("utf-8")
lines = html.splitlines()

def show(label, start, end):
    print(f"\n{'='*60}")
    print(f"  {label}  (lines {start}–{end})")
    print('='*60)
    print(repr("\n".join(lines[start-1:end])))

# 1. Full nav bar  (lines 646-658 from previous scan)
show("NAV BAR", 644, 660)

# 2. Master tab panel opening + sub-tabs (lines 676-690)
show("MASTER PANEL + SUB-TABS", 674, 692)

# 3. Org tab panel opening + sub-tabs (lines 709-716)
show("ORG PANEL + SUB-TABS", 707, 718)

# 4. renderMaster function first 10 lines
show("renderMaster() first 15 lines", 1302, 1317)

# 5. renderCurrent() full body
show("renderCurrent() full body", 891, 900)

# 6. switchTab() full body
show("switchTab() full body", 883, 900)

# 7. State object line
show("State object (S = {...})", 732, 737)

# 8. switchMaster line
show("switchMaster() line", 900, 902)

# 9. switchOrg() line
show("switchOrg() line", 4078, 4083)
