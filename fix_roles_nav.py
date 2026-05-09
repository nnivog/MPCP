with open('index.html','r',encoding='utf-8') as f: c=f.read()
n=0

# ── 1. Fix nav tabs - add role classes to buttons ─────────────────────────
old_nav = """    <button class="nav-tab active" onclick="switchTab('dashboard')">📊 Dashboard</button>
    <button class="nav-tab" onclick="switchTab('team')">👥 Team</button>
    <button class="nav-tab" onclick="switchTab('master')">🔧 Master Setup</button>
    <button class="nav-tab" onclick="switchTab('data')">📁 Data Manager</button>
    <button class="nav-tab" onclick="switchTab('reports')">📈 Reports</button>"""

new_nav = """    <button class="nav-tab active" onclick="switchTab('dashboard')">📊 Dashboard</button>
    <button class="nav-tab" onclick="switchTab('team')">👥 Team</button>
    <button class="nav-tab tab-admin-only" onclick="switchTab('master')">🔧 Master Setup</button>
    <button class="nav-tab tab-mod-only" onclick="switchTab('master')">🔧 Master Setup</button>
    <button class="nav-tab" onclick="switchTab('data')">📁 Data Manager</button>
    <button class="nav-tab" onclick="switchTab('reports')">📈 Reports</button>"""

if old_nav in c:
    c=c.replace(old_nav,new_nav); n+=1; print('1 nav tab roles added')
else: print('1 SKIP - nav not matched')

# Fix Org & Cascade tab
old_org = '<button class="nav-tab" onclick="switchTab(\'org\')">&#127970; Org &amp; Cascade</button>'
new_org = '<button class="nav-tab tab-admin-only" onclick="switchTab(\'org\')">&#127970; Org &amp; Cascade</button>'
if old_org in c: c=c.replace(old_org,new_org); n+=1; print('2 org tab admin-only')
else: print('2 SKIP')

# ── 2. Fix user-badge div - add it if missing from nav ───────────────────
# Check if user-badge exists in nav structure
if 'id="user-badge"' not in c:
    old_tabs_end = '</div>\n  <div id="tab-dashboard"'
    new_tabs_end = '</div>\n  <div id="user-badge" style="flex-shrink:0;padding:4px 8px"></div>\n  <div id="tab-dashboard"'
    if old_tabs_end in c:
        c=c.replace(old_tabs_end,new_tabs_end,1); n+=1; print('3 user-badge div added')
else: print('3 user-badge already exists')

# ── 3. Rewrite renderUserBadge completely ────────────────────────────────
old_fn_start = 'function renderUserBadge() {'
old_fn_end = '\nasync function switchDept('
start = c.find(old_fn_start)
end = c.find(old_fn_end, start)

new_badge = '''function renderUserBadge() {
  const u = S.authUser; if(!u) return
  const badge = document.getElementById('user-badge')
  if (!badge) {
    // inject into nav if missing
    const nav = document.getElementById('main-tabs')
    if (nav && nav.parentNode) {
      const d = document.createElement('div')
      d.id = 'user-badge'
      d.style.cssText = 'flex-shrink:0;padding:4px 8px'
      nav.parentNode.appendChild(d)
    }
  }
  const b = document.getElementById('user-badge'); if(!b) return
  const isMaster = u.role === 'master_admin'
  const isDeptAdmin = u.role === 'dept_admin'
  const isMod = u.role === 'moderator'
  const isUser = u.role === 'user'
  const deptLabel = u.dept_name || u.dept_code || ''
  const initials = (u.full_name||'?').split(' ').map(function(w){return w[0]||''}).join('').slice(0,2).toUpperCase()

  b.innerHTML =
    '<div style="display:flex;align-items:center;gap:8px">'
    + (isMaster
        ? '<select id="dept-switcher" onchange="switchDept(this.value)" style="font-size:11px;padding:3px 8px;height:28px;width:150px;background:#1a2d4a;color:#fff;border:1px solid #2d4a6b;border-radius:6px"><option value="">All Departments</option></select>'
        : '<div style="background:#1a2d4a;border-radius:6px;padding:3px 10px;font-size:11px;color:#60a5fa;font-weight:700">&#127970; '+esc(deptLabel)+'</div>')
    + '<div style="display:flex;align-items:center;gap:6px;background:#1a2d4a;border-radius:20px;padding:3px 10px 3px 5px">'
    + '<div style="width:26px;height:26px;border-radius:50%;background:#1d4ed8;color:#fff;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0">'+initials+'</div>'
    + '<div style="line-height:1.3">'
    + '<div style="font-size:11px;font-weight:700;color:#fff">'+esc(u.full_name||u.username)+'</div>'
    + '<div style="font-size:9px;color:#60a5fa;text-transform:uppercase;letter-spacing:.4px">'+esc((u.role||'').replace(/_/g,' '))+'</div>'
    + '</div></div>'
    + '<a href="/logout" id="logout-btn" title="Sign Out" style="display:flex;align-items:center;justify-content:center;width:28px;height:28px;background:#1a2d4a;border-radius:8px;color:#f87171;font-size:14px;text-decoration:none;border:1px solid #2d4a6b;flex-shrink:0">&#10148;</a>'
    + '</div>'

  // Populate dept switcher for master admin
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

  // Apply role-based tab visibility
  applyRoleVisibility(u.role)
}

function applyRoleVisibility(role) {
  const isMaster = role === 'master_admin'
  const isDeptAdmin = role === 'dept_admin'
  const isMod = role === 'moderator'
  const isUser = role === 'user'

  // Master Setup tab: visible to admin + dept_admin + moderator, hidden from user
  qq('.tab-admin-only').forEach(function(el){
    el.style.display = (isMaster || isDeptAdmin) ? '' : 'none'
  })
  qq('.tab-mod-only').forEach(function(el){
    el.style.display = isMod ? '' : 'none'
  })

  // Org & Cascade: admin + dept_admin only
  // (already handled by tab-admin-only class)

  // Master Setup sub-tabs: Users/Departments hidden from moderator
  qq('.sub-tab[onclick*="users"], .sub-tab[onclick*="departments"]').forEach(function(el){
    el.style.display = (isMaster || isDeptAdmin) ? '' : 'none'
  })

  // master-admin-only items (departments tab)
  qq('.master-admin-only').forEach(function(el){
    el.style.display = isMaster ? '' : 'none'
  })
}
'''

if start != -1 and end != -1:
    c = c[:start] + new_badge + c[end:]
    n+=1; print('4 renderUserBadge fully rewritten')
else:
    print(f'4 SKIP - badge fn not found start={start} end={end}')

# ── 4. Add moderator role support to renderUsers ──────────────────────────
old_role_opts = ("+'<option value=\"user\">User</option>'\n"
                 "      +'<option value=\"dept_admin\">Dept Admin</option>'\n"
                 "      +(isMasterAdmin?'<option value=\"master_admin\">Master Admin</option>':'')")
new_role_opts = ("+'<option value=\"user\">User</option>'\n"
                 "      +'<option value=\"moderator\">Moderator</option>'\n"
                 "      +'<option value=\"dept_admin\">Dept Admin</option>'\n"
                 "      +(isMasterAdmin?'<option value=\"master_admin\">Master Admin</option>':'')")
if old_role_opts in c:
    c=c.replace(old_role_opts,new_role_opts); n+=1; print('5 moderator role option added')
else: print('5 SKIP role opts')

# ── 5. Restrict data editing for user role - add guard to save functions ──
# Add a helper to check if current user can edit master data
guard_fn = """
function canEdit() {
  const r = S.authUser?.role
  return r === 'master_admin' || r === 'dept_admin' || r === 'moderator'
}
function canAdmin() {
  const r = S.authUser?.role
  return r === 'master_admin' || r === 'dept_admin'
}
function requireEdit(msg) {
  if (!canEdit()) { toast(msg || 'You do not have permission to edit', 'err'); return false }
  return true
}
"""
if 'function canEdit()' not in c:
    c=c.replace('function filterMPs()', guard_fn+'\nfunction filterMPs()')
    n+=1; print('6 canEdit/canAdmin guards added')
else: print('6 SKIP guards')

with open('index.html','w',encoding='utf-8') as f: f.write(c)
print(f'\nDone — {n} changes applied')
