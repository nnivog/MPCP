with open('app.py', 'r', encoding='utf-8') as f:
    c = f.read()

tables = (
    "\nCREATE TABLE IF NOT EXISTS locations(\n"
    "  id TEXT PRIMARY KEY,\n"
    "  code TEXT UNIQUE NOT NULL,\n"
    "  name TEXT NOT NULL,\n"
    "  type TEXT DEFAULT 'Branch',\n"
    "  region TEXT DEFAULT '',\n"
    "  active INTEGER DEFAULT 1);\n\n"
    "CREATE TABLE IF NOT EXISTS sectors(\n"
    "  id TEXT PRIMARY KEY,\n"
    "  code TEXT UNIQUE NOT NULL,\n"
    "  name TEXT NOT NULL,\n"
    "  description TEXT DEFAULT '',\n"
    "  location_id TEXT DEFAULT '');\n"
)

routes = (
    "\n@app.route('/api/locations', methods=['GET', 'POST'])\n"
    "def locations_api():\n"
    "    db = get_db()\n"
    "    if request.method == 'GET':\n"
    "        return jsonify(R(db.execute('SELECT * FROM locations ORDER BY code').fetchall()))\n"
    "    d = request.json; lid = d.get('id') or uid()\n"
    "    db.execute('INSERT OR REPLACE INTO locations VALUES(?,?,?,?,?,?)',\n"
    "               (lid, d['code'], d['name'], d.get('type','Branch'), d.get('region',''), 1 if d.get('active', True) else 0))\n"
    "    db.commit(); return jsonify({'id': lid})\n\n"
    "@app.route('/api/locations/<lid>', methods=['PUT', 'DELETE'])\n"
    "def location_api(lid):\n"
    "    db = get_db()\n"
    "    if request.method == 'DELETE':\n"
    "        db.execute('DELETE FROM locations WHERE id=?', (lid,)); db.commit(); return jsonify({'ok': True})\n"
    "    d = request.json\n"
    "    db.execute('UPDATE locations SET code=?,name=?,type=?,region=?,active=? WHERE id=?',\n"
    "               (d['code'], d['name'], d.get('type','Branch'), d.get('region',''), 1 if d.get('active', True) else 0, lid))\n"
    "    db.commit(); return jsonify({'ok': True})\n\n"
    "@app.route('/api/sectors', methods=['GET', 'POST'])\n"
    "def sectors_api():\n"
    "    db = get_db()\n"
    "    if request.method == 'GET':\n"
    "        return jsonify(R(db.execute('SELECT * FROM sectors ORDER BY code').fetchall()))\n"
    "    d = request.json; sid = d.get('id') or uid()\n"
    "    db.execute('INSERT OR REPLACE INTO sectors VALUES(?,?,?,?,?)',\n"
    "               (sid, d['code'], d['name'], d.get('description',''), d.get('location_id','')))\n"
    "    db.commit(); return jsonify({'id': sid})\n\n"
    "@app.route('/api/sectors/<sid>', methods=['PUT', 'DELETE'])\n"
    "def sector_api(sid):\n"
    "    db = get_db()\n"
    "    if request.method == 'DELETE':\n"
    "        db.execute('DELETE FROM sectors WHERE id=?', (sid,)); db.commit(); return jsonify({'ok': True})\n"
    "    d = request.json\n"
    "    db.execute('UPDATE sectors SET code=?,name=?,description=?,location_id=? WHERE id=?',\n"
    "               (d['code'], d['name'], d.get('description',''), d.get('location_id',''), sid))\n"
    "    db.commit(); return jsonify({'ok': True})\n\n"
)

if 'CREATE TABLE IF NOT EXISTS locations' not in c:
    c = c.replace('CREATE TABLE IF NOT EXISTS perf_cache(', tables + 'CREATE TABLE IF NOT EXISTS perf_cache(')
    print("Tables added")
else:
    print("Tables already present")

if 'def locations_api' not in c:
    c = c.replace("if __name__=='__main__':", routes + "if __name__=='__main__':")
    print("Routes added")
else:
    print("Routes already present")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(c)
print("Done")
