"""
fix_all.py  —  Run once in your MPCP folder:
    python fix_all.py
Fixes:
  1. index.html open() encoding crash (500 on /)
  2. Adds /api/cascade  (GET list, POST create, DELETE)
  3. Adds /api/cascade/tree
  4. Adds /api/org/cascade_assign
"""

import os, shutil, datetime

BACK = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

# ══════════════════════════════════════════════════════════════
# FIX 1 — index.html encoding
# ══════════════════════════════════════════════════════════════
print("Reading index.html...")
html = open('index.html', 'r', encoding='utf-8', errors='replace').read()
shutil.copy('index.html', f'index.html.bak.{BACK}')
open('index.html', 'w', encoding='utf-8').write(html)
print("✓ index.html re-saved as clean UTF-8")

# ══════════════════════════════════════════════════════════════
# FIX 2 — app.py: fix open() encoding + add missing routes
# ══════════════════════════════════════════════════════════════
print("\nReading app.py...")
shutil.copy('app.py', f'app.py.bak.{BACK}')
src = open('app.py', 'r', encoding='utf-8', errors='replace').read()

# Fix the / route encoding bug
BROKEN_PATTERNS = [
    "open(os.path.join(os.path.dirname(__file__), 'index.html'), 'r') as f",
    "with  as f:",
    "open(os.path.join(os.path.dirname(__file__), 'index.html'), 'r', 'utf-8') as f",
]
CORRECT = "open(os.path.join(os.path.dirname(__file__), 'index.html'), 'r', encoding='utf-8') as f"

fixed_encoding = False
for pat in BROKEN_PATTERNS:
    if pat in src:
        src = src.replace(pat, CORRECT)
        fixed_encoding = True
        print(f"✓ Fixed encoding: replaced '{pat[:50]}...'")

if not fixed_encoding:
    # Check if already correct
    if "encoding='utf-8'" in src and 'index.html' in src:
        print("✓ Encoding already correct")
    else:
        # Nuclear: find and replace the whole index route
        src = src.replace(
            "@app.route('/')\ndef index():",
            "@app.route('/')\ndef index():\n    # encoding fixed"
        )
        src = src.replace(
            "    with open(os.path.join(os.path.dirname(__file__), 'index.html')",
            "    with open(os.path.join(os.path.dirname(__file__), 'index.html'), encoding='utf-8'"
        )
        print("✓ Applied nuclear encoding fix")

# ── NEW ROUTES to append ──────────────────────────────────────
NEW_ROUTES = '''

# ── CASCADE LINKS (frontend-compatible URLs) ──────────────────────────────
# Frontend calls /api/cascade  (not /api/cascade_links)

@app.route('/api/cascade', methods=['GET', 'POST'])
def cascade_api():
    db = get_db()
    if request.method == 'GET':
        rows = db.execute("""
            SELECT cl.*,
              se.name  as sup_name,  se.emp_code as sup_code,
              sub.name as sub_name, sub.emp_code as sub_code,
              cp.ref   as cp_ref,   cp.title     as cp_title,
              mp.ref   as mp_ref,   mp.title     as mp_title
            FROM cascade_links cl
            LEFT JOIN employees se   ON cl.superior_emp_id    = se.id
            LEFT JOIN employees sub  ON cl.subordinate_emp_id = sub.id
            LEFT JOIN cps       cp   ON cl.superior_cp_id     = cp.id
            LEFT JOIN mps       mp   ON cl.subordinate_mp_id  = mp.id
            ORDER BY se.name
        """).fetchall()
        return jsonify(R(rows))

    d = request.json or {}
    # Support both field naming conventions from frontend
    sup_emp  = d.get('superior_emp_id') or d.get('sup_emp_id') or d.get('parent_emp_id')
    sup_cp   = d.get('superior_cp_id')  or d.get('sup_cp_id')  or d.get('cp_id')
    sub_emp  = d.get('subordinate_emp_id') or d.get('sub_emp_id') or d.get('child_emp_id')
    sub_mp   = d.get('subordinate_mp_id') or d.get('sub_mp_id') or d.get('mp_id') or ''

    if not sup_emp or not sup_cp or not sub_emp:
        return jsonify({'error': 'Missing required fields: superior_emp_id, superior_cp_id, subordinate_emp_id'}), 400

    # Duplicate check
    existing = db.execute(
        'SELECT id FROM cascade_links WHERE superior_cp_id=? AND subordinate_emp_id=?',
        (sup_cp, sub_emp)
    ).fetchone()
    if existing:
        return jsonify({'error': 'Link already exists', 'id': existing['id']}), 409

    auto_created = 0
    sub_mp = sub_mp.strip()
    if not sub_mp:
        cp = db.execute('SELECT * FROM cps WHERE id=?', (sup_cp,)).fetchone()
        if not cp:
            # Try by ref
            cp = db.execute('SELECT * FROM cps WHERE ref=?', (sup_cp,)).fetchone()
        if cp:
            new_ref   = f"AUTO-{cp['ref']}"
            new_title = f"[Auto] {cp['title']}"
            ex_mp = db.execute('SELECT id FROM mps WHERE ref=?', (new_ref,)).fetchone()
            if ex_mp:
                sub_mp = ex_mp['id']
            else:
                sub_mp = uid()
                db.execute('INSERT INTO mps VALUES(?,?,?,?,?,?,?,?)',
                           (sub_mp, new_ref, new_title, cp['target'], cp['freq'], 0, 0, 0))
                db.execute('INSERT OR IGNORE INTO mp_owners VALUES(?,?)', (sub_mp, sub_emp))
            auto_created = 1

    link_id = uid()
    db.execute('INSERT INTO cascade_links VALUES(?,?,?,?,?,?,?)',
               (link_id, sup_emp, sup_cp, sub_emp, sub_mp, auto_created,
                datetime.datetime.now().isoformat()))
    db.commit()
    return jsonify({
        'id': link_id, 'subordinate_mp_id': sub_mp,
        'auto_created': bool(auto_created), 'ok': True
    })


@app.route('/api/cascade/<lid>', methods=['DELETE'])
def cascade_del(lid):
    db = get_db()
    row = db.execute('SELECT * FROM cascade_links WHERE id=?', (lid,)).fetchone()
    if not row: return jsonify({'error': 'Not found'}), 404
    if row['auto_created']:
        db.execute('DELETE FROM mps WHERE id=?', (row['subordinate_mp_id'],))
        db.execute('DELETE FROM mp_owners WHERE mp_id=?', (row['subordinate_mp_id'],))
    db.execute('DELETE FROM cascade_links WHERE id=?', (lid,))
    db.commit()
    return jsonify({'ok': True})


@app.route('/api/cascade/tree')
def cascade_tree():
    db  = get_db()
    eid = request.args.get('emp_id')

    # Build tree: emp → roles → mps → cps → cascade children
    emp_q = "SELECT * FROM employees" + (" WHERE id=?" if eid else "") + " ORDER BY level, name"
    emps  = R(db.execute(emp_q, (eid,) if eid else ()).fetchall())

    links = R(db.execute("""
        SELECT cl.*,
          se.name as sup_name, sub.name as sub_name,
          cp.ref as cp_ref, cp.title as cp_title,
          mp.ref as mp_ref
        FROM cascade_links cl
        LEFT JOIN employees se  ON cl.superior_emp_id    = se.id
        LEFT JOIN employees sub ON cl.subordinate_emp_id = sub.id
        LEFT JOIN cps cp        ON cl.superior_cp_id     = cp.id
        LEFT JOIN mps mp        ON cl.subordinate_mp_id  = mp.id
    """).fetchall())

    # Index links by superior_cp_id for fast lookup
    by_cp = {}
    for lnk in links:
        key = lnk['superior_cp_id']
        by_cp.setdefault(key, []).append(lnk)

    tree = []
    for emp in emps:
        eid_  = emp['id']
        roles = R(db.execute("""
            SELECT r.* FROM roles r
            JOIN emp_roles er ON r.id = er.role_id
            WHERE er.emp_id=?
        """, (eid_,)).fetchall())

        role_nodes = []
        for role in roles:
            mps_ = R(db.execute("""
                SELECT m.* FROM mps m
                JOIN role_mps rm ON m.id = rm.mp_id
                WHERE rm.role_id=?
            """, (role['id'],)).fetchall())

            mp_nodes = []
            for mp in mps_:
                cps_ = R(db.execute("""
                    SELECT c.* FROM cps c WHERE c.mp_id=?
                """, (mp['id'],)).fetchall())

                cp_nodes = []
                for cp in cps_:
                    children = by_cp.get(cp['id'], [])
                    cp_nodes.append({**cp, 'cascade_children': children})

                mp_nodes.append({**mp, 'cps': cp_nodes})
            role_nodes.append({**role, 'mps': mp_nodes})

        tree.append({**emp, 'roles': role_nodes})

    return jsonify({'tree': tree, 'links': links})


@app.route('/api/org/cascade_assign', methods=['POST'])
def cascade_assign():
    """Alternative cascade creation endpoint used by org chart view"""
    d       = request.json or {}
    sup_emp = d.get('parent_emp_id') or d.get('superior_emp_id')
    cp_id   = d.get('cp_id') or d.get('superior_cp_id')
    sub_emp = d.get('child_emp_id') or d.get('subordinate_emp_id')
    sub_mp  = d.get('mp_id') or d.get('subordinate_mp_id') or ''

    if not sup_emp or not cp_id or not sub_emp:
        return jsonify({'error': 'Missing fields'}), 400

    # Reuse the cascade_api logic via internal call
    from flask import current_app
    with current_app.test_request_context(
        '/api/cascade',
        method='POST',
        json={
            'superior_emp_id':    sup_emp,
            'superior_cp_id':     cp_id,
            'subordinate_emp_id': sub_emp,
            'subordinate_mp_id':  sub_mp,
        }
    ):
        db = get_db()
        existing = db.execute(
            'SELECT id FROM cascade_links WHERE superior_cp_id=? AND subordinate_emp_id=?',
            (cp_id, sub_emp)
        ).fetchone()
        if existing:
            return jsonify({'ok': True, 'id': existing['id'], 'existing': True})

        auto_created = 0
        if not sub_mp.strip():
            cp = db.execute('SELECT * FROM cps WHERE id=?', (cp_id,)).fetchone()
            if cp:
                new_ref = f"AUTO-{cp['ref']}"
                ex_mp   = db.execute('SELECT id FROM mps WHERE ref=?', (new_ref,)).fetchone()
                if ex_mp:
                    sub_mp = ex_mp['id']
                else:
                    sub_mp = uid()
                    db.execute('INSERT INTO mps VALUES(?,?,?,?,?,?,?,?)',
                               (sub_mp, new_ref, f"[Auto] {cp['title']}",
                                cp['target'], cp['freq'], 0, 0, 0))
                    db.execute('INSERT OR IGNORE INTO mp_owners VALUES(?,?)', (sub_mp, sub_emp))
                auto_created = 1

        lid = uid()
        db.execute('INSERT INTO cascade_links VALUES(?,?,?,?,?,?,?)',
                   (lid, sup_emp, cp_id, sub_emp, sub_mp, auto_created,
                    datetime.datetime.now().isoformat()))
        db.commit()
        return jsonify({'ok': True, 'id': lid, 'auto_created': bool(auto_created)})
'''

# Only append if routes not already there
if '/api/cascade_assign' not in src and "'/api/cascade'" not in src:
    # Insert before the last if __name__ block
    if "if __name__=='__main__':" in src:
        src = src.replace("if __name__=='__main__':", NEW_ROUTES + "\nif __name__=='__main__':")
    elif 'if __name__ == ' in src:
        src = src.replace("if __name__ == '__main__':", NEW_ROUTES + "\nif __name__ == '__main__':")
    else:
        src += NEW_ROUTES
    print("✓ Added /api/cascade, /api/cascade/tree, /api/org/cascade_assign routes")
else:
    print("✓ Cascade routes already present — skipping")

# ── Also ensure cascade_links table exists in SCHEMA ─────────────────────
CASCADE_TABLE = """CREATE TABLE IF NOT EXISTS cascade_links(
  id TEXT PRIMARY KEY,
  superior_emp_id    TEXT NOT NULL,
  superior_cp_id     TEXT NOT NULL,
  subordinate_emp_id TEXT NOT NULL,
  subordinate_mp_id  TEXT DEFAULT '',
  auto_created       INTEGER DEFAULT 0,
  created_at         TEXT DEFAULT '');"""

if 'cascade_links' not in src:
    src = src.replace(
        'CREATE TABLE IF NOT EXISTS perf_cache(',
        CASCADE_TABLE + '\nCREATE TABLE IF NOT EXISTS perf_cache('
    )
    print("✓ cascade_links table added to SCHEMA")
else:
    print("✓ cascade_links table already in SCHEMA")

# ── Write app.py ──────────────────────────────────────────────
open('app.py', 'w', encoding='utf-8').write(src)
print("✓ app.py saved")

# ── Verify ────────────────────────────────────────────────────
print("\n── Verifying ──────────────────────────────────")
lines = open('app.py', encoding='utf-8').readlines()
routes = [l.strip() for l in lines if '@app.route' in l]
print(f"Total lines: {len(lines)}")
print(f"Total routes: {len(routes)}")

# Check encoding fix
enc_ok = any("encoding='utf-8'" in l and 'index.html' in l for l in lines)
print(f"Encoding fix: {'✓ OK' if enc_ok else '❌ STILL MISSING'}")

# Check cascade routes
casc_ok = any('/api/cascade' in l for l in lines)
print(f"Cascade routes: {'✓ Present' if casc_ok else '❌ Missing'}")

# Syntax check
import subprocess, sys
result = subprocess.run([sys.executable, '-m', 'py_compile', 'app.py'],
                        capture_output=True, text=True)
if result.returncode == 0:
    print("Syntax check: ✓ No errors")
else:
    print(f"Syntax check: ❌ ERROR\n{result.stderr}")

print("""
══════════════════════════════════════════════
  All fixes applied. Now run:

  git add app.py index.html
  git commit -m "fix: cascade routes, UTF-8 encoding"
  git push origin main
  python app.py
══════════════════════════════════════════════
""")
