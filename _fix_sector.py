with open('app.py','r',encoding='utf-8') as f: c=f.read()

if 'analytics_by_sector' in c:
    print('Route already exists - restarting app may fix it')
else:
    # Find a safe insertion point - before the first @app.route after by_location
    marker = "def analytics_by_location():"
    idx = c.find(marker)
    if idx < 0:
        print('ERROR: analytics_by_location not found')
    else:
        # Find end of that function
        next_route = c.find("\n@app.route", idx)
        insert = (
            "\n\n@app.route('/api/analytics/by_sector')\n"
            "def analytics_by_sector():\n"
            "    db = get_db()\n"
            "    fy = request.args.get('fy','')\n"
            "    params = []\n"
            "    sql = ('SELECT COALESCE(NULLIF(e.dept,chr(39)+chr(39)),chr(39)+'Unassigned'+chr(39)) grp,'\n"
        )
        # Simpler - just append the function as a string
        route_code = """

@app.route('/api/analytics/by_sector')
def analytics_by_sector():
    db = get_db()
    fy = request.args.get('fy','')
    params = []
    sql = (
        'SELECT COALESCE(NULLIF(e.dept,""),"Unassigned") grp,'
        ' COUNT(DISTINCT p.emp_code) emp_count,'
        ' COUNT(*) tot,'
        ' SUM(CASE WHEN p.status="C" THEN 1 ELSE 0 END) comp'
        ' FROM perf p'
        ' LEFT JOIN employees e ON e.emp_code=p.emp_code'
        ' WHERE 1=1'
    )
    if fy:
        sql += ' AND p.fy=?'
        params.append(fy)
    sql += ' GROUP BY 1 ORDER BY 1'
    rows = db.execute(sql, params).fetchall()
    result = {}
    for r in rows:
        tot = r[2] or 0
        comp = r[3] or 0
        grp = r[0] or 'Unassigned'
        result[grp] = {
            'name': grp,
            'emp_count': r[1] or 0,
            'total': tot,
            'compliant': comp,
            'nc': tot - comp,
            'pct': round(comp/tot*100, 1) if tot else 0,
            'color': '#475569'
        }
    return jsonify(result)

"""
        c = c[:next_route] + route_code + c[next_route:]
        with open('app.py','w',encoding='utf-8') as f: f.write(c)
        print('Route inserted at position', next_route)

