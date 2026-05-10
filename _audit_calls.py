
with open('app.py','r',encoding='utf-8') as f: c=f.read()

changes = [
    # Login success
    (
        "session['mpcp_user'] = dict(u)",
        "session['mpcp_user'] = dict(u)\n        log_audit('LOGIN', 'user', u['id'], f'Login: {u[\"username\"]}')"
    ),
    # Admin create user
    (
        'db.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?,?,?)",\n            (uid2,uname,hash_password(pw),full,role2,dept2,emp2,1,now))',
        'db.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?,?,?)",\n            (uid2,uname,hash_password(pw),full,role2,dept2,emp2,1,now))\n        log_audit(\'USER_CREATE\', \'user\', uid2, f\'Created user {uname} role={role2} dept={dept2}\')'
    ),
    # Disable/enable user
    (
        'db.execute("UPDATE users SET active=? WHERE id=?", (new_active, uid2))',
        'db.execute("UPDATE users SET active=? WHERE id=?", (new_active, uid2))\n    log_audit(\'USER_\'+(\' ENABLE\' if new_active else \'DISABLE\').strip(), \'user\', uid2, f\'active={new_active}\')'
    ),
    # Password reset by admin
    (
        'db.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(pw), uid2))',
        'db.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(pw), uid2))\n    log_audit(\'PASSWORD_RESET\', \'user\', uid2, \'Admin password reset\')'
    ),
    # Edit user
    (
        '"UPDATE users SET full_name=?,role=?,dept_code=?,emp_code=?,active=?,password_hash=? WHERE id=?"',
        '"UPDATE users SET full_name=?,role=?,dept_code=?,emp_code=?,active=?,password_hash=? WHERE id=?"'
    ),
]

count = 0
for old, new in changes:
    if old in c and old != new:
        c = c.replace(old, new, 1)
        print(f'Patched: {old[:60]}')
        count += 1
    elif old == new:
        pass
    else:
        print(f'NOT MATCHED: {old[:60]}')

# Also log edit user - find the UPDATE users SET full_name line
import re
edit_old = '            (full_name2, role2, dept2, emp2, active2, pw_hash2, uid2)\n        )'
edit_new = '            (full_name2, role2, dept2, emp2, active2, pw_hash2, uid2)\n        )\n        log_audit(\'USER_EDIT\', \'user\', uid2, f\'Edited: {full_name2} role={role2}\')'
if edit_old in c:
    c = c.replace(edit_old, edit_new, 1)
    print('Patched: USER_EDIT call')
    count += 1

with open('app.py','w',encoding='utf-8') as f: f.write(c)
print(f'Total: {count} audit calls added')
