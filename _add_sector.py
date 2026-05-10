with open('app.py','r',encoding='utf-8') as f: c=f.read()

new_route = (
    "\n@app.route('/api/analytics/by_sector')\n"
    "def analytics_by_sector():\n"
    "    db = get_db()\n"
    "    fy = request.args.get('fy','')\n"
    "    params = []\n"
    "    sql = ('SELECT COALESCE(NULLIF(e.dept,\\'\\'),\\'Unassigned\\') grp,'\n"
    "           ' COUNT(DISTINCT p.emp_code) emp_count,'\n"
    "           ' COUNT(*) tot,'\n"
    "           ' SUM(CASE WHEN p.status=\\'C\\' THEN 1 ELSE 0 END) comp'\n"
    "           ' FROM perf p'\n"
    "           ' LEFT JOIN employees e ON e.emp_code=p.emp_code'\n"
    "           ' WHERE 1=1')\n"
    "    if fy:\n"
    "        sql += ' AND p.fy=?'; params.append(fy)\n"
    "    sql += ' GROUP BY 1 ORDER BY 1'\n"
    "    rows = db.execute(sql, params).fetchall()\n"
    "    result = {}\n"
    "    for r in rows:\n"
    "        tot = r[2] or 0; comp = r[3] or 0\n"
    "        grp = r[0] or 'Unassigned'\n"
    "        result[grp] = {\n"
    "            'name': grp, 'emp_count': r[1] or 0,\n"
    "            'total': tot, 'compliant': comp,\n"
    "            'nc': tot - comp,\n"
    "            'pct': round(comp/tot*100,1) if tot else 0,\n"
    "            'color': '#475569'\n"
    "        }\n"
    "    return jsonify(result)\n"
)

idx = c.find("def analytics_by_location()")
end = c.find("\n@app.route", idx)
if end > 0:
    c = c[:end] + new_route + c[end:]
    print('by_sector route added')
else:
    print('NOT FOUND')

with open('app.py','w',encoding='utf-8') as f: f.write(c)
