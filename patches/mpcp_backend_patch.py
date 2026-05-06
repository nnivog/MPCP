"""
MPCP Backend Patch — append these to app.py (or merge into existing routes)
Fixes:
  1. Cascade Links API (was missing — causing 404)
  2. FY auto-detection from AD date
  3. Quick Performance Entry (with dual-mode: count OR percent)
  4. Duplicate perf prevention
  5. SQL-based analytics (replaces Python-loop aggregation)
  6. Input validation helper
  7. Global JSON error handler (stops HTML 404 leaking to frontend)
"""

# ── PASTE THIS BLOCK AT THE TOP OF app.py (after imports) ─────────────────

import datetime, functools

def validate_required(data, *fields):
    """Returns list of missing field names."""
    return [f for f in fields if not data.get(f)]

def json_error(msg, code=400):
    from flask import jsonify
    return jsonify({'error': msg}), code

# ── ADD TO SCHEMA string ───────────────────────────────────────────────────
CASCADE_SCHEMA = """
CREATE TABLE IF NOT EXISTS cascade_links(
  id       TEXT PRIMARY KEY,
  superior_emp_id   TEXT NOT NULL,
  superior_cp_id    TEXT NOT NULL,
  subordinate_emp_id TEXT NOT NULL,
  subordinate_mp_id  TEXT DEFAULT '',
  auto_created       INTEGER DEFAULT 0,
  created_at         TEXT DEFAULT ''
);
"""
# In init_db(), add: db.executescript(CASCADE_SCHEMA)


# ── GLOBAL JSON ERROR HANDLER (add near app = Flask(__name__)) ─────────────
"""
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Route not found', 'path': request.path}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': str(e)}), 500
"""

# ══════════════════════════════════════════════════════════════════════════
# 1. CASCADE LINKS  —  replaces missing route causing HTTP 404
# ══════════════════════════════════════════════════════════════════════════

"""
@app.route('/api/cascade_links', methods=['GET', 'POST'])
def cascade_links_api():
    db = get_db()
    if request.method == 'GET':
        rows = db.execute('''
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
        ''').fetchall()
        return jsonify(R(rows))

    d = request.json or {}
    missing = validate_required(d, 'superior_emp_id', 'superior_cp_id', 'subordinate_emp_id')
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}")

    # Prevent duplicate cascade link
    existing = db.execute(
        'SELECT id FROM cascade_links WHERE superior_cp_id=? AND subordinate_emp_id=?',
        (d['superior_cp_id'], d['subordinate_emp_id'])
    ).fetchone()
    if existing:
        return json_error('Cascade link already exists for this CP → Employee pair', 409)

    sub_mp_id = d.get('subordinate_mp_id', '').strip()
    auto_created = 0

    # Auto-create MP from CP if blank
    if not sub_mp_id:
        cp = db.execute('SELECT * FROM cps WHERE id=?', (d['superior_cp_id'],)).fetchone()
        if cp:
            new_mp_ref  = f"AUTO-{cp['ref']}"
            new_mp_title = f"[Auto] {cp['title']}"
            existing_mp = db.execute('SELECT id FROM mps WHERE ref=?', (new_mp_ref,)).fetchone()
            if existing_mp:
                sub_mp_id = existing_mp['id']
            else:
                sub_mp_id = uid()
                db.execute(
                    'INSERT INTO mps VALUES(?,?,?,?,?,?,?,?)',
                    (sub_mp_id, new_mp_ref, new_mp_title,
                     cp['target'], cp['freq'], 0, 0, 0)
                )
                db.execute('INSERT OR IGNORE INTO mp_owners VALUES(?,?)',
                           (sub_mp_id, d['subordinate_emp_id']))
            auto_created = 1

    link_id = uid()
    db.execute(
        'INSERT INTO cascade_links VALUES(?,?,?,?,?,?,?)',
        (link_id, d['superior_emp_id'], d['superior_cp_id'],
         d['subordinate_emp_id'], sub_mp_id, auto_created,
         datetime.datetime.now().isoformat())
    )
    db.commit()
    return jsonify({'id': link_id, 'subordinate_mp_id': sub_mp_id, 'auto_created': bool(auto_created)})


@app.route('/api/cascade_links/<lid>', methods=['DELETE'])
def cascade_link_del(lid):
    db = get_db()
    row = db.execute('SELECT * FROM cascade_links WHERE id=?', (lid,)).fetchone()
    if not row:
        return json_error('Link not found', 404)
    if row['auto_created']:
        db.execute('DELETE FROM mps WHERE id=?', (row['subordinate_mp_id'],))
        db.execute('DELETE FROM mp_owners WHERE mp_id=?', (row['subordinate_mp_id'],))
    db.execute('DELETE FROM cascade_links WHERE id=?', (lid,))
    db.commit()
    return jsonify({'ok': True})
"""


# ══════════════════════════════════════════════════════════════════════════
# 2. FY AUTO-DETECTION FROM AD DATE
# ══════════════════════════════════════════════════════════════════════════
"""
# Nepali FY runs Shrawan→Ashadh (roughly Jul 16 → Jul 15 next year)
FY_MAP = [
    (datetime.date(2022, 7, 17), datetime.date(2023, 7, 16), "2079-80"),
    (datetime.date(2023, 7, 17), datetime.date(2024, 7, 15), "2080-81"),
    (datetime.date(2024, 7, 16), datetime.date(2025, 7, 15), "2081-82"),
    (datetime.date(2025, 7, 16), datetime.date(2026, 7, 15), "2082-83"),
    (datetime.date(2026, 7, 16), datetime.date(2027, 7, 15), "2083-84"),
]

def ad_date_to_fy_and_month(dt):
    d = dt.date() if isinstance(dt, datetime.datetime) else dt
    for start, end, fy in FY_MAP:
        if start <= d <= end:
            return fy, AD_TO_BS.get(dt.strftime('%B'), 'Shrawan')
    return '2081-82', 'Shrawan'  # fallback

@app.route('/api/fy_from_date')
def fy_from_date():
    date_str = request.args.get('date', '')
    try:
        dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        fy, bs_month = ad_date_to_fy_and_month(dt)
        return jsonify({'fy': fy, 'bs_month': bs_month, 'quarter': bs_q(bs_month)})
    except Exception as e:
        return json_error(f'Invalid date: {e}')
"""


# ══════════════════════════════════════════════════════════════════════════
# 3. QUICK PERFORMANCE ENTRY — replaces broken /api/perf/quick
#    Supports two input modes:
#    Mode A: total + compliant_count  → system calcs nc, pct
#    Mode B: total + pct_achieved     → system calcs compliant, nc
# ══════════════════════════════════════════════════════════════════════════
"""
@app.route('/api/perf/quick', methods=['POST'])
def perf_quick():
    d = request.json or {}
    missing = validate_required(d, 'date', 'emp_code', 'cp_ref')
    if missing:
        return json_error(f"Required: {', '.join(missing)}")

    db = get_db()

    # Resolve employee
    ec = str(d['emp_code']).strip()
    emp = db.execute('SELECT * FROM employees WHERE emp_code=?', (ec,)).fetchone()
    if not emp:
        return json_error(f'Employee not found: {ec}')
    eid = emp['id']

    # Resolve CP + linked MP
    cp = db.execute('SELECT * FROM cps WHERE ref=?', (d['cp_ref'],)).fetchone()
    if not cp:
        return json_error(f'CP not found: {d["cp_ref"]}')
    mp_ref = ''
    if cp['mp_id']:
        mp = db.execute('SELECT ref FROM mps WHERE id=?', (cp['mp_id'],)).fetchone()
        if mp: mp_ref = mp['ref']

    # FY + BS month from date
    try:
        dt = datetime.datetime.strptime(d['date'], '%Y-%m-%d')
        fy, bsm = ad_date_to_fy_and_month(dt)
    except:
        return json_error('Invalid date format. Use YYYY-MM-DD')

    # Compute totals based on input mode
    total = int(d.get('total', 0) or 0)
    if total <= 0:
        return json_error('Total must be a positive number')

    mode = d.get('mode', 'count')  # 'count' or 'percent'
    if mode == 'percent':
        pct_c = float(d.get('pct_achieved', 0) or 0)
        if not (0 <= pct_c <= 100):
            return json_error('Percentage must be 0–100')
        compliant = round(total * pct_c / 100)
    else:
        compliant = int(d.get('compliant', 0) or 0)
        if compliant > total:
            return json_error('Compliant count cannot exceed total')
        pct_c = round(compliant / total * 100, 2)

    nc = total - compliant
    pct_nc = round(nc / total * 100, 2)
    actual_val = float(d.get('actual_val', 0) or 0)
    tgt_val    = float(cp['target'].replace('Days', '').replace('%', '').strip()
                       if cp['target'].replace('Days','').replace('%','').strip().replace('.','').isdigit()
                       else 0)
    unit = d.get('unit', cp['target'].split()[-1] if cp['target'] else '%')
    status = calc_status(actual_val, tgt_val, unit)

    # DUPLICATE CHECK — prevent re-entry for same emp+cp+month+fy
    existing = db.execute(
        'SELECT id FROM perf WHERE fy=? AND bs_month=? AND emp_id=? AND cp_ref=?',
        (fy, bsm, eid, d['cp_ref'])
    ).fetchone()
    if existing and not d.get('overwrite'):
        return jsonify({
            'warning': 'duplicate',
            'message': f'Record already exists for {ec} / {d["cp_ref"]} / {bsm} {fy}',
            'existing_id': existing['id'],
            'hint': 'Send overwrite=true to replace'
        }), 409

    pid = existing['id'] if existing else uid()
    db.execute(
        'INSERT OR REPLACE INTO perf VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        (pid, fy, bsm, bs_q(bsm), eid, ec, mp_ref, d['cp_ref'],
         d.get('metric', cp['title'][:60]),
         total, compliant, nc, pct_c, pct_nc,
         tgt_val, actual_val, unit, status, d.get('notes', ''))
    )
    _upd_cache(db, fy)
    db.commit()
    return jsonify({
        'id': pid, 'fy': fy, 'bs_month': bsm,
        'total': total, 'compliant': compliant, 'nc': nc,
        'pct_compliant': pct_c, 'status': status
    })
"""


# ══════════════════════════════════════════════════════════════════════════
# 4. SQL-BASED ANALYTICS (replaces Python-loop version — faster, scalable)
# ══════════════════════════════════════════════════════════════════════════
"""
@app.route('/api/analytics/summary_v2')
def analytics_summary_v2():
    db  = get_db()
    fys = request.args.get('fys', '')
    flist = [x.strip() for x in fys.split(',') if x.strip()]
    placeholders = ','.join('?' * len(flist)) if flist else "''"

    base_where = f"WHERE fy IN ({placeholders})" if flist else ""

    # Overall per FY
    by_fy = db.execute(f'''
        SELECT fy,
          SUM(total) as total, SUM(compliant) as compliant, SUM(non_compliant) as nc,
          ROUND(SUM(compliant)*100.0 / NULLIF(SUM(total),0), 2) as pct_c,
          ROUND(SUM(non_compliant)*100.0 / NULLIF(SUM(total),0), 2) as pct_nc
        FROM perf {base_where}
        GROUP BY fy ORDER BY fy
    ''', flist).fetchall()

    # By month
    by_month = db.execute(f'''
        SELECT fy, bs_month, quarter,
          SUM(total) as total, SUM(compliant) as compliant,
          ROUND(SUM(compliant)*100.0 / NULLIF(SUM(total),0), 2) as pct_c
        FROM perf {base_where}
        GROUP BY fy, bs_month ORDER BY fy, bs_month
    ''', flist).fetchall()

    # By MP
    by_mp = db.execute(f'''
        SELECT fy, mp_ref,
          SUM(total) as total, SUM(compliant) as compliant,
          ROUND(SUM(compliant)*100.0 / NULLIF(SUM(total),0), 2) as pct_c
        FROM perf {base_where} AND mp_ref != ''
        GROUP BY fy, mp_ref ORDER BY fy, mp_ref
    ''', flist).fetchall()

    # By CP
    by_cp = db.execute(f'''
        SELECT fy, mp_ref, cp_ref,
          SUM(total) as total, SUM(compliant) as compliant,
          ROUND(SUM(compliant)*100.0 / NULLIF(SUM(total),0), 2) as pct_c
        FROM perf {base_where} AND cp_ref != ''
        GROUP BY fy, mp_ref, cp_ref ORDER BY fy, mp_ref, cp_ref
    ''', flist).fetchall()

    # By Employee
    by_emp = db.execute(f'''
        SELECT fy, emp_code, emp_id,
          SUM(total) as total, SUM(compliant) as compliant,
          ROUND(SUM(compliant)*100.0 / NULLIF(SUM(total),0), 2) as pct_c
        FROM perf {base_where} AND emp_code != ''
        GROUP BY fy, emp_code ORDER BY fy, emp_code
    ''', flist).fetchall()

    return jsonify({
        'by_fy':    R(by_fy),
        'by_month': R(by_month),
        'by_mp':    R(by_mp),
        'by_cp':    R(by_cp),
        'by_emp':   R(by_emp),
    })
"""
