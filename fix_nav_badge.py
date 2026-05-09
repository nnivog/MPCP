with open('index.html','r',encoding='utf-8') as f: c=f.read()

old_fn = "function renderUserBadge() {"
start = c.find(old_fn)
end = c.find("\nasync function switchDept(", start)

new_fn = """function renderUserBadge() {
  const u = S.authUser; if(!u) return
  const badge = document.getElementById('user-badge'); if (!badge) return
  const isMaster = u.role === 'master_admin'
  const deptLabel = u.dept_name || u.dept_code || ''
  badge.innerHTML =
    '<div style="display:flex;align-items:center;gap:8px;padding:4px 0">'
    + (isMaster
      ? '<select id="dept-switcher" onchange="switchDept(this.value)" style="font-size:11px;padding:3px 8px;height:28px;width:155px;background:#1a2d4a;color:#fff;border:1px solid #2d4a6b;border-radius:6px"><option value="">All Departments</option></select>'
      : '<div style="background:#1a2d4a;border-radius:6px;padding:3px 10px;font-size:11px;color:#60a5fa;font-weight:700">&#127970; '+esc(deptLabel)+'</div>')
    + '<div style="display:flex;align-items:center;gap:6px;background:#1a2d4a;border-radius:20px;padding:3px 10px 3px 5px">'
    + '<div style="width:26px;height:26px;border-radius:50%;background:#1d4ed8;color:#fff;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0">'
    + ((u.full_name||'?').split(' ').map(function(w){return w[0]||''}).join('').slice(0,2).toUpperCase())
    + '</div>'
    + '<div style="line-height:1.3">'
    + '<div style="font-size:11px;font-weight:700;color:#fff">'+esc(u.full_name||u.username)+'</div>'
    + '<div style="font-size:9px;color:#60a5fa;text-transform:uppercase;letter-spacing:.4px">'+esc((u.role||'').replace(/_/g,' '))+'</div>'
    + '</div></div>'
    + '<a href="/logout" title="Logout" style="display:flex;align-items:center;justify-content:center;width:28px;height:28px;background:#1a2d4a;border-radius:8px;color:#f87171;font-size:14px;text-decoration:none;font-weight:700;border:1px solid #2d4a6b;flex-shrink:0" onmouseover="this.style.background=\'#dc2626\';this.style.color=\'#fff\'" onmouseout="this.style.background=\'#1a2d4a\';this.style.color=\'#f87171\'">&#10148;</a>'
    + '</div>'
  if (isMaster) {
    fetch('/api/departments').then(function(r){return r.json()}).then(function(depts){
      const sel = document.getElementById('dept-switcher'); if(!sel) return
      depts.forEach(function(d){
        const o=document.createElement('option')
        o.value=d.code; o.textContent=d.name
        if(d.code===S.activeDept) o.selected=true
        sel.appendChild(o)
      })
    }).catch(function(){})
  }
}
"""

if start != -1 and end != -1:
    c = c[:start] + new_fn + c[end:]
    print('✓ renderUserBadge rewritten with logout button')
else:
    print(f'start={start} end={end}')

with open('index.html','w',encoding='utf-8') as f: f.write(c)
