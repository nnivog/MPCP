import re

with open('index.html', 'r', encoding='utf-8') as f:
    txt = f.read()

print("Starting patch...")
changed = []

# ── 1. Nav tab ──
if "switchTab('locations')" not in txt:
    txt = txt.replace(
        "onclick=\"switchTab('reports')\">📈 Reports</button>",
        "onclick=\"switchTab('reports')\">📈 Reports</button>\n    <button class=\"nav-tab\" onclick=\"switchTab('locations')\">📍 Locations</button>"
    )
    changed.append("nav tab")

# ── 2. Tab panel ──
if 'id="tab-locations"' not in txt:
    txt = txt.replace(
        '<div id="tab-reports" class="tab-panel">',
        '<div id="tab-locations" class="tab-panel"><div class="spinner"></div></div>\n\n<div id="tab-reports" class="tab-panel">'
    )
    changed.append("tab panel")

# ── 3. State ──
if 'locations:[]' not in txt:
    txt = txt.replace('const S = {', 'const S = {\n  locations:[],')
    changed.append("state")

# ── 4. loadAll - find exact pattern and patch once ──
# Find the Promise.all line and patch it
old_destructure = None
old_api_line    = None
old_assign_line = None

# Try to find current patterns
for pattern in [
    "const [e,m,c,r,p,ca] = await Promise.all([",
    "const [e,m,c,r,p,ca,lo] = await Promise.all(["
]:
    if pattern in txt:
        old_destructure = pattern
        break

for pattern in [
    "api.get('/api/roles'), api.get('/api/perf'), api.get('/api/cache')",
    "api.get('/api/roles'), api.get('/api/perf'), api.get('/api/cache'), api.get('/api/locations')"
]:
    if pattern in txt:
        old_api_line = pattern
        break

for pattern in [
    "S.employees=e; S.mps=m; S.cps=c; S.roles=r; S.perf=p; S.cache=ca",
    "S.employees=e; S.mps=m; S.cps=c; S.roles=r; S.perf=p; S.cache=ca; S.locations=lo"
]:
    if pattern in txt:
        old_assign_line = pattern
        break

print("Found destructure:", old_destructure)
print("Found api line:", old_api_line)
print("Found assign line:", old_assign_line)

if old_destructure and 'lo' not in old_destructure:
    txt = txt.replace(old_destructure,
        "const [e,m,c,r,p,ca,lo] = await Promise.all([")
    changed.append("destructure")

if old_api_line and 'locations' not in old_api_line:
    txt = txt.replace(old_api_line,
        "api.get('/api/roles'), api.get('/api/perf'), api.get('/api/cache'), api.get('/api/locations')")
    changed.append("api list")

if old_assign_line and 'lo' not in old_assign_line:
    txt = txt.replace(old_assign_line,
        "S.employees=e; S.mps=m; S.cps=c; S.roles=r; S.perf=p; S.cache=ca; S.locations=lo")
    changed.append("assign")

# ── 5. Router ──
if 'renderLocations' not in txt:
    txt = txt.replace(
        "else if(S.currentTab==='reports') renderReport()",
        "else if(S.currentTab==='reports') renderReport()\n  else if(S.currentTab==='locations') renderLocations()"
    )
    changed.append("router")

# ── 6. Inject JS once before LAST </script> ──
if 'function renderLocations' not in txt:
    loc_js = """
// ── LOCATIONS ─────────────────────────────────────────────────────────────

function renderLocations() {
  var TCOLOR = {'HQ':'#0f2540','Branch':'#1d4ed8','Depot':'#047857','Warehouse':'#0891b2','Border Point':'#b45309','Other':'#475569'};
  var el = document.getElementById('tab-locations');
  var html = '<div class="section-head"><div><h2>Locations</h2><p>' + S.locations.length + ' location(s)</p></div>' +
    '<button class="btn btn-primary btn-sm" onclick="openLocForm()">+ Add Location</button></div>';
  if (!S.locations.length) {
    el.innerHTML = html + '<div class="card" style="padding:48px;text-align:center">' +
      '<p style="font-size:32px">&#128205;</p><p class="font-black mt-8">No locations yet</p>' +
      '<button class="btn btn-primary mt-16" onclick="openLocForm()">+ Add First Location</button></div>';
    return;
  }
  html += '<div class="grid-3">';
  S.locations.forEach(function(loc) {
    var color = TCOLOR[loc.type] || '#475569';
    var emps  = (loc.emp_ids||[]).map(function(id){return S.employees.find(function(e){return e.id===id;});}).filter(Boolean);
    var chips = emps.map(function(e){return '<span class="owner-chip" style="background:'+dc(e.dept)+'">'+e.name.split(' ')[0]+'</span>';}).join('');
    html += '<div class="card" style="border-top:3px solid '+color+';padding:16px;opacity:'+(loc.active?'1':'0.5')+'">' +
      '<div class="flex items-start justify-between mb-12">' +
        '<div style="display:flex;gap:6px;flex-wrap:wrap">' +
          '<span class="ref-badge" style="background:'+color+';color:#fff">'+esc(loc.code)+'</span>' +
          '<span class="badge" style="background:'+color+'22;color:'+color+'">'+esc(loc.type)+'</span>' +
          (loc.dept?'<span class="dept-badge" style="background:'+dc(loc.dept)+'">'+esc(loc.dept)+'</span>':'') +
          (!loc.active?'<span class="badge badge-gray">Inactive</span>':'') +
        '</div>' +
        '<div class="flex gap-6">' +
          '<button class="btn-icon" onclick="openLocForm(\''+loc.id+'\')">&#9998;</button>' +
          '<button class="btn-icon" style="color:var(--red)" onclick="delLoc(\''+loc.id+'\')">&#128465;</button>' +
        '</div>' +
      '</div>' +
      '<p class="font-black" style="font-size:15px">'+esc(loc.name)+'</p>' +
      '<p class="text-xs text-muted mt-4">'+esc(loc.address||'-')+'</p>' +
      '<p class="text-xxs text-muted mt-8">'+emps.length+' staff</p>' +
      (chips?'<div class="mp-owners mt-8">'+chips+'</div>':'') +
    '</div>';
  });
  el.innerHTML = html + '</div>';
}

function openLocForm(id) {
  var loc   = id ? S.locations.find(function(l){return l.id===id;}) : null;
  var TYPES = ['HQ','Branch','Depot','Warehouse','Border Point','Other'];
  var DEPTS = ['HOD','Vehicle','Registration','Warehouse','Stock','Ops','Finance','HR'];
  var tOpts = TYPES.map(function(t){return '<option'+(loc&&loc.type===t?' selected':'')+'>'+t+'</option>';}).join('');
  var dOpts = DEPTS.map(function(d){return '<option'+(loc&&loc.dept===d?' selected':'')+'>'+d+'</option>';}).join('');
  var body =
    '<div class="form-grid-2">' +
      '<div class="form-group"><label class="form-label">Location Code</label>' +
        '<input class="form-input" id="lf-code" value="'+esc(loc?loc.code:'')+'" placeholder="e.g. KTM-HQ"></div>' +
      '<div class="form-group"><label class="form-label">Type</label>' +
        '<select class="form-select" id="lf-type">'+tOpts+'</select></div>' +
    '</div>' +
    '<div class="form-group"><label class="form-label">Location Name</label>' +
      '<input class="form-input" id="lf-name" value="'+esc(loc?loc.name:'')+'" placeholder="e.g. Kathmandu HQ"></div>' +
    '<div class="form-group"><label class="form-label">Address</label>' +
      '<input class="form-input" id="lf-address" value="'+esc(loc?loc.address||'':'')+'" placeholder="Full address"></div>' +
    '<div class="form-grid-2">' +
      '<div class="form-group"><label class="form-label">Department / Sector</label>' +
        '<select class="form-select" id="lf-dept">'+dOpts+'</select></div>' +
      '<div class="form-group"><label class="form-label">Status</label>' +
        '<select class="form-select" id="lf-active">' +
          '<option value="1"'+(!loc||loc.active?' selected':'')+'>Active</option>' +
          '<option value="0"'+(loc&&!loc.active?' selected':'')+'>Inactive</option>' +
        '</select></div>' +
    '</div>' +
    '<div class="form-group"><label class="form-label">Assigned Staff</label>' +
      buildOwnerPicker('lf-emps', loc?loc.emp_ids||[]:[]) +
    '</div>';
  openModal(loc?'Edit Location':'Add Location', body, [{
    label: loc?'Save Changes':'Add Location', cls:'btn-primary',
    fn: function() {
      var code = document.getElementById('lf-code').value.trim();
      var name = document.getElementById('lf-name').value.trim();
      if (!code||!name){toast('Code and name required','error');return;}
      var d = {
        code:code, name:name,
        address:document.getElementById('lf-address').value.trim(),
        type:document.getElementById('lf-type').value,
        dept:document.getElementById('lf-dept').value,
        active:document.getElementById('lf-active').value==='1',
        emp_ids:getOwnerPicked('lf-emps')
      };
      (loc ? api.put('/api/locations/'+loc.id, Object.assign({id:loc.id},d))
           : api.post('/api/locations', d))
      .then(function(res){
        if(res.error){toast('Error: '+res.error,'error');return;}
        toast(loc?'Location updated':'Location added','ok');
        closeModal(); loadAll();
      }).catch(function(err){toast('Error: '+err.message,'error');});
    }
  }], true);
}

function delLoc(id) {
  var loc = S.locations.find(function(l){return l.id===id;});
  if (!confirm('Delete "'+(loc?loc.name:id)+'"?')) return;
  api.del('/api/locations/'+id).then(function(){toast('Deleted','ok');loadAll();});
}
"""
    # Insert before the last </script>
    last = txt.rfind('</script>')
    txt  = txt[:last] + loc_js + '\n</script>' + txt[last+9:]
    changed.append("JS functions")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(txt)

print("Changed:", changed)
print("Final </script> count:", txt.count('</script>'))
print("renderLocations count:", txt.count('function renderLocations'))
print("Done!")
