"""
Run from ~/mpcp:  python fix_accumulate.py
"""
import shutil
from pathlib import Path

shutil.copy('app.py', 'app.py.bak7')
shutil.copy('index.html', 'index.html.bak7')
print("Backups saved (.bak7)")

# ── app.py ────────────────────────────────────────────────────────────────
py = Path('app.py').read_text(encoding='utf-8')

lines = py.split('\n')
start = end = -1
for i, line in enumerate(lines):
    if "if existing and not d.get('overwrite'):" in line:
        start = i
    if start != -1 and '}), 409' in line:
        end = i
        break

if start != -1 and end != -1:
    new_block = [
        "    if existing:",
        "        total     = (existing['total'] or 0) + total",
        "        compliant = (existing['compliant'] or 0) + compliant",
        "        nc        = total - compliant",
        "        pct_c     = round(compliant / total * 100, 2) if total else 0",
        "        pct_nc    = round(nc / total * 100, 2) if total else 0",
        "        actual_val = max(actual_val, existing['actual_val'] or 0)",
        "        status    = 'C' if pct_c >= 95 else 'NC'",
    ]
    lines[start:end+1] = new_block
    print(f"  v app.py: replaced lines {start+1}-{end+1} with accumulate logic")
else:
    print("  x app.py: could not find duplicate block")

Path('app.py').write_text('\n'.join(lines), encoding='utf-8')

# ── index.html ────────────────────────────────────────────────────────────
html = Path('index.html').read_text(encoding='utf-8')
lines = html.split('\n')

# Remove the 409 duplicate block
start = end = -1
for i, line in enumerate(lines):
    if 'r.status === 409' in line and "data.warning === 'duplicate'" in line:
        start = i
        break
if start != -1:
    for j in range(start, min(start+10, len(lines))):
        if lines[j].strip() == '}':
            end = j
            break

if start != -1 and end != -1:
    lines[start:end+1] = []
    print(f"  v index.html: removed 409 duplicate block (lines {start+1}-{end+1})")
else:
    print("  x index.html: 409 block not found")

# Replace toast line with cumulative version
html2 = '\n'.join(lines)
old_toast = "  toast(`\u2713 Saved \u2014 ${data.bs_month} ${data.fy} | ${data.pct_compliant}% compliant`, 'ok');"
new_toast = (
    "  const _msg = data.accumulated\n"
    "    ? `\u2713 Accumulated \u2014 ${data.bs_month} ${data.fy} | Total: ${data.total} | ${data.compliant} compliant (${data.pct_compliant}%)`\n"
    "    : `\u2713 Saved \u2014 ${data.bs_month} ${data.fy} | ${data.pct_compliant}% compliant`\n"
    "  toast(_msg, 'ok');"
)
if old_toast in html2:
    html2 = html2.replace(old_toast, new_toast, 1)
    print("  v index.html: cumulative toast added")
else:
    # try finding by partial match
    idx = html2.find("toast(`")
    ctx = html2[max(0,idx-20):idx+80] if idx!=-1 else "NOT FOUND"
    print(f"  x index.html: toast line not matched. Context: {repr(ctx)}")

Path('index.html').write_text(html2, encoding='utf-8')
print("\nDone — restart Flask: python app.py")
