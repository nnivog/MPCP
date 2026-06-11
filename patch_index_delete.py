"""
Patch: Add Delete button to Department cards + Delete User in index.html
Run from repo root: python patch_index_delete.py
"""

content = open('index.html', encoding='utf-8').read()

# ── PATCH 1: Add Delete button to department card ────────────────────────────

old_dept_btns = """html+='<button class="btn btn-ghost btn-sm" style="font-size:10px" onclick="openDeptForm('+JSON.stringify(d.id)+','+JSON.stringify(d.name)+','+JSON.stringify(d.active)+')">&#9998; Edit</button>'
      html+='</div>'
      html+='</div>'
    })"""

new_dept_btns = """html+='<button class="btn btn-ghost btn-sm" style="font-size:10px" onclick="openDeptForm('+JSON.stringify(d.id)+','+JSON.stringify(d.name)+','+JSON.stringify(d.active)+')">&#9998; Edit</button>'
      html+='<button class="btn btn-ghost btn-sm" style="font-size:10px;color:#dc2626;border-color:#fca5a5" onclick="deleteDept('+JSON.stringify(d.id)+','+JSON.stringify(d.name)+')">&#128465; Delete</button>'
      html+='</div>'
      html+='</div>'
    })"""

if old_dept_btns in content:
    content = content.replace(old_dept_btns, new_dept_btns)
    print("✅ Patch 1: Delete button added to department cards")
else:
    print("❌ Patch 1 failed - department card buttons not found")

# ── PATCH 2: Add deleteDept JS function ─────────────────────────────────────

old_open_dept = "function openDeptForm(did, dname, dactive) {"

new_open_dept = """function deleteDept(did, dname) {
  if (!confirm('Delete department "' + dname + '"?\\nThis will deactivate it. This cannot be undone.')) return
  fetch('/api/departments/' + did, {method:'DELETE'})
    .then(function(r){return r.json()})
    .then(function(data){
      if(data.ok){ toast('Department deleted','ok'); renderDepartments() }
      else toast('Error: '+(data.error||'Unknown'),'err')
    })
    .catch(function(e){ toast('Error: '+e.message,'err') })
}

function openDeptForm(did, dname, dactive) {"""

if "function openDeptForm(did, dname, dactive) {" in content:
    content = content.replace(old_open_dept, new_open_dept)
    print("✅ Patch 2: deleteDept() function added")
else:
    print("❌ Patch 2 failed - openDeptForm not found")

# ── PATCH 3: Add Delete button to Users table in renderUsers ─────────────────

old_user_btns = """html+='<button class="btn btn-ghost btn-sm" onclick="openUserForm('+JSON.stringify(u.id)+')" style="font-size:10px;margin-right:4px">Edit</button>'
      html+='<button class="btn btn-ghost btn-sm" style="color:var(--red);font-size:10px" onclick="resetUserPw('+JSON.stringify(u.id)+','+JSON.stringify(u.username)+')">Reset PW</button>'
      html+='</td></tr>'"""

new_user_btns = """html+='<button class="btn btn-ghost btn-sm" onclick="openUserForm('+JSON.stringify(u.id)+')" style="font-size:10px;margin-right:4px">Edit</button>'
      html+='<button class="btn btn-ghost btn-sm" style="color:var(--red);font-size:10px;margin-right:4px" onclick="resetUserPw('+JSON.stringify(u.id)+','+JSON.stringify(u.username)+')">Reset PW</button>'
      +(u.username!=='admin'?'<button class="btn btn-ghost btn-sm" style="color:#dc2626;font-size:10px;border-color:#fca5a5" onclick="deleteUser('+JSON.stringify(u.id)+','+JSON.stringify(u.username)+')">&#128465; Delete</button>':'')
      html+='</td></tr>'"""

if old_user_btns in content:
    content = content.replace(old_user_btns, new_user_btns)
    print("✅ Patch 3: Delete button added to users table")
else:
    print("❌ Patch 3 failed - user buttons not found")

# ── PATCH 4: Add deleteUser JS function ─────────────────────────────────────

old_open_user = "function openUserForm(uid2) {"

new_open_user = """function deleteUser(uid2, uname) {
  if (!confirm('Delete user @' + uname + '?\\nThis cannot be undone.')) return
  fetch('/admin/users/' + uid2 + '/delete', {method:'POST'})
    .then(function(r){return r.json()})
    .then(function(data){
      if(data.ok||data.msg){ toast('User deleted','ok'); renderUsers() }
      else toast('Error: '+(data.error||data.msg||'Unknown'),'err')
    })
    .catch(function(e){ toast('Error: '+e.message,'err') })
}

function openUserForm(uid2) {"""

if "function openUserForm(uid2) {" in content:
    content = content.replace(old_open_user, new_open_user)
    print("✅ Patch 4: deleteUser() function added")
else:
    print("❌ Patch 4 failed - openUserForm not found")

# ── Write file ───────────────────────────────────────────────────────────────
open('index.html', 'w', encoding='utf-8').write(content)
print("\n✅ index.html saved. Now run:")
print("   git add index.html app.py")
print("   git commit -m 'feat: add delete buttons for departments and users'")
print("   git push origin main")
