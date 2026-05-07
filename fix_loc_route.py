with open('app.py', 'r', encoding='utf-8') as f:
    txt = f.read()

import re

# Find and remove the entire broken locations API block
# It starts at @app.route('/api/locations' and ends before the next major section
idx_start = txt.find("# ── LOCATIONS")
if idx_start == -1:
    idx_start = txt.find("@app.route('/api/locations'")

# Find where it ends - look for next section comment or route after location_api
idx_end = txt.find("\n# ──", idx_start + 10)
if idx_end == -1:
    idx_end = txt.find("\n@app.route", txt.find("def location_api", idx_start) + 10)

print(f"Removing chars {idx_start} to {idx_end}")
print("REMOVED BLOCK PREVIEW:")
print(txt[idx_start:idx_end][:300])

# Clean replacement
loc_api = '''# ── LOCATIONS ─────────────────────────────────────────────────────────────

@app.route('/api/locations', methods=['GET','POST'])
def locations_api():
    db = get_db()
    # Ensure table exists with correct schema
    db.execute("""CREATE TABLE IF NOT EXISTS locations(
        id TEXT PRIMARY KEY,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        address TEXT DEFAULT '',
        type TEXT DEFAULT 'Branch',
        dept TEXT DEFAULT 'Ops',
        active INTEGER DEFAULT 1
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS location_employees(
        loc_id TEXT, emp_id TEXT, PRIMARY KEY(loc_id, emp_id)
    )""")
    # Add missing columns if upgrading from old schema
    existing = [r[1] for r in db.execute("PRAGMA table_info(locations)").fetchall()]
    if 'dept'   not in existing: db.execute("ALTER TABLE locations ADD COLUMN dept TEXT DEFAULT 'Ops'")
    if 'active' not in existing: db.execute("ALTER TABLE locations ADD COLUMN active INTEGER DEFAULT 1")
    db.commit()

    if request.method == 'GET':
        locs = R(db.execute("SELECT * FROM locations ORDER BY code").fetchall())
        for loc in locs:
            loc['emp_ids'] = [r['emp_id'] for r in db.execute(
                "SELECT emp_id FROM location_employees WHERE loc_id=?", (loc['id'],))]
        return jsonify(locs)

    d      = request.json or {}
    lid    = d.get('id') or uid()
    code   = d.get('code','').strip()
    name   = d.get('name','').strip()
    if not code or not name:
        return jsonify({'error':'code and name required'}), 400
    db.execute(
        "INSERT OR REPLACE INTO locations(id,code,name,address,type,dept,active) VALUES(?,?,?,?,?,?,?)",
        (lid, code, name, d.get('address',''), d.get('type','Branch'), d.get('dept','Ops'), 1 if d.get('active',True) else 0)
    )
    db.execute("DELETE FROM location_employees WHERE loc_id=?", (lid,))
    for eid in d.get('emp_ids',[]):
        db.execute("INSERT OR IGNORE INTO location_employees(loc_id,emp_id) VALUES(?,?)", (lid, eid))
    db.commit()
    return jsonify({'id': lid})


@app.route('/api/locations/<lid>', methods=['PUT','DELETE'])
def location_api(lid):
    db = get_db()
    if request.method == 'DELETE':
        db.execute("DELETE FROM locations WHERE id=?", (lid,))
        db.execute("DELETE FROM location_employees WHERE loc_id=?", (lid,))
        db.commit()
        return jsonify({'ok': True})
    d      = request.json or {}
    code   = d.get('code','').strip()
    name   = d.get('name','').strip()
    if not code or not name:
        return jsonify({'error':'code and name required'}), 400
    db.execute(
        "UPDATE locations SET code=?,name=?,address=?,type=?,dept=?,active=? WHERE id=?",
        (code, name, d.get('address',''), d.get('type','Branch'), d.get('dept','Ops'), 1 if d.get('active',True) else 0, lid)
    )
    db.execute("DELETE FROM location_employees WHERE loc_id=?", (lid,))
    for eid in d.get('emp_ids',[]):
        db.execute("INSERT OR IGNORE INTO location_employees(loc_id,emp_id) VALUES(?,?)", (lid, eid))
    db.commit()
    return jsonify({'ok': True})

'''

txt = txt[:idx_start] + loc_api + txt[idx_end:]

# Verify no syntax errors
import ast
try:
    ast.parse(txt)
    print("Syntax check: PASSED")
except SyntaxError as e:
    print(f"Syntax ERROR at line {e.lineno}: {e.msg}")
    print(f"Text: {e.text}")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(txt)

print("app.py fixed")
