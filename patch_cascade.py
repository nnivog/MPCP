with open('app.py','r',encoding='utf-8') as f: c=f.read()

if 'def cascade_link_detail' in c:
    print('Route already exists'); exit()

put_route = (
    "\n@app.route('/api/cascade_links/<lid>', methods=['PUT','DELETE'])\n"
    "def cascade_link_detail(lid):\n"
    "    db = get_db()\n"
    "    if request.method == 'DELETE':\n"
    "        db.execute('DELETE FROM cascade_links WHERE id=?', (lid,))\n"
    "        db.commit(); return jsonify({'ok': True})\n"
    "    d = request.json or {}\n"
    "    missing = validate_required(d, 'superior_emp_id', 'superior_cp_id', 'subordinate_emp_id')\n"
    "    if missing: return json_error(f\"Missing: {', '.join(missing)}\")\n"
    "    sub_mp_id = d.get('subordinate_mp_id','').strip()\n"
    "    if not sub_mp_id:\n"
    "        cp = db.execute('SELECT * FROM cps WHERE id=?', (d['superior_cp_id'],)).fetchone()\n"
    "        if cp:\n"
    "            new_ref = 'AUTO-'+cp['ref']\n"
    "            ex_mp = db.execute('SELECT id FROM mps WHERE ref=?', (new_ref,)).fetchone()\n"
    "            if ex_mp: sub_mp_id = ex_mp['id']\n"
    "    db.execute(\n"
    "        'UPDATE cascade_links SET superior_emp_id=?,superior_cp_id=?,subordinate_emp_id=?,subordinate_mp_id=? WHERE id=?',\n"
    "        (d['superior_emp_id'],d['superior_cp_id'],d['subordinate_emp_id'],sub_mp_id,lid))\n"
    "    db.commit()\n"
    "    return jsonify({'ok': True})\n"
)

idx = c.find('def cascade_links_api():')
if idx != -1:
    next_route = c.find('\n@app.route', idx)
    c = c[:next_route] + '\n' + put_route + c[next_route:]
    print('✓ PUT/DELETE /api/cascade_links/<lid> added')
else:
    c = c.replace("if __name__ == '__main__':", put_route + "\nif __name__ == '__main__':")
    print('✓ Route added before __main__')

with open('app.py','w',encoding='utf-8') as f: f.write(c)
