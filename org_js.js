// ── BS DATE UTILITIES ─────────────────────────────────────────────────────────
const BS_MONTHS_JS=['Baisakh','Jestha','Ashadh','Shrawan','Bhadra','Ashwin','Kartik','Mangsir','Poush','Magh','Falgun','Chaitra']
const BS_FY_Q_JS={Baisakh:'Q4',Jestha:'Q4',Ashadh:'Q4',Shrawan:'Q1',Bhadra:'Q1',Ashwin:'Q1',Kartik:'Q2',Mangsir:'Q2',Poush:'Q2',Magh:'Q3',Falgun:'Q3',Chaitra:'Q3'}
const BS_MONTH_DAYS_JS={2078:[31,31,32,32,31,30,30,29,30,29,30,30],2079:[31,32,31,32,31,30,30,30,29,29,30,30],2080:[31,32,31,32,31,30,30,30,29,30,29,31],2081:[31,31,32,32,31,30,30,30,29,30,30,30],2082:[31,32,31,32,31,30,30,30,29,30,29,31]}
function bsDays(y,mi){return(BS_MONTH_DAYS_JS[y]||[31,32,31,32,31,30,30,30,29,30,29,31])[mi]||30}
function bsMonthIdx(mn){const i=BS_MONTHS_JS.indexOf(mn);return i>=0?i:0}
function bsStr(y,mn,d){const i=bsMonthIdx(mn);return y+'-'+(i+1).toString().padStart(2,'0')+'-'+String(d).padStart(2,'0')}
function parseBsDate(s){
  if(!s)return{y:2081,m:'Shrawan',d:1}
  const p=String(s).replace(/\//g,'-').split('-')
  if(p.length===3){const y=parseInt(p[0]),mi=parseInt(p[1])-1,d=parseInt(p[2]);if(y>2000&&mi>=0&&mi<12&&d>=1)return{y,m:BS_MONTHS_JS[mi],d:Math.min(d,bsDays(y,mi))}}
  return{y:2081,m:p[0]||'Shrawan',d:1}
}
function bsDisplay(s){if(!s)return'—';const{y,m,d}=parseBsDate(s);return d+' '+m+' '+y+' BS'}
function todayBS(){return S.bsToday&&S.bsToday.date?S.bsToday.date:'2081-07-01'}
function currentFYbs(){return S.bsToday&&S.bsToday.fy?S.bsToday.fy:S.currentFY}

function bsDatePicker(id,val){
  const {y,m,d}=val?parseBsDate(val):parseBsDate(todayBS())
  const yOpts=[2078,2079,2080,2081,2082].map(yr=>'<option value="'+yr+'"'+(yr===y?' selected':'')+'>'+yr+' BS</option>').join('')
  const mOpts=BS_MONTHS_JS.map((mn,i)=>'<option value="'+mn+'"'+(mn===m?' selected':'')+'>'+(i+1)+'. '+mn+'</option>').join('')
  const maxD=bsDays(y,bsMonthIdx(m))
  return '<div class="bs-date-picker" id="'+id+'-wrap">'
    +'<select id="'+id+'-y" onchange="bsPickerSync(\''+id+'\')">'+yOpts+'</select>'
    +'<select id="'+id+'-m" onchange="bsPickerSync(\''+id+'\')">'+mOpts+'</select>'
    +'<input type="number" id="'+id+'-d" value="'+d+'" min="1" max="'+maxD+'">'
    +'<span class="text-xs text-muted" id="'+id+'-lbl">'+d+' '+m+' '+y+' BS</span>'
    +'</div>'
}
function bsPickerSync(id){
  const y=parseInt(q('#'+id+'-y').value),m=q('#'+id+'-m').value
  const maxD=bsDays(y,bsMonthIdx(m)),dEl=q('#'+id+'-d')
  dEl.max=maxD; if(parseInt(dEl.value)>maxD)dEl.value=maxD
  const lbl=q('#'+id+'-lbl'); if(lbl)lbl.textContent=dEl.value+' '+m+' '+y+' BS'
}
function getBsVal(id){
  const y=q('#'+id+'-y')?.value,m=q('#'+id+'-m')?.value,d=q('#'+id+'-d')?.value
  if(!y||!m||!d)return todayBS()
  return bsStr(parseInt(y),m,parseInt(d))
}

// ── ORG & CASCADE TAB ─────────────────────────────────────────────────────────
let orgSub='tree', orgTreeData=null
function switchOrg(s){
  orgSub=s
  qq('#org-tabs .sub-tab').forEach(t=>t.classList.remove('active'))
  event.target.classList.add('active')
  renderOrgTab()
}
function renderOrgTab(){
  if(orgSub==='tree') renderOrgTree()
  else if(orgSub==='builder') renderCascadeBuilder()
  else renderAssignPanel()
}

// ── LIVE ORG TREE WITH ROLLUP ─────────────────────────────────────────────────
async function renderOrgTree(){
  const fyOpts=S.cache.map(c=>'<option value="'+c.fy+'"'+(c.fy===S.currentFY?' selected':'')+'>'+c.fy+'</option>').join('')
  const locOpts=S.locations.map(l=>'<option value="'+esc(l.code)+'">'+esc(l.name)+'</option>').join('')
  const sectOpts=[...new Set(S.employees.map(e=>e.dept))].map(d=>'<option value="'+d+'">'+d+'</option>').join('')
  let html='<div class="card mb-16"><div class="card-body">'
  html+='<div style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end">'
  html+='<div><label class="form-label" style="margin-bottom:3px">Fiscal Year</label>'
  html+='<select class="form-select" id="ot-fy" style="width:120px">'+fyOpts+'</select></div>'
  html+='<div><label class="form-label" style="margin-bottom:3px">Location</label>'
  html+='<select class="form-select" id="ot-loc" style="width:150px"><option value="">All Locations</option>'+locOpts+'</select></div>'
  html+='<div><label class="form-label" style="margin-bottom:3px">Sector</label>'
  html+='<select class="form-select" id="ot-sect" style="width:130px"><option value="">All Sectors</option>'+sectOpts+'</select></div>'
  html+='<button class="btn btn-primary btn-sm" onclick="loadOrgTree()">Load Tree</button>'
  html+='<button class="btn btn-ghost btn-sm" onclick="openAddEmpToOrg()">+ Add Person</button>'
  html+='</div></div></div>'
  html+='<div id="org-tree-wrap"><div class="info-box"><p>Click <strong>Load Tree</strong> to view the live organisation with rollup compliance scores at every level.</p></div></div>'
  q('#org-content').innerHTML=html
}

async function loadOrgTree(){
  const fy=q('#ot-fy')?.value||S.currentFY
  const loc=q('#ot-loc')?.value||'', sect=q('#ot-sect')?.value||''
  q('#org-tree-wrap').innerHTML='<div class="spinner"></div>'
  const url='/api/org/tree?fy='+encodeURIComponent(fy)+'&loc='+encodeURIComponent(loc)+'&sect='+encodeURIComponent(sect)
  orgTreeData=await api.get(url)
  if(!orgTreeData||!orgTreeData.length){
    q('#org-tree-wrap').innerHTML='<p class="text-sm text-muted italic" style="padding:20px">No employees found.</p>'
    return
  }
  q('#org-tree-wrap').innerHTML='<div style="overflow-x:auto;padding:16px">'+drawOrgLevel(orgTreeData,0)+'</div>'
}

function pctCol(p){return p===null||p===undefined?'#94a3b8':p>=95?'#16a34a':p>=80?'#d97706':'#dc2626'}

function drawOrgLevel(nodes,depth){
  if(!nodes||!nodes.length)return''
  return '<div style="display:flex;gap:20px;justify-content:center;flex-wrap:wrap;position:relative">'
    +nodes.map(n=>drawOrgNode(n,depth)).join('')+'</div>'
}

function drawOrgNode(n,depth){
  if(!n)return''
  const col=dc(n.dept||'Ops')
  const ownPct=n.own&&n.own.pct!==null?n.own.pct:null
  const rPct=n.rollup&&n.rollup.pct!==null?n.rollup.pct:null
  const roles=(n.roles||[]).map(r=>'<span class="badge" style="background:'+r.color+';color:#fff;font-size:9px;margin:1px">'+esc(r.code)+'</span>').join('')
  const locs=(n.locations||[]).map(l=>'<span style="font-size:9px;background:#f1f5f9;border-radius:4px;padding:1px 5px;color:#475569">'+esc(l.code)+'</span>').join('')
  const lvlCls='level-'+(n.level||3)
  const mpCnt=(n.mps||[]).length, cpCnt=(n.mps||[]).reduce(function(s,m){return s+(m.cps||[]).length},0)

  let node='<div style="display:inline-flex;flex-direction:column;align-items:center">'
  node+='<div class="org-node" id="on-'+n.id+'" style="border-top:4px solid '+col+'" onclick="orgClick(\''+n.id+'\',event)">'
  node+='<div style="display:flex;gap:8px;align-items:center;margin-bottom:6px">'
  node+='<div class="avatar avatar-sm" style="background:'+col+';flex-shrink:0">'+av(n.name)+'</div>'
  node+='<div style="min-width:0;flex:1">'
  node+='<p style="font-weight:900;font-size:12px;font-family:\'Syne\',sans-serif;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(n.name)+'</p>'
  node+='<p class="text-xxs text-muted" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(n.role||n.dept)+'</p>'
  node+='</div></div>'
  node+='<div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:5px">'
  node+='<span class="level-badge '+lvlCls+'">L'+n.level+'</span>'
  if(roles)node+=roles
  node+='</div>'
  if(locs)node+='<div style="margin-bottom:5px">'+locs+'</div>'
  node+='<div style="display:flex;gap:6px;font-size:10px;color:var(--muted);margin-bottom:6px">'
  node+='<span>'+mpCnt+' MP</span><span>'+cpCnt+' CP</span><span>'+(n.children&&n.children.length||0)+' reports</span>'
  node+='</div>'
  // Own score
  node+='<div style="margin-top:4px">'
  node+='<div style="display:flex;justify-content:space-between;font-size:10px;margin-bottom:2px">'
  node+='<span style="color:var(--muted)">Own</span>'
  node+='<span style="font-weight:700;color:'+pctCol(ownPct)+'">'+(ownPct!==null?ownPct+'%':'—')+'</span></div>'
  node+='<div class="rollup-bar"><div class="rollup-bar-fill" style="width:'+Math.min(ownPct||0,100)+'%;background:'+pctCol(ownPct)+'"></div></div>'
  // Rollup score
  node+='<div style="display:flex;justify-content:space-between;font-size:10px;margin-top:5px;margin-bottom:2px">'
  node+='<span style="color:var(--muted)">Rollup incl. subs</span>'
  node+='<span style="font-weight:900;font-family:\'Syne\',sans-serif;color:'+pctCol(rPct)+'">'+(rPct!==null?rPct+'%':'—')+'</span></div>'
  node+='<div class="rollup-bar"><div class="rollup-bar-fill" style="width:'+Math.min(rPct||0,100)+'%;background:'+pctCol(rPct)+'"></div></div>'
  node+='<div style="font-size:9px;color:var(--muted);margin-top:3px">'+  (n.rollup&&n.rollup.tot?n.rollup.comp+'/'+n.rollup.tot+' records':'No data')+'</div>'
  node+='</div>'
  // Actions
  node+='<div style="display:flex;gap:4px;margin-top:8px;padding-top:8px;border-top:1px solid var(--border)">'
  node+='<button class="btn btn-ghost btn-sm flex-1" style="font-size:10px" onclick="openProfile(\''+n.id+'\',event)">Profile</button>'
  node+='<button class="btn btn-ghost btn-sm" style="font-size:10px" onclick="openOrgActions(\''+n.id+'\',event)">Manage</button>'
  node+='</div></div>'

  if(n.children&&n.children.length){
    node+='<div style="width:2px;height:20px;background:var(--border)"></div>'
    node+='<div style="position:relative;display:flex;gap:16px;flex-wrap:wrap;justify-content:center">'
    if(n.children.length>1)node+='<div style="position:absolute;top:0;left:10%;right:10%;height:2px;background:var(--border)"></div>'
    n.children.forEach(function(child){
      node+='<div style="display:flex;flex-direction:column;align-items:center">'
      node+='<div style="width:2px;height:20px;background:var(--border)"></div>'
      node+=drawOrgNode(child,depth+1)
      node+='</div>'
    })
    node+='</div>'
  }
  node+='</div>'
  return node
}

function orgClick(id,e){
  if(e)e.stopPropagation()
  qq('.org-node').forEach(function(n){n.classList.remove('selected')})
  const el=q('#on-'+id); if(el)el.classList.add('selected')
}

function openOrgActions(id,e){
  if(e)e.stopPropagation()
  const emp=getEmp(id); if(!emp)return
  const col=dc(emp.dept)
  const mgrOpts=S.employees.filter(function(x){return x.id!==id}).map(function(s){
    return '<option value="'+s.id+'"'+(s.id===emp.manager_id?' selected':'')+'>'+esc(s.name)+' (L'+s.level+' '+s.dept+')</option>'
  }).join('')
  const roleChecks=S.roles.map(function(r){
    return '<div class="item-row"><input type="checkbox" value="'+r.id+'" id="oa-r-'+r.id+'" '+((emp.role_ids||[]).includes(r.id)?'checked':'')+'>'
      +'<span class="color-swatch" style="background:'+r.color+'"></span>'
      +'<span class="ref-badge">'+esc(r.code)+'</span>'
      +'<span class="text-xs flex-1">'+esc(r.name)+'</span></div>'
  }).join('')
  openModal('Manage: '+emp.name,
    '<div class="profile-header" style="border-color:'+col+';background:'+col+'10;margin-bottom:16px">'
    +'<div class="avatar avatar-md" style="background:'+col+'">'+av(emp.name)+'</div>'
    +'<div><p style="font-size:16px;font-weight:900;font-family:\'Syne\',sans-serif">'+esc(emp.name)+'</p>'
    +'<p class="text-xs text-muted">'+esc(emp.role||'')+' &middot; L'+emp.level+'</p></div></div>'
    +'<div class="form-group"><label class="form-label">Move under manager</label>'
    +'<select class="form-select" id="oa-mgr"><option value="">Top level (no manager)</option>'+mgrOpts+'</select></div>'
    +'<div class="form-group"><label class="form-label">Roles</label>'
    +'<div class="item-list">'+roleChecks+'</div></div>',
  [{label:'Save',cls:'btn-primary',fn:async function(){
    const newMgr=q('#oa-mgr').value||null
    await api.post('/api/org/move',{emp_id:id,new_manager_id:newMgr})
    const rids=[...document.querySelectorAll('[id^="oa-r-"]:checked')].map(function(x){return x.value})
    await api.post('/api/emp_links/'+id,{role_ids:rids,mp_ids:[],cp_ids:[]})
    toast('Updated','ok'); closeModal(); await loadAll(); loadOrgTree()
  }}],true)
}

function openAddEmpToOrg(){
  const DEPTS=['HOD','Vehicle','Registration','Warehouse','Stock','Ops','Finance','HR']
  const mgrOpts=S.employees.map(function(e){return '<option value="'+e.id+'">'+esc(e.name)+' (L'+e.level+' '+e.dept+')</option>'}).join('')
  openModal('Add Person to Org',
    '<div class="form-grid-2">'
    +'<div class="form-group"><label class="form-label">Code (optional)</label><input class="form-input" id="ae-code" placeholder="Auto"></div>'
    +'<div class="form-group"><label class="form-label">Level</label>'
    +'<select class="form-select" id="ae-level">'
    +'<option value="1">1 - Dept Head</option><option value="2">2 - Team Lead</option>'
    +'<option value="3" selected>3 - Senior Exec</option><option value="4">4 - Executive</option>'
    +'<option value="5">5 - Assistant</option></select></div></div>'
    +'<div class="form-group"><label class="form-label">Full Name</label><input class="form-input" id="ae-name"></div>'
    +'<div class="form-group"><label class="form-label">Designation</label><input class="form-input" id="ae-role"></div>'
    +'<div class="form-grid-2">'
    +'<div class="form-group"><label class="form-label">Sector/Dept</label>'
    +'<select class="form-select" id="ae-dept">'+DEPTS.map(function(d){return'<option>'+d+'</option>'}).join('')+'</select></div>'
    +'<div class="form-group"><label class="form-label">Reports To</label>'
    +'<select class="form-select" id="ae-mgr"><option value="">Top level</option>'+mgrOpts+'</select></div></div>',
  [{label:'Add',cls:'btn-primary',fn:async function(){
    const d={name:q('#ae-name').value,role:q('#ae-role').value,
      emp_code:q('#ae-code').value.trim()||undefined,level:+q('#ae-level').value,
      dept:q('#ae-dept').value,manager_id:q('#ae-mgr').value||null,email:''}
    if(!d.name){toast('Name required','error');return}
    await api.post('/api/employees',d)
    toast('Added','ok'); closeModal(); await loadAll()
    if(orgSub==='tree') loadOrgTree()
  }}])
}

// ── CASCADE BUILDER ───────────────────────────────────────────────────────────
function renderCascadeBuilder(){
  const byParent={}
  S.cascade.forEach(function(lnk){if(!byParent[lnk.parent_emp_id])byParent[lnk.parent_emp_id]=[];byParent[lnk.parent_emp_id].push(lnk)})
  let html='<div class="info-box mb-16"><p><strong>Cascade rule:</strong> Superior\'s <strong>CP</strong> becomes subordinate\'s <strong>MP</strong>. Click <strong>+ New Link</strong> to map the chain.</p></div>'
  html+='<div class="section-head"><div><h2>Cascade Links</h2><p>'+S.cascade.length+' links configured</p></div>'
  html+='<button class="btn btn-primary btn-sm" onclick="openCascadeForm()">+ New Link</button></div>'
  if(!S.cascade.length){
    html+='<div class="card"><div class="card-body" style="text-align:center;padding:32px">'
    html+='<p style="font-size:28px;margin-bottom:8px">&#128279;</p><p class="font-bold">No cascade links yet</p>'
    html+='<p class="text-sm text-muted mt-8">Click <strong>+ New Link</strong> above to start mapping how a superior\'s CP becomes a subordinate\'s MP</p>'
    html+='</div></div>'
  } else {
    html+='<div style="display:flex;flex-direction:column;gap:12px">'
    Object.entries(byParent).forEach(function(kv){
      const pid=kv[0],links=kv[1],parent=getEmp(pid); if(!parent)return
      const col=dc(parent.dept)
      html+='<div class="card"><div class="card-head" style="background:'+col+'10">'
      html+='<div style="display:flex;align-items:center;gap:10px">'
      html+='<div class="avatar avatar-sm" style="background:'+col+'">'+av(parent.name)+'</div>'
      html+='<div><p style="font-weight:900">'+esc(parent.name)+'</p>'
      html+='<p class="text-xxs text-muted">'+esc(parent.emp_code||'')+' &middot; L'+parent.level+' &middot; '+esc(parent.dept)+'</p></div>'
      html+='</div></div><div class="card-body">'
      links.forEach(function(lnk){
        const child=getEmp(lnk.child_emp_id)
        html+='<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid var(--border)">'
        html+='<div style="flex:1">'
        html+='<div style="display:flex;gap:6px;align-items:center;padding:8px;background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;margin-bottom:4px">'
        html+='<span class="ref-badge ref-badge-blue">'+esc(lnk.cp_ref||'CP')+'</span>'
        html+='<span class="text-xs font-bold flex-1">'+esc(lnk.cp_title||'')+'</span>'
        html+='<span class="badge" style="background:#dbeafe;color:#1e40af;font-size:9px">CP</span></div>'
        html+='<div style="text-align:center;font-size:11px;color:#94a3b8;padding:2px">&#8595; becomes MP for &#8595;</div>'
        html+='<div style="display:flex;gap:6px;align-items:center;padding:8px;background:#f0fdf4;border:1px solid #86efac;border-radius:8px">'
        if(child)html+='<div class="avatar avatar-sm" style="background:'+dc(child.dept)+'">'+av(child.name)+'</div>'
          +'<div style="flex-shrink:0"><p class="text-xs font-bold">'+esc(child.name)+'</p>'
          +'<p class="text-xxs text-muted">'+esc(child.emp_code||'')+' L'+child.level+'</p></div>'
        html+='<span class="ref-badge" style="margin-left:4px">'+esc(lnk.mp_ref||'MP')+'</span>'
        html+='<span class="text-xs flex-1">'+esc(lnk.mp_title||'')+'</span>'
        html+='<span class="badge badge-c" style="font-size:9px">MP</span></div></div>'
        html+='<button class="btn-icon" style="color:var(--red);flex-shrink:0" onclick="delCascadeLink(\''+lnk.id+'\')">&#128465;</button></div>'
      })
      html+='</div></div>'
    })
    html+='</div>'
  }
  q('#org-content').innerHTML=html
}

function openCascadeForm(){
  const empOpts=S.employees.map(function(e){return'<option value="'+e.id+'">'+esc(e.name)+' ('+esc(e.emp_code||'')+' L'+e.level+' '+esc(e.dept)+')</option>'}).join('')
  openModal('New Cascade Link',
    '<div class="info-box mb-12"><p>Pick superior\'s CP &#8594; subordinate\'s MP. Leave MP blank to auto-create from the CP.</p></div>'
    +'<div class="form-group"><label class="form-label">&#8593; Superior Employee</label>'
    +'<select class="form-select" id="cl-parent" onchange="refreshCascadeCP()"><option value="">Select...</option>'+empOpts+'</select></div>'
    +'<div id="cl-cp-group" style="display:none" class="form-group"><label class="form-label">Their CP (cascades down)</label>'
    +'<select class="form-select" id="cl-cp" onchange="refreshCascadePreview()"><option value="">Select CP...</option></select></div>'
    +'<div class="form-group"><label class="form-label">&#8595; Subordinate Employee</label>'
    +'<select class="form-select" id="cl-child" onchange="refreshCascadeMP()"><option value="">Select...</option>'+empOpts+'</select></div>'
    +'<div id="cl-mp-group" style="display:none" class="form-group"><label class="form-label">Their MP (blank = auto-create)</label>'
    +'<select class="form-select" id="cl-mp"><option value="">Auto-create MP from CP</option></select></div>'
    +'<div id="cl-prev" style="display:none" class="mt-12"></div>',
  [{label:'Create Link',cls:'btn-primary',fn:async function(){
    const pid=q('#cl-parent').value,cid=q('#cl-cp').value,eid=q('#cl-child').value,mid=q('#cl-mp').value
    if(!pid||!cid||!eid){toast('Superior, CP and subordinate required','error');return}
    const res=await api.post('/api/org/cascade_assign',{parent_emp_id:pid,parent_cp_id:cid,child_emp_id:eid,child_mp_id:mid||undefined})
    if(res.ok){toast('Cascade link created','ok');closeModal();await loadAll();if(orgSub==='builder')renderCascadeBuilder()}
    else toast(res.error||'Error','error')
  }}],true)
}

function refreshCascadeCP(){
  const pid=q('#cl-parent').value,sel=q('#cl-cp')
  if(!pid){q('#cl-cp-group').style.display='none';return}
  const myCPs=S.cps.filter(function(c){return(c.owner_ids||[]).includes(pid)})
  sel.innerHTML='<option value="">Select CP...</option>'+myCPs.map(function(c){
    const mp=S.mps.find(function(m){return m.id===c.mp_id})
    return'<option value="'+c.id+'">['+esc(c.ref)+'] '+esc(c.title.slice(0,50))+(mp?' ('+esc(mp.ref)+')':'')+'</option>'
  }).join('')
  q('#cl-cp-group').style.display=''
  refreshCascadePreview()
}

function refreshCascadeMP(){
  const eid=q('#cl-child').value,sel=q('#cl-mp')
  if(!eid){q('#cl-mp-group').style.display='none';return}
  const myMPs=S.mps.filter(function(m){return(m.owner_ids||[]).includes(eid)})
  sel.innerHTML='<option value="">Auto-create MP from CP</option>'+myMPs.map(function(m){
    return'<option value="'+m.id+'">['+esc(m.ref)+'] '+esc(m.title.slice(0,50))+'</option>'
  }).join('')
  q('#cl-mp-group').style.display=''
  refreshCascadePreview()
}

function refreshCascadePreview(){
  const pid=q('#cl-parent')?.value,cid=q('#cl-cp')?.value,eid=q('#cl-child')?.value,mid=q('#cl-mp')?.value
  const prev=q('#cl-prev'); if(!prev)return
  if(pid&&cid&&eid){
    const pe=getEmp(pid),cp=S.cps.find(function(c){return c.id===cid}),ce=getEmp(eid),mp=mid?S.mps.find(function(m){return m.id===mid}):null
    prev.style.display=''
    prev.innerHTML='<div style="background:#f8fafc;border:1.5px solid var(--border);border-radius:10px;padding:12px">'
      +'<p class="text-xxs text-muted font-bold" style="text-transform:uppercase;margin-bottom:8px">Preview</p>'
      +'<div style="display:flex;gap:8px;align-items:center;margin-bottom:4px">'
      +(pe?'<div class="avatar avatar-sm" style="background:'+dc(pe.dept)+'">'+av(pe.name)+'</div>':'')
      +'<span class="font-bold text-sm">'+(pe?esc(pe.name):'—')+'</span>'
      +(cp?'<span class="ref-badge ref-badge-blue">'+esc(cp.ref)+'</span><span class="text-xs flex-1">'+esc(cp.title.slice(0,40))+'</span>':'')
      +'</div><div style="text-align:center;color:#94a3b8;font-size:12px;padding:4px">&#8595; cascades to &#8595;</div>'
      +'<div style="display:flex;gap:8px;align-items:center">'
      +(ce?'<div class="avatar avatar-sm" style="background:'+dc(ce.dept)+'">'+av(ce.name)+'</div>':'')
      +'<span class="font-bold text-sm">'+(ce?esc(ce.name):'—')+'</span>'
      +(mp?'<span class="ref-badge">'+esc(mp.ref)+'</span><span class="text-xs flex-1">'+esc(mp.title.slice(0,40))+'</span>'
          :'<span class="text-xs text-muted italic">Will auto-create MP from CP</span>')
      +'</div></div>'
  } else prev.style.display='none'
}

async function delCascadeLink(id){
  if(!confirm('Remove this cascade link?'))return
  await api.del('/api/cascade/'+id)
  toast('Link removed','ok'); await loadAll()
  if(orgSub==='builder')renderCascadeBuilder()
}

// ── ASSIGN MP/CP PANEL ────────────────────────────────────────────────────────
function renderAssignPanel(){
  const locOpts=S.locations.map(function(l){return'<option value="'+l.id+'">['+esc(l.code)+'] '+esc(l.name)+'</option>'}).join('')
  let html='<div class="section-head"><div><h2>Assign MP / CP</h2>'
  html+='<p>Assign managing and checking points to employees by location or sector</p></div></div>'
  html+='<div class="grid-2" style="gap:16px">'
  html+='<div class="card"><div class="card-head"><p>Select Employee</p></div>'
  html+='<div class="card-body" style="max-height:420px;overflow-y:auto">'
  S.employees.forEach(function(e){
    const col=dc(e.dept)
    html+='<div class="assign-card" id="ac-'+e.id+'" onclick="selectAssignEmp(\''+e.id+'\')">'
    html+='<div style="display:flex;gap:8px;align-items:center">'
    html+='<div class="avatar avatar-sm" style="background:'+col+'">'+av(e.name)+'</div>'
    html+='<div><p class="font-bold text-sm">'+esc(e.name)+'</p>'
    html+='<p class="text-xxs text-muted">'+esc(e.emp_code||'')+' &middot; L'+e.level+' &middot; '+esc(e.dept)+'</p></div>'
    html+='</div></div>'
  })
  html+='</div></div>'
  html+='<div id="assign-right" class="card"><div class="card-head"><p>MP/CP Assignment</p></div>'
  html+='<div class="card-body"><p class="text-sm text-muted italic">Select an employee on the left.</p></div></div>'
  html+='</div>'
  q('#org-content').innerHTML=html
}

let assignEmp=null
function selectAssignEmp(id){
  assignEmp=id
  qq('[id^="ac-"]').forEach(function(c){c.classList.remove('selected')})
  const el=q('#ac-'+id); if(el)el.classList.add('selected')
  const emp=getEmp(id); if(!emp)return
  const col=dc(emp.dept)
  const ownMPs=S.mps.filter(function(m){return(m.owner_ids||[]).includes(id)}).map(function(m){return m.id})
  const ownCPs=S.cps.filter(function(c){return(c.owner_ids||[]).includes(id)}).map(function(c){return c.id})
  const locOpts=S.locations.map(function(l){return'<option value="'+l.id+'">['+esc(l.code)+'] '+esc(l.name)+'</option>'}).join('')
  const right=q('#assign-right')
  right.innerHTML='<div class="card-head" style="background:'+col+'10">'
    +'<div style="display:flex;gap:8px;align-items:center">'
    +'<div class="avatar avatar-sm" style="background:'+col+'">'+av(emp.name)+'</div>'
    +'<div><p class="font-bold">'+esc(emp.name)+'</p>'
    +'<p class="text-xxs text-muted">'+esc(emp.emp_code||'')+' &middot; L'+emp.level+'</p></div>'
    +'</div></div>'
    +'<div class="card-body">'
    +'<div class="form-group"><label class="form-label">Location Context</label>'
    +'<select class="form-select" id="asgn-loc"><option value="">No specific location</option>'+locOpts+'</select></div>'
    +'<p class="text-xxs text-muted font-bold" style="text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px">Managing Points</p>'
    +'<div style="max-height:160px;overflow-y:auto;border:1.5px solid var(--border);border-radius:8px;margin-bottom:12px">'
    +S.mps.map(function(m){return'<div class="item-row"><input type="checkbox" id="asgn-mp-'+m.id+'" '+(ownMPs.includes(m.id)?'checked':'')+'>'
      +'<span class="ref-badge">'+esc(m.ref)+'</span><span class="text-xs flex-1">'+esc(m.title.slice(0,50))+'</span></div>'}).join('')
    +'</div>'
    +'<p class="text-xxs text-muted font-bold" style="text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px">Checking Points</p>'
    +'<div style="max-height:160px;overflow-y:auto;border:1.5px solid var(--border);border-radius:8px;margin-bottom:12px">'
    +S.cps.map(function(c){const mp=S.mps.find(function(m){return m.id===c.mp_id});
      return'<div class="item-row"><input type="checkbox" id="asgn-cp-'+c.id+'" '+(ownCPs.includes(c.id)?'checked':'')+'>'
        +(mp?'<span class="ref-badge" style="font-size:9px">'+esc(mp.ref)+'</span>':'')
        +'<span class="ref-badge ref-badge-blue">'+esc(c.ref)+'</span>'
        +'<span class="text-xs flex-1">'+esc(c.title.slice(0,45))+'</span></div>'}).join('')
    +'</div>'
    +'<button class="btn btn-success btn-sm" onclick="saveAssignments(\''+id+'\')">Save Assignments</button>'
    +'</div>'
}

async function saveAssignments(empId){
  const locId=q('#asgn-loc')?.value||''
  const mpIds=[...document.querySelectorAll('[id^="asgn-mp-"]:checked')].map(function(x){return x.id.replace('asgn-mp-','')})
  const cpIds=[...document.querySelectorAll('[id^="asgn-cp-"]:checked')].map(function(x){return x.id.replace('asgn-cp-','')})
  await api.post('/api/emp_links/'+empId,{role_ids:(getEmp(empId)?.role_ids||[]),mp_ids:mpIds,cp_ids:cpIds})
  if(locId){
    for(const mid of mpIds) await api.post('/api/org/assign_mp',{emp_id:empId,mp_id:mid,loc_id:locId})
    for(const cid of cpIds) await api.post('/api/org/assign_cp',{emp_id:empId,cp_id:cid,loc_id:locId})
  }
  toast('Assignments saved','ok'); await loadAll()
  selectAssignEmp(empId)
}
