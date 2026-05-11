"""
Run from ~/mpcp:  python fix_fstring.py
Fixes NameError caused by unescaped CSS braces inside the f-string
in export_employee_mpcp_html (and any bleed-in from the admin CSS block).
"""
import re, shutil, sys
from pathlib import Path

APP = Path("app.py")
if not APP.exists():
    sys.exit("Run this from ~/mpcp where app.py lives.")

# Backup first
shutil.copy(APP, "app.py.bak")
print("Backup saved → app.py.bak")

src = APP.read_text(encoding="utf-8")

# ── Locate the f-string block ────────────────────────────────────────────
# The broken CSS is inside the big f"""...""" in export_employee_mpcp_html.
# We fix ONLY those lines by replacing the exact bad strings.

REPLACEMENTS = [
    # (bad, good)  — order matters, more specific first
    (
        '.tab-bar{display:flex;gap:4px;margin-bottom:20px;border-bottom:2px solid #EEEEEE;padding-bottom:0}',
        '.tab-bar{{display:flex;gap:4px;margin-bottom:20px;border-bottom:2px solid #EEEEEE;padding-bottom:0}}'
    ),
    (
        ".tab-btn{font-family:'Montserrat',sans-serif;font-size:11px;font-weight:700;padding:8px 18px;border:none;background:none;cursor:pointer;color:#777;border-bottom:3px solid transparent;margin-bottom:-2px;text-transform:uppercase;letter-spacing:.3px}",
        ".tab-btn{{font-family:'Montserrat',sans-serif;font-size:11px;font-weight:700;padding:8px 18px;border:none;background:none;cursor:pointer;color:#777;border-bottom:3px solid transparent;margin-bottom:-2px;text-transform:uppercase;letter-spacing:.3px}}"
    ),
    (
        '.tab-btn.active{color:#ED1C24;border-bottom-color:#ED1C24}',
        '.tab-btn.active{{color:#ED1C24;border-bottom-color:#ED1C24}}'
    ),
    (
        '.tab-btn:hover{color:#ED1C24}',
        '.tab-btn:hover{{color:#ED1C24}}'
    ),
    (
        '.tab-panel{display:none}.tab-panel.active{display:block}',
        '.tab-panel{{display:none}}.tab-panel.active{{display:block}}'
    ),
    (
        '.audit-table td{font-size:11px;padding:8px 12px}',
        '.audit-table td{{font-size:11px;padding:8px 12px}}'
    ),
    (
        ".audit-action{font-family:'Montserrat',sans-serif;font-weight:700;font-size:10px;padding:2px 7px;border-radius:3px;background:#F0FDF4;color:#166534}",
        ".audit-action{{font-family:'Montserrat',sans-serif;font-weight:700;font-size:10px;padding:2px 7px;border-radius:3px;background:#F0FDF4;color:#166634}}"
    ),
    (
        '.audit-action.login{background:#EFF6FF;color:#1D4ED8}',
        '.audit-action.login{{background:#EFF6FF;color:#1D4ED8}}'
    ),
    (
        '.audit-action.delete,.audit-action.disable{background:#FFF0F0;color:#ED1C24}',
        '.audit-action.delete,.audit-action.disable{{background:#FFF0F0;color:#ED1C24}}'
    ),
    (
        '.audit-action.edit{background:#FFFBEB;color:#92400E}',
        '.audit-action.edit{{background:#FFFBEB;color:#92400E}}'
    ),
]

changed = 0
for bad, good in REPLACEMENTS:
    if bad in src:
        src = src.replace(bad, good, 1)
        print(f"  ✓ Fixed: {bad[:60]}…")
        changed += 1
    else:
        print(f"  ✗ Not found (already fixed or different): {bad[:60]}…")

APP.write_text(src, encoding="utf-8")
print(f"\nDone. {changed}/{len(REPLACEMENTS)} replacements made.")
print("Restart Flask:  python app.py")
