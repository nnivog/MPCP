"""
Patch: Add Delete User + Delete Department to MPCP Admin Panel
Run from repo root: python patch_delete.py
"""
import re

f = open('app.py', encoding='utf-8')
content = f.read()
f.close()

# ── PATCH 1: Add Delete button in users table (after the toggle form) ────────

old_buttons = """              <form method="POST" action="/admin/users/{{ u.id }}/toggle">
                <button class="btn {{ 'btn-danger' if u.active else 'btn-success' }}" type="submit">{{ 'Disable' if u.active else 'Enable' }}</button>
              </form>
            </div>"""

new_buttons = """              <form method="POST" action="/admin/users/{{ u.id }}/toggle">
                <button class="btn {{ 'btn-danger' if u.active else 'btn-success' }}" type="submit">{{ 'Disable' if u.active else 'Enable' }}</button>
              </form>
              {% if current_user_role == 'master_admin' and u.username != 'admin' %}
              <form method="POST" action="/admin/users/{{ u.id }}/delete" onsubmit="return confirm('Delete user {{ u.username }}? This cannot be undone.')">
                <button class="btn btn-danger" type="submit" style="background:#dc2626;color:#fff;font-size:10px">&#128465; Delete</button>
              </form>
              {% endif %}
            </div>"""

if old_buttons in content:
    content = content.replace(old_buttons, new_buttons)
    print("✅ Patch 1: Delete button added to users table")
else:
    print("❌ Patch 1 failed - toggle form not found")

# ── PATCH 2: Add delete user route (after edit route) ───────────────────────

old_route = "@app.route('/admin/users/<uid2>/reset', methods=['POST'])"

new_route = """@app.route('/admin/users/<uid2>/delete', methods=['POST'])
def admin_delete_user(uid2):
    err = require_role('master_admin')
    if err: return err
    u = current_user()
    if u['id'] == uid2:
        return _admin_msg('Cannot delete your own account', 'err')
    db = get_master_conn()
    try:
        user = db.execute('SELECT username FROM users WHERE id=?', (uid2,)).fetchone()
        if not user:
            return _admin_msg('User not found', 'err')
        if user['username'] == 'admin':
            return _admin_msg('Cannot delete the master admin account', 'err')
        db.execute('DELETE FROM users WHERE id=?', (uid2,))
        log_audit('USER_DELETE', 'user', uid2, f'Admin deleted user {user["username"]}')
        db.commit()
        return _admin_msg(f'User {user["username"]} deleted successfully', 'ok')
    except Exception as ex:
        return _admin_msg(str(ex), 'err')
    finally:
        db.close()

@app.route('/admin/users/<uid2>/reset', methods=['POST'])"""

if "@app.route('/admin/users/<uid2>/reset', methods=['POST'])" in content:
    content = content.replace(old_route, new_route)
    print("✅ Patch 2: Delete user route added")
else:
    print("❌ Patch 2 failed - reset route not found")

# ── PATCH 3: Add department table with delete button ────────────────────────
# Find where departments are rendered in ADMIN_HTML

old_dept = "{% for d in departments %}"

# Check if departments section exists
if old_dept in content:
    # Find the dept table row and add delete button
    old_dept_row = """{% for d in departments %}"""
    print("ℹ️  Department table found - checking structure...")
else:
    print("ℹ️  Checking dept table structure...")

# Find dept table rows
dept_idx = content.find("dept_code")
# Look for department table structure near ADMIN_HTML
admin_start = content.find('ADMIN_HTML = """')

# Find dept row in HTML
dept_for_match = re.search(r'\{%\s*for d in departments\s*%\}.*?\{%\s*endfor\s*%\}', 
                            content[admin_start:], re.DOTALL)
if dept_for_match:
    print("✅ Department loop found in ADMIN_HTML")
    dept_loop = dept_for_match.group(0)
    print("First 300 chars:", dept_loop[:300])
else:
    print("❌ Department loop not found - need to check manually")
    # Find any dept references in ADMIN_HTML
    admin_section = content[admin_start:admin_start+50000]
    dept_lines = [(i, line) for i, line in enumerate(admin_section.split('\n')) 
                  if 'dept' in line.lower() and ('for' in line or 'code' in line or 'name' in line)]
    for i, line in dept_lines[:10]:
        print(f"  Line ~{i}: {line[:100]}")

# ── Write patched file ───────────────────────────────────────────────────────
open('app.py', 'w', encoding='utf-8').write(content)
print("\n✅ app.py saved. Check output above for any failed patches.")
print("Run: grep -n 'admin/users.*delete' app.py  to verify")
