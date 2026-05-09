with open('index.html','r',encoding='utf-8') as f: c=f.read()
n=0

old_s = "locations:[], currentTab:'dashboard', teamView:'cards', masterSub:'mps',"
new_s = "locations:[], currentTab:'dashboard', teamView:'cards', masterSub:'mps', authUser:null, activeDept:null,"
if old_s in c: c=c.replace(old_s,new_s); n+=1; print('1 S.authUser added')
else: print('1 SKIP')

old_load = "async function loadAll() {"
new_load = """async function loadAll() {
  try {
    const me = await fetch('/api/auth/me').then(r=>r.ok?r.json():null)
    if (!me || me.error) { window.location='/login'; return }
    S.authUser = me; S.activeDept = me.active_dept || me.dept_code || null
    renderUserBadge()
  } catch(e) { window.location='/login'; return }"""
if old_load in c and 'auth/me' not in c:
    c=c.replace(old_load,new_load); n+=1; print('2 auth/me added')
else: print('2 SKIP')

badge_fn = """
function renderUserBadge() {
  const u = S.authUser; if(!u) return
  const badge = document.getElementById('user-badge'); if (!badge) return
  const isMaster = u.role === 'master_admin'
  badge.innerHTML = '<div style="display:flex;align-items:center;gap:10px">'
    + (isMaster
      ? '<select id="dept-switcher" class="form-select" style="font-size:11px;padding:4px 8px;height:28px;width:160px;background:#1a2d4a;color:#fff;border-color:#2d4a6b" onchange="switchDept(this.value)"><option value="">All Departments</option></select>'
      : '<span style="font-size:11px;color:#60a5fa;font-weight:700">'+esc(u.dept_name||u.dept_code||'')+'</span>')
    + '<div style="display:flex;align-items:center;gap:6px;background:#1a2d4a;border-radius:20px;padding:4px 12px 4px 6px">'
    + '<div style="width:24px;height:24px;border-radius:50%;background:#1d4ed8;color:#fff;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700">'
    + ((u.full_name||'?').split(' ').map(function(w){return w[0]}).join('').slice(0,2).toUpperCase())
    + '</div><div>'
    + '<div style="font-size:11px;font-weight:700;color:#fff;line-height:1.2">'+esc(u.full_name||u.username)+'</div>'
    + '<div style="font-size:9px;color:#60a5fa;text-transform:uppercase;letter-spacing:.5px">'+esc(u.role.replace(/_/g,' '))+'</div>'
    + '</div><a href="/logout" style="margin-left:6px;color:#94a3b8;font-size:14px;text-decoration:none;font-weight:700" title="Logout">&#10005;</a>'
    + '</div></div>'
  if (isMaster) {
    fetch('/api/departments').then(function(r){return r.json()}).then(function(depts){
      const sel = document.getElementById('dept-switcher'); if(!sel) return
      depts.forEach(function(d){
        const o=document.createElement('option')
        o.value=d.code; o.textContent=d.name
        if(d.code===S.activeDept) o.selected=true
        sel.appendChild(o)
      })
    })
  }
}

async function switchDept(deptCode) {
  const r = await fetch('/api/auth/switch_dept',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({dept_code:deptCode})})
  if(r.ok){ S.activeDept=deptCode||null; await loadAll(); toast(deptCode?'Switched to '+deptCode:'All departments','ok') }
}
"""
if 'function renderUserBadge()' not in c:
    c=c.replace('function filterMPs()', badge_fn+'\nfunction filterMPs()')
    n+=1; print('3 renderUserBadge added')
else: print('3 SKIP')

old_nav = '<div class="nav-tabs" id="main-tabs">'
if old_nav in c and 'user-badge' not in c:
    c=c.replace(old_nav,
        '<div style="display:flex;align-items:center;justify-content:space-between;padding:0 16px">\n  <div class="nav-tabs" id="main-tabs">')
    idx = c.find('id="main-tabs"')
    end = c.find('</div>', idx)
    c = c[:end+6] + '\n  <div id="user-badge" style="flex-shrink:0;padding:4px 0"></div>\n</div>' + c[end+6:]
    n+=1; print('4 user-badge added to nav')
else: print('4 SKIP')

old_mt = '<button class="sub-tab" onclick="switchMaster(\'dashboard_builder\')">&#128196; Dashboard Builder</button>'
new_mt = '<button class="sub-tab" onclick="switchMaster(\'users\')">&#128100; Users</button>\n      '+old_mt
if old_mt in c and "switchMaster('users')" not in c:
    c=c.replace(old_mt,new_mt); n+=1; print('5 Users sub-tab added')
else: print('5 SKIP')

old_mh = "else if(S.masterSub==='levels') renderLevels()"
new_mh = "else if(S.masterSub==='levels') renderLevels()\n  else if(S.masterSub==='users') renderUsers()"
if old_mh in c and 'renderUsers()' not in c:
    c=c.replace(old_mh,new_mh); n+=1; print('6 renderUsers wired')
else: print('6 SKIP')

users_fn = """
function renderUsers() {
  const isMaster = S.authUser&&S.authUser.role==='master_admin'
  const isDeptAdmin = S.authUser&&S.authUser.role==='dept_admin'
  if(!isMaster&&!isDeptAdmin){q('#master-content').innerHTML='<div class="info-box"><p>Access denied.</p></div>';return}
  fetch('/api/users').then(function(r){return r.json()}).then(function(users){
    let html='<div class="card"><div class="card-head"><p>User Management</p>'
    html+='<button class="btn btn-primary btn-sm" onclick="openUserForm()">+ New User</button></div>'
    html+='<div class="card-body"><table style="width:100%;border-collapse:collapse;font-size:12px">'
    html+='<thead><tr style="background:#f8fafc">'
    ;['User','Department','Role','Emp Code','Actions'].forEach(function(h){
      html+='<th style="padding:8px 10px;text-align:'+(h==='Actions'?'center':'left')+';font-size:10px;font-weight:700;color:#6b7a99;text-transform:uppercase;border-bottom:2px solid var(--border)">'+h+'</th>'
    })
    html+='</tr></thead><tbody>'
    users.forEach(function(u){
      const rc=u.role==='master_admin'?'#7c3aed':u.role==='dept_admin'?'#1d4ed8':'#047857'
      html+='<tr style="border-bottom:1px solid var(--border)">'
      html+='<td style="padding:8px 10px"><div style="font-weight:700;font-size:12px">'+esc(u.full_name)+'</div>'
      html+='<div style="font-size:10px;color:#6b7a99">@'+esc(u.username)+'</div></td>'
      html+='<td style="padding:8px 10px;font-size:11px">'+esc(u.dept_name||u.dept_code||'All')+'</td>'
      html+='<td style="padding:8px 10px"><span style="background:'+rc+'20;color:'+rc+';padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700">'+esc(u.role.replace(/_/g,' ').toUpperCase())+'</span></td>'
      html+='<td style="padding:8px 10px;font-size:11px;font-family:monospace">'+esc(u.emp_code||'\\u2014')+'</td>'
      html+='<td style="padding:8px 10px;text-align:center">'
      html+='<button class="btn btn-ghost btn-sm" onclick="openUserForm('+JSON.stringify(u.id)+')" style="font-size:10px;margin-right:4px">Edit</button>'
      html+='<button class="btn btn-ghost btn-sm" style="color:var(--red);font-size:10px" onclick="resetUserPw('+JSON.stringify(u.id)+','+JSON.stringify(u.username)+')">Reset PW</button>'
      html+='</td></tr>'
    })
    html+='</tbody></table></div></div>'
    q('#master-content').innerHTML=html
  })
}

function openUserForm(uid2) {
  fetch('/api/departments').then(function(r){return r.ok?r.json():[]}).then(function(depts){
    const deptOpts=depts.map(function(d){return'<option value="'+d.code+'">'+esc(d.name)+'</option>'}).join('')
    const isMasterAdmin=S.authUser&&S.authUser.role==='master_admin'
    const isEdit=!!uid2
    const body='<div class="form-grid-2">'
      +'<div class="form-group"><label class="form-label">Full Name *</label><input class="form-input" id="uf-name" placeholder="Full name"></div>'
      +'<div class="form-group"><label class="form-label">Username *</label><input class="form-input" id="uf-user" placeholder="username"'+(isEdit?' disabled':'')+'></div>'
      +'</div><div class="form-grid-2">'
      +'<div class="form-group"><label class="form-label">'+(isEdit?'New Password (blank=keep)':'Password *')+'</label>'
      +'<input class="form-input" type="password" id="uf-pw" placeholder="'+(isEdit?'Leave blank to keep':'Min 6 chars')+'"></div>'
      +'<div class="form-group"><label class="form-label">Role *</label>'
      +'<select class="form-select" id="uf-role">'
      +'<option value="user">User</option>'
      +'<option value="dept_admin">Dept Admin</option>'
      +(isMasterAdmin?'<option value="master_admin">Master Admin</option>':'')
      +'</select></div>'
      +'</div><div class="form-grid-2">'
      +'<div class="form-group"><label class="form-label">Department</label>'
      +'<select class="form-select" id="uf-dept"><option value="">-- None (Master) --</option>'+deptOpts+'</select></div>'
      +'<div class="form-group"><label class="form-label">Employee Code</label>'
      +'<input class="form-input" id="uf-emp" placeholder="e.g. EMP000513"></div>'
      +'</div>'
    const saveBtn={label:isEdit?'Save Changes':'Create User',cls:'btn-primary',fn:async function(){
      const pw=q('#uf-pw')?.value||''
      if(!isEdit&&(!q('#uf-name')?.value||!q('#uf-user')?.value||!pw)){toast('Fill required fields','err');return}
      if(pw&&pw.length<6){toast('Password min 6 chars','err');return}
      const payload={full_name:q('#uf-name').value,role:q('#uf-role').value,
        dept_code:q('#uf-dept').value||null,emp_code:q('#uf-emp')?.value||''}
      if(!isEdit) payload.username=q('#uf-user').value
      if(pw) payload.password=pw
      const r=isEdit?await api.put('/api/users/'+uid2,payload):await api.post('/api/users',payload)
      if(r?.ok||r?.id){toast(isEdit?'User updated':'User created','ok');closeModal();renderUsers()}
      else toast('Error: '+(r?.error||'Unknown'),'err')
    }}
    openModal(isEdit?'Edit User':'New User',body,[saveBtn,{label:'Cancel',cls:'btn-ghost',fn:()=>closeModal()}],true)
    if(isEdit){
      fetch('/api/users').then(function(r){return r.json()}).then(function(users){
        const u=users.find(function(x){return x.id===uid2}); if(!u)return
        setTimeout(function(){
          if(q('#uf-name'))q('#uf-name').value=u.full_name||''
          if(q('#uf-user'))q('#uf-user').value=u.username||''
          if(q('#uf-role'))q('#uf-role').value=u.role||'user'
          if(q('#uf-dept'))q('#uf-dept').value=u.dept_code||''
          if(q('#uf-emp'))q('#uf-emp').value=u.emp_code||''
        },60)
      })
    }
  })
}

async function resetUserPw(uid2,username){
  const pw=prompt('New password for @'+username+' (min 6 chars):')
  if(!pw)return
  if(pw.length<6){toast('Min 6 characters','err');return}
  const r=await api.put('/api/users/'+uid2,{password:pw})
  if(r?.ok)toast('Password reset for @'+username,'ok')
  else toast('Error resetting password','err')
}
"""
if 'function renderUsers()' not in c:
    c=c.replace('function renderLevels()', users_fn+'\nfunction renderLevels()')
    n+=1; print('7 renderUsers + openUserForm added')
else: print('7 SKIP')

with open('index.html','w',encoding='utf-8') as f: f.write(c)
print(f'\nDone — {n} changes applied')
