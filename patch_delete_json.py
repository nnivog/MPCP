"""
Patch: Fix delete routes to return JSON (not HTML) so JS fetch works
Run from repo root: python patch_delete_json.py
"""

content = open('app.py', encoding='utf-8').read()

# ── PATCH 1: Fix admin_delete_user to return JSON ───────────────────────────

old_delete_user = """@app.route('/admin/users/<uid2>/delete', methods=['POST'])
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
        db.close()"""

new_delete_user = """@app.route('/admin/users/<uid2>/delete', methods=['POST'])
def admin_delete_user(uid2):
    err = require_role('master_admin')
    if err: return jsonify({'ok': False, 'error': 'Access denied'}), 403
    u = current_user()
    if u['id'] == uid2:
        return jsonify({'ok': False, 'error': 'Cannot delete your own account'})
    db = get_master_conn()
    try:
        user = db.execute('SELECT username FROM users WHERE id=?', (uid2,)).fetchone()
        if not user:
            return jsonify({'ok': False, 'error': 'User not found'})
        if user['username'] == 'admin':
            return jsonify({'ok': False, 'error': 'Cannot delete master admin account'})
        db.execute('DELETE FROM users WHERE id=?', (uid2,))
        log_audit('USER_DELETE', 'user', uid2, f'Admin deleted user {user["username"]}')
        db.commit()
        return jsonify({'ok': True, 'msg': f'User {user["username"]} deleted'})
    except Exception as ex:
        return jsonify({'ok': False, 'error': str(ex)})
    finally:
        db.close()"""

if old_delete_user in content:
    content = content.replace(old_delete_user, new_delete_user)
    print("✅ Patch 1: admin_delete_user now returns JSON")
else:
    print("❌ Patch 1 failed - route not found, trying alternate search...")
    idx = content.find("def admin_delete_user")
    if idx != -1:
        print(f"   Found at index {idx}, manual review needed")
        print("   Context:", content[idx:idx+200])
    else:
        print("   admin_delete_user function not found at all")

# ── Write file ───────────────────────────────────────────────────────────────
open('app.py', 'w', encoding='utf-8').write(content)
print("\n✅ app.py saved.")

# ── PATCH 2: Fix deleteUser JS to handle redirect/HTML response ─────────────
content2 = open('index.html', encoding='utf-8').read()

old_delete_user_js = """function deleteUser(uid2, uname) {
  if (!confirm('Delete user @' + uname + '?\\nThis cannot be undone.')) return
  fetch('/admin/users/' + uid2 + '/delete', {method:'POST'})
    .then(function(r){return r.json()})
    .then(function(data){
      if(data.ok||data.msg){ toast('User deleted','ok'); renderUsers() }
      else toast('Error: '+(data.error||data.msg||'Unknown'),'err')
    })
    .catch(function(e){ toast('Error: '+e.message,'err') })
}"""

new_delete_user_js = """function deleteUser(uid2, uname) {
  if (!confirm('Delete user @' + uname + '?\\nThis cannot be undone.')) return
  fetch('/admin/users/' + uid2 + '/delete', {
    method: 'POST',
    headers: {'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
  })
    .then(function(r){
      const ct = r.headers.get('content-type')||''
      if(ct.includes('application/json')) return r.json()
      return r.ok ? {ok:true} : {ok:false, error:'Server error '+r.status}
    })
    .then(function(data){
      if(data.ok){ toast('User @'+uname+' deleted','ok'); renderUsers() }
      else toast('Error: '+(data.error||'Unknown'),'err')
    })
    .catch(function(e){ toast('Error: '+e.message,'err') })
}"""

if old_delete_user_js in content2:
    content2 = content2.replace(old_delete_user_js, new_delete_user_js)
    print("✅ Patch 2: deleteUser JS fixed to handle JSON response")
else:
    print("❌ Patch 2 failed - deleteUser JS not found")

# ── PATCH 3: Fix deleteDept JS similarly ────────────────────────────────────

old_delete_dept_js = """function deleteDept(did, dname) {
  if (!confirm('Delete department "' + dname + '"?\\nThis will deactivate it. This cannot be undone.')) return
  fetch('/api/departments/' + did, {method:'DELETE'})
    .then(function(r){return r.json()})
    .then(function(data){
      if(data.ok){ toast('Department deleted','ok'); renderDepartments() }
      else toast('Error: '+(data.error||'Unknown'),'err')
    })
    .catch(function(e){ toast('Error: '+e.message,'err') })
}"""

new_delete_dept_js = """function deleteDept(did, dname) {
  if (!confirm('Delete department "' + dname + '"?\\nThis will deactivate it. This cannot be undone.')) return
  fetch('/api/departments/' + did, {
    method: 'DELETE',
    headers: {'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
  })
    .then(function(r){
      const ct = r.headers.get('content-type')||''
      if(ct.includes('application/json')) return r.json()
      return r.ok ? {ok:true} : {ok:false, error:'Server error '+r.status}
    })
    .then(function(data){
      if(data.ok){ toast('Department "'+dname+'" deleted','ok'); renderDepartments() }
      else toast('Error: '+(data.error||'Unknown'),'err')
    })
    .catch(function(e){ toast('Error: '+e.message,'err') })
}"""

if old_delete_dept_js in content2:
    content2 = content2.replace(old_delete_dept_js, new_delete_dept_js)
    print("✅ Patch 3: deleteDept JS fixed")
else:
    print("❌ Patch 3 failed - deleteDept JS not found")

open('index.html', 'w', encoding='utf-8').write(content2)
print("\n✅ index.html saved. Now run:")
print("   git add app.py index.html")
print("   git commit -m 'fix: delete routes return JSON, fix fetch handlers'")
print("   git push origin main")
