
with open('app.py','r',encoding='utf-8') as f: c=f.read()

# Add API route to fetch audit log
audit_route = '''
@app.route('/api/audit_log')
def get_audit_log():
    err = require_role('master_admin')
    if err: return err
    db = get_master_conn()
    rows = db.execute(
        "SELECT * FROM audit_log ORDER BY ts DESC LIMIT 200"
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

'''

if '/api/audit_log' not in c:
    # Insert before admin panel route
    idx = c.find("\n@app.route('/admin')")
    if idx < 0: idx = c.find("\ndef admin_panel()")
    c = c[:idx] + audit_route + c[idx:]
    print('Audit log API route added')
else:
    print('Audit route already exists')

with open('app.py','w',encoding='utf-8') as f: f.write(c)
