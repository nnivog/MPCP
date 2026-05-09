with open('app.py','r',encoding='utf-8') as f: c=f.read()

# ── 1. Add imports ──────────────────────────────────────────────────────────
old_import = "from flask import Flask, jsonify, request, send_file"
new_import = "from flask import Flask, jsonify, request, send_file, session, redirect, render_template_string"
c = c.replace(old_import, new_import)

old_stdlib = "import sqlite3, csv, io, os, json, datetime, random, string"
new_stdlib = "import sqlite3, csv, io, os, json, datetime, random, string, hashlib, secrets"
c = c.replace(old_stdlib, new_stdlib)

# ── 2. Add SECRET_KEY + DATA_DIR after app = Flask(__name__) ───────────────
old_app = 'app = Flask(__name__)\nDB = os.path.join(os.path.dirname(__file__), "scm.db")'
new_app = '''app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# ── DATA DIR & DB PATHS ────────────────────────────────────────────────────
DATA_DIR   = os.environ.get('MPCP_DATA_DIR', os.path.join(os.path.dirname(__file__), 'data'))
os.makedirs(DATA_DIR, exist_ok=True)
MASTER_DB  = os.path.join(DATA_DIR, 'master.db')
DB         = os.path.join(os.path.dirname(__file__), 'scm.db')  # legacy fallback

def get_dept_db_path(dept_code):
    return os.path.join(DATA_DIR, f'{dept_code}.db')

def get_master_conn():
    c = sqlite3.connect(MASTER_DB)
    c.row_factory = sqlite3.Row
    return c

# ── PASSWORD UTILS ─────────────────────────────────────────────────────────
def hash_password(pw):
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), 260000)
    return salt + ':' + h.hex()

def verify_password(pw, stored):
    try:
        salt, h = stored.split(':',1)
        check = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), 260000)
        return check.hex() == h
    except: return False

# ── MASTER DB INIT ─────────────────────────────────────────────────────────
def init_master_db():
    db = get_master_conn()
    db.executescript("""
CREATE TABLE IF NOT EXISTS departments(
  id TEXT PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT '');

CREATE TABLE IF NOT EXISTS users(
  id TEXT PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  full_name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  dept_code TEXT DEFAULT NULL,
  emp_code TEXT DEFAULT '',
  active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT '');
""")
    # Create default master admin if no users exist
    existing = db.execute("SELECT COUNT(*) c FROM users").fetchone()['c']
    if existing == 0:
        import datetime as _dt
        pid = ''.join(random.choices(string.ascii_lowercase+string.digits, k=8))
        db.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?,?,?)",
            (pid,'admin', hash_password('admin123'),
             'Master Admin','master_admin',None,'',1,
             _dt.datetime.now().isoformat()))
        db.commit()
        print("  Created default admin user: admin / admin123")
    db.commit()
    db.close()

init_master_db()'''
c = c.replace(old_app, new_app)
print('✓ Imports, SECRET_KEY, DATA_DIR, master DB init added')

# ── 3. Replace get_db() with dept-aware routing ────────────────────────────
old_getdb = "def get_db():\n    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c"
new_getdb = '''def get_db(dept_override=None):
    """Return dept DB connection based on session role."""
    user = session.get('mpcp_user')
    # Allow unauthenticated access to /login and /static
    if not user:
        # Fallback to legacy DB for non-session contexts (CLI, tests)
        c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c
    role = user.get('role','user')
    if role == 'master_admin':
        dept = dept_override or request.args.get('dept') or user.get('active_dept')
        path = get_dept_db_path(dept) if dept else DB
    else:
        path = get_dept_db_path(user['dept_code'])
    if not os.path.exists(path):
        # Auto-init new dept DB with schema
        _init_dept_db(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def _init_dept_db(path):
    """Create a fresh department DB with full schema."""
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.commit(); conn.close()
    print(f"  Initialized new dept DB: {path}")

def current_user():
    return session.get('mpcp_user')

def require_role(*roles):
    """Check session role. Returns error response or None."""
    u = current_user()
    if not u: return jsonify({'error':'Not authenticated'}),401
    if roles and u.get('role') not in roles:
        return jsonify({'error':'Insufficient permissions'}),403
    return None

def perf_emp_filter(query, params):
    """Inject emp_code filter for user role."""
    u = current_user()
    if u and u.get('role') == 'user' and u.get('emp_code'):
        query += ' AND emp_code=?'
        params.append(u['emp_code'])
    return query, params'''

if old_getdb in c:
    c = c.replace(old_getdb, new_getdb)
    print('✓ get_db() replaced with dept-aware routing')
else:
    print('✗ get_db() not matched — check manually')

# ── 4. Add before_request middleware ───────────────────────────────────────
old_err = "# ── GLOBAL ERROR HANDLERS"
new_before = '''# ── AUTH MIDDLEWARE ───────────────────────────────────────────────────────
PUBLIC_PATHS = {'/login', '/logout', '/static'}

@app.before_request
def auth_guard():
    if request.path.startswith('/static'): return
    if request.path in ('/login','/logout'): return
    if not session.get('mpcp_user'):
        if request.path.startswith('/api/'):
            return jsonify({'error':'Not authenticated','redirect':'/login'}),401
        return redirect('/login')

# ── GLOBAL ERROR HANDLERS
'''
c = c.replace('# ── GLOBAL ERROR HANDLERS', new_before)
print('✓ before_request auth guard added')

# ── 5. Add LOGIN/LOGOUT + USER/DEPT API routes before __main__ ─────────────
auth_routes = '''
# ══════════════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ══════════════════════════════════════════════════════════════════════════

LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MPCP Login — Sipradi</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,sans-serif;background:#0a1628;min-height:100vh;display:flex;align-items:center;justify-content:center}
.card{background:#fff;border-radius:16px;padding:40px;width:360px;box-shadow:0 20px 60px rgba(0,0,0,.4)}
.logo{text-align:center;margin-bottom:24px}
.logo h1{font-size:22px;font-weight:900;color:#0a1628;letter-spacing:-0.5px}
.logo p{font-size:11px;color:#6b7a99;margin-top:4px}
.form-group{margin-bottom:16px}
label{display:block;font-size:11px;font-weight:700;color:#374151;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px}
input{width:100%;padding:10px 14px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:14px;outline:none;transition:.2s}
input:focus{border-color:#1d4ed8;box-shadow:0 0 0 3px #1d4ed820}
.btn{width:100%;padding:12px;background:#1d4ed8;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;margin-top:8px;transition:.2s}
.btn:hover{background:#1e40af}
.err{background:#fef2f2;border:1px solid #fecaca;color:#dc2626;padding:10px 14px;border-radius:8px;font-size:12px;margin-bottom:16px}
.dept{text-align:center;margin-top:16px;font-size:11px;color:#6b7a99}
</style></head><body>
<div class="card">
  <div class="logo">
    <h1>SC-MPCP System</h1>
    <p>Sipradi Trading Pvt. Ltd.</p>
  </div>
  {% if error %}<div class="err">{{ error }}</div>{% endif %}
  <form method="POST" action="/login">
    <div class="form-group"><label>Username</label>
      <input type="text" name="username" placeholder="Enter username" autofocus required></div>
    <div class="form-group"><label>Password</label>
      <input type="password" name="password" placeholder="Enter password" required></div>
    <button class="btn" type="submit">Sign In</button>
  </form>
  <div class="dept" id="dept-label"></div>
</div>
</body></html>"""

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username','').strip().lower()
        password = request.form.get('password','')
        db = get_master_conn()
        user = db.execute(
            "SELECT u.*,d.name dept_name FROM users u "
            "LEFT JOIN departments d ON d.code=u.dept_code "
            "WHERE u.username=? AND u.active=1", (username,)
        ).fetchone()
        db.close()
        if user and verify_password(password, user['password_hash']):
            session.permanent = True
            session['mpcp_user'] = {
                'id':        user['id'],
                'username':  user['username'],
                'full_name': user['full_name'],
                'role':      user['role'],
                'dept_code': user['dept_code'],
                'dept_name': user['dept_name'] or 'All Departments',
                'emp_code':  user['emp_code'] or '',
                'active_dept': user['dept_code']
            }
            return redirect('/')
        error = 'Invalid username or password'
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/api/auth/me')
def auth_me():
    u = current_user()
    if not u: return jsonify({'error':'Not authenticated'}),401
    return jsonify({k:v for k,v in u.items() if k!='password_hash'})

@app.route('/api/auth/switch_dept', methods=['POST'])
def switch_dept():
    err = require_role('master_admin')
    if err: return err
    dept = (request.json or {}).get('dept_code','')
    if dept:
        db = get_master_conn()
        exists = db.execute("SELECT id FROM departments WHERE code=?", (dept,)).fetchone()
        db.close()
        if not exists: return json_error('Department not found')
    u = session['mpcp_user'].copy()
    u['active_dept'] = dept or None
    session['mpcp_user'] = u
    return jsonify({'ok':True,'active_dept':dept})

# ── DEPARTMENT MANAGEMENT (master_admin only) ──────────────────────────────
@app.route('/api/departments', methods=['GET','POST'])
def departments_api():
    err = require_role('master_admin')
    if err: return err
    db = get_master_conn()
    if request.method == 'GET':
        rows = R(db.execute("SELECT * FROM departments ORDER BY name").fetchall())
        # Attach user count per dept
        for r in rows:
            r['user_count'] = db.execute(
                "SELECT COUNT(*) c FROM users WHERE dept_code=? AND active=1",
                (r['code'],)).fetchone()['c']
        db.close(); return jsonify(rows)
    d = request.json or {}
    if not d.get('code') or not d.get('name'):
        return json_error('code and name required')
    did = uid()
    db.execute("INSERT INTO departments VALUES(?,?,?,?,?)",
        (did, d['code'].lower().replace(' ','_'), d['name'], 1,
         datetime.datetime.now().isoformat()))
    # Auto-create the dept DB
    _init_dept_db(get_dept_db_path(d['code'].lower().replace(' ','_')))
    db.commit(); db.close()
    return jsonify({'id':did})

@app.route('/api/departments/<did>', methods=['PUT','DELETE'])
def department_api(did):
    err = require_role('master_admin')
    if err: return err
    db = get_master_conn()
    if request.method == 'DELETE':
        db.execute("UPDATE departments SET active=0 WHERE id=?", (did,))
        db.commit(); db.close(); return jsonify({'ok':True})
    d = request.json or {}
    db.execute("UPDATE departments SET name=?,active=? WHERE id=?",
        (d.get('name'), 1 if d.get('active',True) else 0, did))
    db.commit(); db.close(); return jsonify({'ok':True})

# ── USER MANAGEMENT (master_admin + dept_admin) ────────────────────────────
@app.route('/api/users', methods=['GET','POST'])
def users_api():
    err = require_role('master_admin','dept_admin')
    if err: return err
    u = current_user()
    db = get_master_conn()
    if request.method == 'GET':
        if u['role'] == 'master_admin':
            rows = R(db.execute(
                "SELECT u.id,u.username,u.full_name,u.role,u.dept_code,"
                "u.emp_code,u.active,u.created_at,d.name dept_name "
                "FROM users u LEFT JOIN departments d ON d.code=u.dept_code "
                "ORDER BY u.dept_code,u.full_name").fetchall())
        else:
            rows = R(db.execute(
                "SELECT u.id,u.username,u.full_name,u.role,u.dept_code,"
                "u.emp_code,u.active,u.created_at,d.name dept_name "
                "FROM users u LEFT JOIN departments d ON d.code=u.dept_code "
                "WHERE u.dept_code=? ORDER BY u.full_name",
                (u['dept_code'],)).fetchall())
        db.close(); return jsonify(rows)

    d = request.json or {}
    missing = validate_required(d,'username','password','full_name','role')
    if missing: return json_error(f"Missing: {', '.join(missing)}")
    # dept_admin can only create users in own dept
    dept_code = d.get('dept_code') or u.get('dept_code')
    if u['role']=='dept_admin': dept_code = u['dept_code']
    if d['role'] not in ('master_admin','dept_admin','user'):
        return json_error('Invalid role')
    new_id = uid()
    try:
        db.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?,?,?)",
            (new_id, d['username'].strip().lower(),
             hash_password(d['password']),
             d['full_name'], d['role'],
             dept_code, d.get('emp_code',''), 1,
             datetime.datetime.now().isoformat()))
        db.commit()
    except sqlite3.IntegrityError:
        return json_error('Username already exists', 409)
    finally: db.close()
    return jsonify({'id':new_id})

@app.route('/api/users/<uid2>', methods=['PUT','DELETE'])
def user_api(uid2):
    err = require_role('master_admin','dept_admin')
    if err: return err
    u = current_user()
    db = get_master_conn()
    target = db.execute("SELECT * FROM users WHERE id=?", (uid2,)).fetchone()
    if not target: db.close(); return json_error('User not found',404)
    # dept_admin can only manage own dept users
    if u['role']=='dept_admin' and dict(target).get('dept_code')!=u['dept_code']:
        db.close(); return json_error('Access denied',403)
    if request.method == 'DELETE':
        db.execute("UPDATE users SET active=0 WHERE id=?", (uid2,))
        db.commit(); db.close(); return jsonify({'ok':True})
    d = request.json or {}
    pw_hash = dict(target)['password_hash']
    if d.get('password'): pw_hash = hash_password(d['password'])
    db.execute(
        "UPDATE users SET full_name=?,role=?,dept_code=?,emp_code=?,active=?,password_hash=? WHERE id=?",
        (d.get('full_name', target['full_name']),
         d.get('role', target['role']),
         d.get('dept_code', target['dept_code']),
         d.get('emp_code', target['emp_code']),
         1 if d.get('active',True) else 0,
         pw_hash, uid2))
    db.commit(); db.close()
    return jsonify({'ok':True})

@app.route('/api/master/summary')
def master_summary():
    err = require_role('master_admin')
    if err: return err
    db_m = get_master_conn()
    depts = R(db_m.execute("SELECT * FROM departments WHERE active=1").fetchall())
    db_m.close()
    summary = []
    for dept in depts:
        path = get_dept_db_path(dept['code'])
        if not os.path.exists(path):
            summary.append({**dept,'employees':0,'mps':0,'cps':0,'compliance':None})
            continue
        d = sqlite3.connect(path); d.row_factory=sqlite3.Row
        emps = d.execute("SELECT COUNT(*) c FROM employees").fetchone()['c']
        mps  = d.execute("SELECT COUNT(*) c FROM mps").fetchone()['c']
        cps  = d.execute("SELECT COUNT(*) c FROM cps").fetchone()['c']
        perf = d.execute(
            "SELECT COUNT(*) tot,SUM(CASE WHEN status='C' THEN 1 ELSE 0 END) comp FROM perf"
        ).fetchone()
        pct = round(perf['comp']/perf['tot']*100,1) if perf['tot'] else None
        d.close()
        summary.append({**dept,'employees':emps,'mps':mps,'cps':cps,'compliance':pct})
    return jsonify(summary)
'''

c = c.replace("if __name__ == '__main__':", auth_routes + "\nif __name__ == '__main__':")
print('✓ Auth routes added (login, logout, users, departments, master summary)')

with open('app.py','w',encoding='utf-8') as f: f.write(c)
print('\nStep 1 complete — app.py patched')
