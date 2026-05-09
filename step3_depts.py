with open('index.html','r',encoding='utf-8') as f: c=f.read()
n=0

# 1. Add Departments sub-tab in Master Setup (master_admin only — shown conditionally via JS)
old_mt = '<button class="sub-tab" onclick="switchMaster(\'users\')">&#128100; Users</button>'
new_mt = '<button class="sub-tab" onclick="switchMaster(\'departments\')">&#127970; Departments</button>\n      ' + old_mt
if old_mt in c and "switchMaster('departments')" not in c:
    c=c.replace(old_mt,new_mt); n+=1; print('1 Departments sub-tab added')
else: print('1 SKIP')

# 2. Wire renderDepartments into renderMaster
old_mh = "else if(S.masterSub==='users') renderUsers()"
new_mh = "else if(S.masterSub==='users') renderUsers()\n  else if(S.masterSub==='departments') renderDepartments()"
if old_mh in c and 'renderDepartments()' not in c:
    c=c.replace(old_mh,new_mh); n+=1; print('2 renderDepartments wired')
else: print('2 SKIP')

# 3. Hide Departments sub-tab for non-master-admin
# Find switchMaster function and add dept tab visibility logic after renderUserBadge call
old_rb = "    renderUserBadge()\n  } catch(e) { window.location='/login'; return }"
new_rb = """    renderUserBadge()
    // Show/hide master-only tabs
    qq('.master-admin-only').forEach(function(el){
      el.style.display=(S.authUser&&S.authUser.role==='master_admin')?'':'none'
    })
  } catch(e) { window.location='/login'; return }"""
if old_rb in c:
    c=c.replace(old_rb,new_rb); n+=1; print('3 master-only tab visibility added')

# Mark the Departments sub-tab as master-admin-only
c=c.replace(
    '<button class="sub-tab" onclick="switchMaster(\'departments\')">&#127970; Departments</button>',
    '<button class="sub-tab master-admin-only" onclick="switchMaster(\'departments\')">&#127970; Departments</button>'
)

# 4. Add renderDepartments function
depts_fn = """
function renderDepartments() {
  if(!S.authUser||S.authUser.role!=='master_admin'){
    q('#master-content').innerHTML='<div class="info-box"><p>Master Admin only.</p></div>';return
  }
  fetch('/api/departments').then(function(r){return r.json()}).then(function(depts){
    let html='<div class="card"><div class="card-head"><p>Departments ('+depts.length+' / 15)</p>'
    html+='<button class="btn btn-primary btn-sm" onclick="openDeptForm()">+ New Department</button></div>'
    html+='<div class="card-body">'
    html+='<p style="font-size:11px;color:var(--muted);margin-bottom:16px">Each department has its own isolated database. Create a department, then assign a Dept Admin in the Users tab.</p>'
    html+='<div class="grid-3">'
    depts.forEach(function(d){
      const pct=d.compliance!==null&&d.compliance!==undefined?d.compliance:null
      const barCol=pct===null?'#94a3b8':pct>=95?'#16a34a':pct>=80?'#d97706':'#dc2626'
      html+='<div class="stat-box" style="border-top:4px solid '+barCol+';text-align:left;padding:14px">'
      html+='<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">'
      html+='<div>'
      html+='<div style="font-size:10px;font-weight:800;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-family:monospace">'+esc(d.code)+'</div>'
      html+='<div style="font-size:14px;font-weight:700;color:var(--text);margin-top:2px">'+esc(d.name)+'</div>'
      html+='</div>'
      html+='<span style="background:'+(d.active?'#dcfce7':'#fee2e2')+';color:'+(d.active?'#16a34a':'#dc2626')+';padding:2px 8px;border-radius:4px;font-size:9px;font-weight:700">'+(d.active?'ACTIVE':'INACTIVE')+'</span>'
      html+='</div>'
      html+='<div style="display:flex;gap:16px;font-size:11px;color:var(--muted);margin-bottom:10px">'
      html+='<span>&#128100; '+d.user_count+' users</span>'
      html+='<span>&#128106; '+(d.employees||'?')+' employees</span>'
      html+='</div>'
      if(pct!==null){
        html+='<div style="display:flex;justify-content:space-between;font-size:10px;margin-bottom:3px">'
        html+='<span style="color:var(--muted)">Compliance</span>'
        html+='<span style="font-weight:700;color:'+barCol+'">'+pct+'%</span></div>'
        html+='<div style="height:4px;background:#f1f5f9;border-radius:2px;overflow:hidden">'
        html+='<div style="height:4px;width:'+Math.min(pct,100)+'%;background:'+barCol+';border-radius:2px"></div></div>'
      } else {
        html+='<div style="font-size:10px;color:var(--muted);font-style:italic">No performance data yet</div>'
      }
      html+='<div style="display:flex;gap:6px;margin-top:12px">'
      html+='<button class="btn btn-ghost btn-sm" style="font-size:10px" onclick="switchDept('+JSON.stringify(d.code)+').then(()=>switchTab(\'dashboard\'))">&#128065; View</button>'
      html+='<button class="btn btn-ghost btn-sm" style="font-size:10px" onclick="openDeptForm('+JSON.stringify(d.id)+','+JSON.stringify(d.name)+','+JSON.stringify(d.active)+')">&#9998; Edit</button>'
      html+='</div>'
      html+='</div>'
    })
    if(!depts.length) html+='<div class="info-box"><p>No departments yet. Create your first department to get started.</p></div>'
    html+='</div></div></div>'

    // Also show master summary stats at top
    fetch('/api/master/summary').then(function(r){return r.json()}).then(function(summary){
      const totalEmps=summary.reduce(function(s,d){return s+(d.employees||0)},0)
      const totalMPs=summary.reduce(function(s,d){return s+(d.mps||0)},0)
      const totalCPs=summary.reduce(function(s,d){return s+(d.cps||0)},0)
      const withComp=summary.filter(function(d){return d.compliance!==null})
      const avgComp=withComp.length?Math.round(withComp.reduce(function(s,d){return s+d.compliance},0)/withComp.length*10)/10:null
      const statsHtml='<div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap">'
        +'<div class="stat-box" style="padding:10px 16px;flex:1;min-width:100px"><div class="val" style="color:var(--blue)">'+depts.length+'</div><div class="lbl">Departments</div></div>'
        +'<div class="stat-box" style="padding:10px 16px;flex:1;min-width:100px"><div class="val" style="color:var(--violet)">'+totalEmps+'</div><div class="lbl">Total Employees</div></div>'
        +'<div class="stat-box" style="padding:10px 16px;flex:1;min-width:100px"><div class="val" style="color:#047857">'+totalMPs+'</div><div class="lbl">Total MPs</div></div>'
        +'<div class="stat-box" style="padding:10px 16px;flex:1;min-width:100px"><div class="val" style="color:#d97706">'+totalCPs+'</div><div class="lbl">Total CPs</div></div>'
        +(avgComp!==null?'<div class="stat-box" style="padding:10px 16px;flex:1;min-width:100px"><div class="val" style="color:'+(avgComp>=95?'#16a34a':avgComp>=80?'#d97706':'#dc2626')+'">'+avgComp+'%</div><div class="lbl">Avg Compliance</div></div>':'')
        +'</div>'
      q('#master-content').innerHTML=statsHtml+html
    }).catch(function(){q('#master-content').innerHTML=html})
  })
}

function openDeptForm(did, dname, dactive) {
  const isEdit=!!did
  const body='<div class="form-group"><label class="form-label">Department Name *</label>'
    +'<input class="form-input" id="df-name" placeholder="e.g. Finance & Accounts" value="'+(dname?esc(dname):'')+'"></div>'
    +(isEdit?'':'<div class="form-group"><label class="form-label">Department Code *</label>'
    +'<input class="form-input" id="df-code" placeholder="e.g. finance (lowercase, no spaces)">'
    +'<p class="text-xs text-muted mt-4">Used as DB filename. Cannot be changed later.</p></div>')
    +(isEdit?'<div class="form-group"><label class="form-label">Status</label>'
    +'<select class="form-select" id="df-active"><option value="1"'+(dactive?' selected':'')+'">Active</option><option value="0"'+(dactive?'':' selected')+'>Inactive</option></select></div>':'')
  openModal(isEdit?'Edit Department':'New Department',body,[
    {label:isEdit?'Save':'Create Department',cls:'btn-primary',fn:async function(){
      const name=q('#df-name')?.value?.trim()
      if(!name){toast('Department name required','err');return}
      let r
      if(isEdit){
        const active=q('#df-active')?.value==='1'
        r=await api.put('/api/departments/'+did,{name,active})
      } else {
        const code=q('#df-code')?.value?.trim().toLowerCase().replace(/[^a-z0-9_]/g,'_')
        if(!code){toast('Code required','err');return}
        r=await api.post('/api/departments',{code,name})
      }
      if(r?.ok||r?.id){toast(isEdit?'Department updated':'Department created — DB initialized','ok');closeModal();renderDepartments()}
      else toast('Error: '+(r?.error||'Unknown'),'err')
    }},
    {label:'Cancel',cls:'btn-ghost',fn:()=>closeModal()}
  ],true)
}
"""
if 'function renderDepartments()' not in c:
    c=c.replace('function renderUsers()', depts_fn+'\nfunction renderUsers()')
    n+=1; print('4 renderDepartments + openDeptForm added')
else: print('4 SKIP')

with open('index.html','w',encoding='utf-8') as f: f.write(c)
print(f'\nDone — {n} changes applied')
