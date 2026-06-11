"""
MPCP → Hugging Face Spaces Patch Script
Run this ONCE from your repo root in Git Bash:

    python patch_for_hf.py

It will:
  1. Read your existing app.py
  2. Inject persistent storage path config
  3. Replace all sqlite3.connect("*.db") calls
  4. Fix the port to 7860
  5. Save patched file as app.py (original backed up as app.py.bak)
"""

import re
import shutil
import sys
from pathlib import Path

APP_FILE = Path("app.py")

if not APP_FILE.exists():
    print("ERROR: app.py not found. Run this script from your repo root.")
    sys.exit(1)

# --- Backup original ---
shutil.copy(APP_FILE, "app.py.bak")
print("✅ Backed up original → app.py.bak")

original = APP_FILE.read_text(encoding="utf-8")
patched = original

# ──────────────────────────────────────────────
# PATCH 1: Inject HF storage config block
# Inserted right after the last import line
# ──────────────────────────────────────────────

HF_CONFIG_BLOCK = '''
# ── HF Spaces Persistent Storage Config ──────────────────────────────────────
import os as _os
import shutil as _shutil

_DATA_DIR = "/data" if _os.path.exists("/data") else "."

# All DB paths — edit here if you add more databases
_DB_MAP = {
    "master.db":  _os.path.join(_DATA_DIR, "master.db"),
    "scm.db":     _os.path.join(_DATA_DIR, "scm.db"),
}

# Seed on first boot: copy bundled .db files into /data if not present
for _src, _dst in _DB_MAP.items():
    if not _os.path.exists(_dst) and _os.path.exists(_src):
        _shutil.copy(_src, _dst)
        print(f"[BOOT] Seeded {_src} → {_dst}")

def _db(name: str) -> str:
    """Return the correct DB path for local or HF environment."""
    return _DB_MAP.get(name, _os.path.join(_DATA_DIR, name))
# ─────────────────────────────────────────────────────────────────────────────
'''

# Find insertion point: after the last top-level import block
# Strategy: find last "^import " or "^from " line index
lines = patched.splitlines()
last_import_idx = 0
for i, line in enumerate(lines):
    if re.match(r'^(import |from )\S', line):
        last_import_idx = i

# Insert config block after last import line
lines.insert(last_import_idx + 1, HF_CONFIG_BLOCK)
patched = "\n".join(lines)
print(f"✅ Injected HF storage config block after line {last_import_idx + 1}")

# ──────────────────────────────────────────────
# PATCH 2: Replace sqlite3.connect("*.db") calls
# ──────────────────────────────────────────────

def replace_connect(match):
    db_name = match.group(1)  # e.g. master.db or scm.db
    return f'sqlite3.connect(_db("{db_name}")'

pattern = r'sqlite3\.connect\(["\']([^"\']+\.db)["\']\)'
before_count = len(re.findall(pattern, patched))
patched = re.sub(pattern, replace_connect, patched)
print(f"✅ Replaced {before_count} sqlite3.connect() call(s)")

# ──────────────────────────────────────────────
# PATCH 3: Fix port — 5050 → 7860, add host
# ──────────────────────────────────────────────

# Handle common patterns:
#   app.run(port=5050)
#   app.run(debug=True, port=5050)
#   app.run(host='0.0.0.0', port=5050)
#   app.run()

def fix_port(match):
    run_args = match.group(1)
    # Remove existing host and port args
    run_args = re.sub(r",?\s*host\s*=\s*['\"].*?['\"]", "", run_args)
    run_args = re.sub(r",?\s*port\s*=\s*\d+", "", run_args)
    run_args = run_args.strip().strip(",").strip()
    if run_args:
        return f'app.run({run_args}, host="0.0.0.0", port=7860)'
    else:
        return 'app.run(host="0.0.0.0", port=7860)'

port_pattern = r'app\.run\(([^)]*)\)'
port_matches = re.findall(port_pattern, patched)
if port_matches:
    patched = re.sub(port_pattern, fix_port, patched)
    print(f"✅ Fixed app.run() port → 7860 with host=0.0.0.0")
else:
    print("⚠️  No app.run() found — add manually: app.run(host='0.0.0.0', port=7860)")

# ──────────────────────────────────────────────
# Write patched file
# ──────────────────────────────────────────────
APP_FILE.write_text(patched, encoding="utf-8")
print("\n✅ app.py patched successfully!")
print("\nNext steps:")
print("  1. Review app.py to confirm changes look correct")
print("  2. git add app.py Dockerfile requirements.txt .github/workflows/sync_hf.yml")
print("  3. git commit -m 'feat: HF Spaces deployment config'")
print("  4. git push origin main")
