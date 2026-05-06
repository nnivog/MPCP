"""
MPCP Diagnostic & Auto-Fix Script
Run this on your machine: python diagnose_and_fix.py
It will tell you exactly what is wrong and fix it.
"""
import os, re, sys, sqlite3

APP = "app.py"
DB  = "scm.db"

print("=" * 60)
print("  MPCP Diagnostic & Fix Tool")
print("=" * 60)

# ── 1. Check we are in the right folder ──────────────────────
if not os.path.exists(APP):
    print(f"\n❌ ERROR: {APP} not found.")
    print("   Run this script from inside your MPCP folder!")
    sys.exit(1)

print(f"\n✅ Found {APP}")

# ── 2. Check DB columns ──────────────────────────────────────
if not os.path.exists(DB):
    print(f"⚠️  {DB} not found — will be created on first run")
    loc_cols = []
    sec_cols = []
else:
    db = sqlite3.connect(DB)
    try:
        loc_cols = [r[1] for r in db.execute("PRAGMA table_info(locations)").fetchall()]
        sec_cols = [r[1] for r in db.execute("PRAGMA table_info(sectors)").fetchall()]
    except:
        loc_cols = []
        sec_cols = []
    db.close()

print(f"\n📋 DB locations columns : {loc_cols}")
print(f"📋 DB sectors columns   : {sec_cols}")

# ── 3. Read app.py ───────────────────────────────────────────
with open(APP, "r", encoding="utf-8") as f:
    src = f.read()

fixes_needed = []
fixes_applied = []

# ── FIX A: locations INSERT ──────────────────────────────────
OLD_LOC = 'db.execute("INSERT OR REPLACE INTO locations VALUES(?,?,?,?,?)",'
NEW_LOC_5 = 'db.execute("INSERT OR REPLACE INTO locations(id,code,name,type,address) VALUES(?,?,?,?,?)",'
NEW_LOC_7 = 'db.execute("INSERT OR REPLACE INTO locations(id,code,name,type,address,sector_id,active) VALUES(?,?,?,?,?,?,?)",'

if OLD_LOC in src:
    fixes_needed.append("A: locations INSERT uses VALUES() without column names (will crash if DB has extra columns)")
elif NEW_LOC_5 in src:
    fixes_needed.append("A: locations INSERT has 5 named columns but DB may have 7")
elif NEW_LOC_7 in src:
    print("\n✅ Fix A already applied (locations INSERT has named columns)")
else:
    fixes_needed.append("A: locations INSERT line not found — may be a different version")

# ── FIX B: sectors INSERT ────────────────────────────────────
OLD_SEC = 'db.execute("INSERT OR REPLACE INTO sectors VALUES(?,?,?,?,?,?)",'
NEW_SEC  = 'db.execute("INSERT OR REPLACE INTO sectors(id,code,name,description,color,sort_order) VALUES(?,?,?,?,?,?)",'

if OLD_SEC in src:
    fixes_needed.append("B: sectors INSERT uses VALUES() without column names (column order mismatch)")
elif NEW_SEC in src:
    print("✅ Fix B already applied (sectors INSERT has named columns)")
else:
    fixes_needed.append("B: sectors INSERT line not found — may be a different version")

# ── Report ────────────────────────────────────────────────────
if fixes_needed:
    print(f"\n⚠️  Issues found ({len(fixes_needed)}):")
    for f in fixes_needed:
        print(f"   - {f}")
    
    print("\n🔧 Applying fixes...")
    backup = APP + ".bak_diagnostic"
    with open(backup, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"   Backup saved: {backup}")

    # Apply Fix A
    if OLD_LOC in src:
        # Also fix the values line below it
        src = src.replace(
            'db.execute("INSERT OR REPLACE INTO locations VALUES(?,?,?,?,?)",\n'
            '               (lid, d.get(\'code\',\'\'), d.get(\'name\',\'\'), d.get(\'type\',\'Office\'), d.get(\'address\',\'\')))',
            'db.execute("INSERT OR REPLACE INTO locations(id,code,name,type,address,sector_id,active) VALUES(?,?,?,?,?,?,?)",\n'
            '               (lid, d.get(\'code\',\'\'), d.get(\'name\',\'\'), d.get(\'type\',\'Office\'), d.get(\'address\',\'\'),\n'
            '                d.get(\'sector_id\',\'\'), d.get(\'active\',1)))'
        )
        # Fallback: just fix the INSERT line if full match failed
        if OLD_LOC in src:
            src = src.replace(OLD_LOC, NEW_LOC_7.rstrip(',') + ',')
        fixes_applied.append("A")
        print("   ✅ Fix A applied: locations INSERT")

    elif NEW_LOC_5 in src:
        src = src.replace(NEW_LOC_5, NEW_LOC_7)
        fixes_applied.append("A")
        print("   ✅ Fix A applied: locations INSERT upgraded to 7-col")

    # Apply Fix B
    if OLD_SEC in src:
        src = src.replace(OLD_SEC, NEW_SEC)
        fixes_applied.append("B")
        print("   ✅ Fix B applied: sectors INSERT")

    with open(APP, "w", encoding="utf-8") as f:
        f.write(src)

    print(f"\n🎉 Fixed! Applied: {', '.join('Fix '+x for x in fixes_applied)}")
    print("\n⚡ Now restart Flask:")
    print("   Kill the running process (Ctrl+C), then: python app.py")
else:
    print("\n✅ app.py looks correct — no code fixes needed.")
    print("\nIf you still see errors, the issue is:")
    print("  1. Flask is still running the OLD version (restart it!)")
    print("  2. Or the browser is cached (hard refresh: Ctrl+Shift+R)")

# ── 4. Check DB for column mismatches ────────────────────────
if loc_cols and 'sector_id' not in loc_cols:
    print(f"\n⚠️  DB locations table missing 'sector_id' column — adding it...")
    db = sqlite3.connect(DB)
    try:
        db.execute("ALTER TABLE locations ADD COLUMN sector_id TEXT DEFAULT ''")
        db.execute("ALTER TABLE locations ADD COLUMN active INTEGER DEFAULT 1")
        db.commit()
        print("   ✅ Added sector_id and active columns to locations table")
    except Exception as e:
        print(f"   (already exists or error: {e})")
    db.close()

print("\n" + "=" * 60)
print("  Done. Restart Flask and hard-refresh browser (Ctrl+Shift+R)")
print("=" * 60)
