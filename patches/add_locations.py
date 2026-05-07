import re

with open('app.py', 'r', encoding='utf-8') as f:
    txt = f.read()

# ── 1. Find the SCHEMA string and add locations tables ──
loc_tables = (
    "CREATE TABLE IF NOT EXISTS locations(\n"
    "  id TEXT PRIMARY KEY,\n"
    "  code TEXT UNIQUE NOT NULL,\n"
    "  name TEXT NOT NULL,\n"
    "  address TEXT DEFAULT '',\n"
    "  type TEXT DEFAULT 'Branch',\n"
    "  dept TEXT DEFAULT 'Ops',\n"
    "  active INTEGER DEFAULT 1\n"
    ");\n"
    "CREATE TABLE IF NOT EXISTS location_employees(\n"
    "  loc_id TEXT,\n"
    "  emp_id TEXT,\n"
    "  PRIMARY KEY(loc_id, emp_id)\n"
    ");\n"
)

if 'CREATE TABLE IF NOT EXISTS locations' not in txt:
    txt = txt.replace(
        'CREATE TABLE IF NOT EXISTS perf_cache(',
        loc_tables + 'CREATE TABLE IF NOT EXISTS perf_cache('
    )
    print("Added locations schema")
else:
    print("locations schema already present")

# ── 2. Add seed data after emp_roles seed ──
seed_marker = 'db.executemany("INSERT OR IGNORE INTO emp_roles VALUES(?,?)",emp_roles)'
seed_locs = (
    "\n"
    "    if not db.execute('SELECT 1 FROM locations LIMIT 1').fetchone():\n"
    "        locs = [\n"
    "            ('loc1','KTM-HQ','Kathmandu HQ','Sipradi Trading, Naxal, Kathmandu','HQ','HOD',1),\n"
    "            ('loc2','BRT-BR','Birgunj Branch','Sipradi Trading, Birgunj','Branch','Vehicle',1),\n"
    "            ('loc3','BRD-BR','Bhairahawa Branch','Sipradi Trading, Bhairahawa','Branch','Vehicle',1),\n"
    "            ('loc4','PKH-BR','Pokhara Branch','Sipradi Trading, Pokhara','Branch','Ops',1),\n"
    "            ('loc5','ITA-BR','Itahari Branch','Sipradi Trading, Itahari','Branch','Warehouse',1),\n"
    "        ]\n"
    "        db.executemany(\n"
    "            'INSERT OR IGNORE INTO locations(id,code,name,address,type,dept,active) VALUES(?,?,?,?,?,?,?)',\n"
    "            locs\n"
    "        )\n"
)

if 'INSERT OR IGNORE INTO locations' not in txt:
    if seed_marker in txt:
        txt = txt.replace(seed_marker, seed_marker + seed_locs)
        print("Added seed locations")
    else:
        print("WARNING: seed marker not found - skipping seed")
else:
    print("seed locations already present")

# ── 3. Add Locations API routes ──
loc_api = '''

# ── LOCATIONS ──────────────────────────────────────────────────────────────

@app.route('/api/locations', methods=['GET', 'POST'])
def locations_api():
    db = get_db()
    if request.method == 'GET':
        rows = db.execute("SELECT * FROM locations ORDER BY code").fetchall()
        res = []
        for r in rows:
            loc = dict(r)
            loc['emp_ids'] = [
                x['emp_id'] for x in
                db.execute("SELECT emp_id FROM location_employees WHERE loc_id=?", (r['id'],))
            ]
            res.append(loc)
        return jsonify(res)
    d = request.json
    lid     = d.get('id') or uid()
    code    = d.get('code', '').strip()
    name    = d.get('name', '').strip()
    if not code or not name:
        return jsonify({'error': 'code and name required'}), 400
    address = d.get('address', '')
    ltype   = d.get('type', 'Branch')
    dept    = d.get('dept', 'Ops')
    active  = 1 if d.get('active', True) else 0
    db.execute(
        "INSERT OR REPLACE INTO locations(id,code,name,address,type,dept,active) VALUES(?,?,?,?,?,?,?)",
        (lid, code, name, address, ltype, dept, active)
    )
    db.execute("DELETE FROM location_employees WHERE loc_id=?", (lid,))
    for eid in d.get('emp_ids', []):
        db.execute("INSERT OR IGNORE INTO location_employees(loc_id,emp_id) VALUES(?,?)", (lid, eid))
    db.commit()
    return jsonify({'id': lid})


@app.route('/api/locations/<lid>', methods=['PUT', 'DELETE'])
def location_api(lid):
    db = get_db()
    if request.method == 'DELETE':
        db.execute("DELETE FROM locations WHERE id=?", (lid,))
        db.execute("DELETE FROM location_employees WHERE loc_id=?", (lid,))
        db.commit()
        return jsonify({'ok': True})
    d       = request.json
    code    = d.get('code', '').strip()
    name    = d.get('name', '').strip()
    address = d.get('address', '')
    ltype   = d.get('type', 'Branch')
    dept    = d.get('dept', 'Ops')
    active  = 1 if d.get('active', True) else 0
    db.execute(
        "UPDATE locations SET code=?,name=?,address=?,type=?,dept=?,active=? WHERE id=?",
        (code, name, address, ltype, dept, active, lid)
    )
    db.execute("DELETE FROM location_employees WHERE loc_id=?", (lid,))
    for eid in d.get('emp_ids', []):
        db.execute("INSERT OR IGNORE INTO location_employees(loc_id,emp_id) VALUES(?,?)", (lid, eid))
    db.commit()
    return jsonify({'ok': True})

'''

if 'def locations_api' not in txt:
    # Find a safe insertion point — before if __name__
    if "if __name__=='__main__':" in txt:
        txt = txt.replace("if __name__=='__main__':", loc_api + "if __name__=='__main__':")
        print("Added locations API")
    elif 'if __name__ ==' in txt:
        txt = re.sub(r"if __name__ ==", loc_api + "if __name__ ==", txt, count=1)
        print("Added locations API")
    else:
        txt = txt + loc_api
        print("Added locations API at end of file")
else:
    print("locations API already present")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(txt)

print("\nDone. Verifying...")

import ast
try:
    ast.parse(txt)
    print("Syntax check: PASSED")
except SyntaxError as e:
    print(f"Syntax check: FAILED at line {e.lineno} — {e.msg}")
