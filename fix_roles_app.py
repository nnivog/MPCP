with open('app.py','r',encoding='utf-8') as f: c=f.read()
n=0

# Add moderator to valid roles
old_roles = "if d['role'] not in ('master_admin','dept_admin','user'):"
new_roles = "if d['role'] not in ('master_admin','dept_admin','moderator','user'):"
if old_roles in c: c=c.replace(old_roles,new_roles); n+=1; print('1 moderator role added to validation')

# Add /admin route - separate admin panel
admin_route = '''
# ── ADMIN PANEL ────────────────────────────────────────────────────────────
ADMIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MPCP Admin Panel</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,sans-serif;background:#f8fafc;color:#0f1a2e;font-size:13px}
.topbar{background:#0a1628;color:#fff;padding:12px 24px;display:flex;justify-content:space-between;align-items:center}
.topbar h1{font-size:15px;font-weight:800}
.topbar a{color:#60a5fa;font-size:12px;text-decoration:none}
.container{max-width:1100px;margin:24px auto;padding:0 16px}
.card{background:#fff;border-radius:12px;border:1px solid #e5e7eb;margin-bottom:20px;overflow:hidden}
.card-head{padding:14px 20px;border-bottom:1px solid #e5e7eb;display:flex;justify-content:space-between;align-items:center;background:#f8fafc}
.card-head h2{font-size:13px;font-weight:700;color:#0a1628}
table{width:100%;border-collapse:collapse}
thead th{padding:9px 14px;text-align:left;font-size:10px;font-weight:700;color:#6b7a99;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid #e5e7eb;background:#f8fafc}
tbody td{padding:9px 14px;border-bottom:1px solid #f1f5f9;font-size:12px}
tbody tr:hover{background:#f8fafc}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700}
.b-master{background:#ede9fe;color:#7c3aed}
.b-dept{background:#dbeafe;color:#1d4ed8}
.b-mod{background:#fef3c7;color:#92400e}
.b-user{background:#dcfce7;color:#166534}
.b-inactive{background:#fee2e2;color:#dc2626}
.btn{padding:6px 14px;border:none;border-radius:6px;font-size:11px;font-weight:700;cursor:pointer}
.btn-primary{background:#0a1628;color:#fff}
.btn-danger{background:#fee2e2;color:#dc2626;border:1px solid #fecaca}
.btn-warn{background:#fef3c7;color:#92400e;border:1px solid #fde68a}
.form-row{display:flex;gap:10px;flex-wrap:wrap;padding:16px 20px;border-bottom:1px solid #e5e7eb;background:#f0f9ff}
.form-row label{font-size:10px;font-weight:700;color:#374151;display:block;margin-bottom:4px;text-transform:uppercase}
.form-row input,.form-row select{padding:7px 10px;border:1.5px solid #e5e7eb;border-radius:6px;font-size:12px;min-width:150px}
.form-row input:focus,.form-row select:focus{border-color:#1d4ed8;outline:none}
.err{background:#fef2f2;color:#dc2626;padding:8px 14px;border-radius:6px;font-size:12px;margin:10px 20px}
.ok{background:#f0fdf4;color:#16a34a;padding:8px 14px;border-radius:6px;font-size:12px;margin:10px 20px}
</style></head><body>
<div class="topbar">
  <h1>&#128272; MPCP Admin Panel — User Management</h1>
  <div style="display:flex;gap:16px;align-items:center">
    <a href="/">&#8592; Back to App</a>
    <a href="/logout">Sign Out</a>
  </div>
</div>
<div class="container">
  {% if msg %}<div class="{{ 'ok' if msg_type=='ok' else 'err' }}">{{ msg }}</div>{% endif %}

  <!-- Create User -->
  <div class="card">
    <div class="card-head"><h2>&#43; Create New User</h2></div>
    <form method="POST" action="/admin/users/create">
      <div class="form-row">
        <div><label>Full Name *</label><input name="full_name" placeholder="Full name" required></div>
        <div><label>Username *</label><input name="username" placeholder="username" required></div>
        <div><label>Password *</label><input name="password" type="password" placeholder="Min 6 chars" required></div>
        <div><label>Role *</label>
          <select name="role">
            <option value="user">User</option>
            <option value="moderator">Moderator</option>
            <option value="dept_admin">Dept Admin</option>
            {% if current_user_role == 'master_admin' %}<option value="master_admin">Master Admin</option>{% endif %}
          </select></div>
        <div><label>Department</label>
          <select name="dept_code">
            <option value="">— None —</option>
            {% for d in departments %}<option value="{{ d.code }}">{{ d.name }}</option>{% endfor %}
          </select></div>
        <div><label>Emp Code</label><input name="emp_code" placeholder="EMP000XXX"></div>
        <div style="display:flex;align-items:flex-end"><button class="btn btn-primary" type="submit">Create User</button></div>
      </div>
    </form>
  </div>

  <!-- Users Table -->
  <div class="card">
    <div class="card-head"><h2>&#128100; All Users ({{ users|length }})</h2>
      <input placeholder="Search..." oninput="filterTable(this.value)" style="padding:5px 10px;border:1px solid #e5e7eb;border-radius:6px;font-size:12px;width:200px">
    </div>
    <table id="users-table">
      <thead><tr><th>Name / Username</th><th>Department</th><th>Role</th><th>Emp Code</th><th>Status</th><th>Actions</th></tr></thead>
      <tbody>
        {% for u in users %}
        <tr>
          <td><div style="font-weight:700">{{ u.full_name }}</div><div style="color:#6b7a99;font-size:11px">@{{ u.username }}</div></td>
          <td>{{ u.dept_name or u.dept_code or '—' }}</td>
          <td><span class="badge b-{{ u.role.replace('_admin','').replace('master','master') }}">{{ u.role.replace('_',' ').upper() }}</span></td>
          <td style="font-family:monospace">{{ u.emp_code or '—' }}</td>
          <td><span style="color:{{ '#16a34a' if u.active else '#dc2626' }};font-weight:700">{{ 'Active' if u.active else 'Inactive' }}</span></td>
          <td style="display:flex;gap:6px;flex-wrap:wrap;padding:8px 14px">
            <form method="POST" action="/admin/users/{{ u.id }}/reset" style="display:inline">
              <input name="new_password" placeholder="New password" style="padding:4px 8px;border:1px solid #e5e7eb;border-radius:4px;font-size:11px;width:120px">
              <button class="btn btn-warn" type="submit">Reset PW</button>
            </form>
            <form method="POST" action="/admin/users/{{ u.id }}/toggle" style="display:inline">
              <button class="btn {{ 'btn-danger' if u.active else 'btn-primary' }}" type="submit">{{ 'Disable' if u.active else 'Enable' }}</button>
            </form>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
<script>
function filterTable(q){
  const rows=document.querySelectorAll('#users-table tbody tr')
  rows.forEach(function(r){r.style.display=r.textContent.toLowerCase().includes(q.toLowerCase())?'':'none'})
}
</script>
</body></html>"""

def admin_users_data(db, current_role, current_dept):
    if current_role == 'master_admin':
        users = R(db.execute(
            "SELECT u.*,d.name dept_name FROM users u LEFT JOIN departments d ON d.code=u.dept_code ORDER BY u.dept_code,u.full_name"
        ).fetchall())
    else:
        users = R(db.execute(
            "SELECT u.*,d.name dept_name FROM users u LEFT JOIN departments d ON d.code=u.dept_code WHERE u.dept_code=? ORDER BY u.full_name",
            (current_dept,)
        ).fetchall())
    depts = R(db.execute("SELECT code,name FROM departments WHERE active=1 ORDER BY name").fetchall())
    return users, depts

@app.route('/admin')
@app.route('/admin/users')
def admin_panel():
    err = require_role('master_admin','dept_admin')
    if err: return err
    u = current_user()
    db = get_master_conn()
    users, depts = admin_users_data(db, u['role'], u.get('dept_code'))
    db.close()
    return render_template_string(ADMIN_HTML, users=users, depts=depts,
        current_user_role=u['role'], msg=None, msg_type=None)

@app.route('/admin/users/create', methods=['POST'])
def admin_create_user():
    err = require_role('master_admin','dept_admin')
    if err: return err
    u = current_user()
    d = request.form
    pw = d.get('password','')
    if not d.get('full_name') or not d.get('username') or not pw:
        return _admin_msg('Full name, username and password required', 'err')
    if len(pw) < 6:
        return _admin_msg('Password must be at least 6 characters', 'err')
    role = d.get('role','user')
    if u['role'] == 'dept_admin':
        role = role if role in ('user','moderator') else 'user'
    dept_code = d.get('dept_code') or u.get('dept_code')
    if u['role'] == 'dept_admin': dept_code = u['dept_code']
    db = get_master_conn()
    try:
        new_id = uid()
        db.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?,?,?)",
            (new_id, d['username'].strip().lower(), hash_password(pw),
             d['full_name'], role, dept_code, d.get('emp_code',''), 1,
             datetime.datetime.now().isoformat()))
        db.commit()
        return _admin_msg(f"User @{d['username']} created successfully", 'ok')
    except sqlite3.IntegrityError:
        return _admin_msg(f"Username @{d['username']} already exists", 'err')
    finally: db.close()

@app.route('/admin/users/<uid2>/reset', methods=['POST'])
def admin_reset_pw(uid2):
    err = require_role('master_admin','dept_admin')
    if err: return err
    pw = request.form.get('new_password','')
    if len(pw) < 6:
        return _admin_msg('Password must be at least 6 characters', 'err')
    db = get_master_conn()
    db.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(pw), uid2))
    db.commit(); db.close()
    return _admin_msg('Password reset successfully', 'ok')

@app.route('/admin/users/<uid2>/toggle', methods=['POST'])
def admin_toggle_user(uid2):
    err = require_role('master_admin','dept_admin')
    if err: return err
    u = current_user()
    db = get_master_conn()
    target = db.execute("SELECT * FROM users WHERE id=?", (uid2,)).fetchone()
    if not target: db.close(); return _admin_msg('User not found', 'err')
    if u['role']=='dept_admin' and dict(target).get('dept_code')!=u['dept_code']:
        db.close(); return _admin_msg('Access denied', 'err')
    new_active = 0 if dict(target)['active'] else 1
    db.execute("UPDATE users SET active=? WHERE id=?", (new_active, uid2))
    db.commit(); db.close()
    status = 'enabled' if new_active else 'disabled'
    return _admin_msg(f"User {status} successfully", 'ok')

def _admin_msg(msg, msg_type):
    u = current_user()
    db = get_master_conn()
    users, depts = admin_users_data(db, u['role'], u.get('dept_code'))
    db.close()
    return render_template_string(ADMIN_HTML, users=users, depts=depts,
        current_user_role=u['role'], msg=msg, msg_type=msg_type)
'''

if '/admin/users' not in c:
    c = c.replace("if __name__ == '__main__':", admin_route + "\nif __name__ == '__main__':")
    n+=1; print('2 Admin panel routes added')
else: print('2 SKIP - admin routes exist')

with open('app.py','w',encoding='utf-8') as f: f.write(c)
print(f'\nDone — {n} changes applied')
