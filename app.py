"""
Sipradi SC-MPCP Control System v3.0
Flask + SQLite | python app.py | http://localhost:5050
Patches: cascade_links API, perf/quick entry, FY auto-detect,
         duplicate guard, SQL analytics, global error handlers
"""

from flask import Flask, jsonify, request, send_file
import sqlite3, csv, io, os, json, datetime, random, string

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "scm.db")

@app.route('/api/analytics/summary_yoy')
def analytics_summary_yoy():
    """Returns analytics indexed by FY for YoY report."""
    db = get_db()
    all_fys = [r['fy'] for r in db.execute("SELECT DISTINCT fy FROM perf ORDER BY fy").fetchall()]
    result = {}
    for fy in all_fys:
        rows = R(db.execute("SELECT * FROM perf WHERE fy=?", (fy,)).fetchall())
        tot  = sum(r.get('total',1) for r in rows)
        comp = sum(r.get('compliant',0) for r in rows)
        nc   = tot-comp
        pct_c = round(comp/tot*100,2) if tot else 0
        pct_nc= round(nc/tot*100,2) if tot else 0
        # by_month
        by_month = {}
        for r in rows:
            m = r.get('bs_month','')
            by_month.setdefault(m,{'total':0,'compliant':0,'nc':0})
            by_month[m]['total']+=r.get('total',1)
            by_month[m]['compliant']+=r.get('compliant',0)
            by_month[m]['nc']+=r.get('non_compliant',0)
        # by_mp
        by_mp = {}
        for r in rows:
            ref = r.get('mp_ref','')
            if not ref: continue
            by_mp.setdefault(ref,{'total':0,'compliant':0,'nc':0})
            by_mp[ref]['total']+=r.get('total',1)
            by_mp[ref]['compliant']+=r.get('compliant',0)
            by_mp[ref]['nc']+=r.get('non_compliant',0)
        for ref in by_mp:
            t=by_mp[ref]['total']
            c=by_mp[ref]['compliant']
            by_mp[ref]['pct_c'] = round(c/t*100,2) if t else 0
        result[fy] = {'total':tot,'compliant':comp,'nc':nc,'pct_c':pct_c,'pct_nc':pct_nc,
                      'by_month':by_month,'by_mp':by_mp}
    return jsonify(result)
