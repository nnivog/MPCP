import re, sys

# ── PATCH app.py ──────────────────────────────────────────────────────────────
with open('app.py', 'r', encoding='utf-8') as f:
    src = f.read()

# 1. Fix Unicode bug
old = "with open(os.path.join(os.path.dirname(__file__),'index.html'),'r') as f: return f.read()"
new = "with open(os.path.join(os.path.dirname(__file__),'index.html'),'r', encoding='utf-8') as f: return f.read()"
src = src.replace(old, new)

# 2. Add location tables to SCHEMA
old = 'CREATE TABLE IF NOT EXISTS perf_cache('
new = """CREATE TABLE IF NOT EXISTS locations(
  id TEXT PRIMARY KEY, code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL, type TEXT DEFAULT 'Office',
  address TEXT DEFAULT '');

CREATE TABLE IF NOT EXISTS emp_locations(
  emp_id TEXT, loc_id TEXT, PRIMARY KEY(emp_id, loc_id));

CREATE TABLE IF NOT EXISTS cp_locations(
  cp_id TEXT, loc_id TEXT, PRIMARY KEY(cp_id, loc_id));

CREATE TABLE IF NOT EXISTS mp_locations(
  mp_id TEXT, loc_id TEXT, PRIMARY KEY(mp_id, loc_id));

CREATE TABLE IF NOT EXISTS perf_cache("""
src = src.replace(old, new)

# 3. Add location column to perf table
old = "status TEXT DEFAULT 'C', notes TEXT DEFAULT '');"
new = "status TEXT DEFAULT 'C', notes TEXT DEFAULT '', location TEXT DEFAULT '');"
src = src.replace(old, new)

# 4. Add location seed data
old = '    for fy in ["2080-81","2081-82"]: _upd_cache(db,fy)'
new = '''    locs=[
        ("loc1","HQ","Head Office - Sipradi","Office","Kathmandu"),
        ("loc2","BORDER","Border Clearance Station","Border","Birgunj"),
        ("loc3","WH-KTM","Kathmandu Warehouse","Warehouse","Kathmandu"),
        ("loc4","REG-KTM","Registration Office","Office","Kathmandu"),
        ("loc5","WH-BRG","Birgunj Warehouse","Warehouse","Birgunj"),
    ]
    db.executemany("INSERT OR IGNORE INTO locations VALUES(?,?,?,?,?)",locs)
    emp_locs=[
        ("e1","loc1"),("e2","loc1"),("e2","loc2"),("e3","loc2"),("e4","loc4"),
        ("e5","loc4"),("e6","loc4"),("e7","loc2"),("e8","loc1"),("e9","loc1"),
        ("e10","loc1"),("e11","loc3"),("e12","loc3"),("e13","loc3"),("e14","loc3"),
        ("e15","loc2"),("e16","loc1"),
    ]
    db.executemany("INSERT OR IGNORE INTO emp_locations VALUES(?,?)",emp_locs)
    for fy in ["2080-81","2081-82"]: _upd_cache(db,fy)'''
src = src.replace(old, new)

# 5. Inject Location API routes before index route
location_api = '''
# -- LOCATIONS -----------------------------------------------------------------
@app.route('/api/locations', methods=['GET','POST'])
def locations_api():
    db = get_db()
    if request.method == 'GET':
        res = []
        for loc in db.execute("SELECT * FROM locations ORDER BY code"):
            l = dict(loc)
            l['emp_ids'] = [r['emp_id'] for r in db.execute(
                "SELECT emp_id FROM emp_locations WHERE loc_id=?", (l['id'],))]
            res.append(l)
        return jsonify(res)
    d = request.json; lid = d.get('id') or uid()
    db.execute("INSERT OR REPLACE INTO locations VALUES(?,?,?,?,?)",
               (lid, d['code'], d['name'], d.get('type','Office'), d.get('address','')))
    db.execute("DELETE FROM emp_locations WHERE loc_id=?", (lid,))
    for eid in d.get('emp_ids', []):
        db.execute("INSERT OR IGNORE INTO emp_locations VALUES(?,?)", (eid, lid))
    db.commit(); return jsonify({'id': lid})

@app.route('/api/locations/<lid>', methods=['PUT','DELETE'])
def location_api(lid):
    db = get_db()
    if request.method == 'DELETE':
        for t,c in [('locations','id'),('emp_locations','loc_id'),
                    ('cp_locations','loc_id'),('mp_locations','loc_id')]:
            db.execute(f"DELETE FROM {t} WHERE {c}=?", (lid,))
        db.commit(); return jsonify({'ok': True})
    d = request.json
    db.execute("UPDATE locations SET code=?,name=?,type=?,address=? WHERE id=?",
               (d['code'], d['name'], d.get('type','Office'), d.get('address',''), lid))
    db.execute("DELETE FROM emp_locations WHERE loc_id=?", (lid,))
    for eid in d.get('emp_ids', []):
        db.execute("INSERT OR IGNORE INTO emp_locations VALUES(?,?)", (eid, lid))
    db.commit(); return jsonify({'ok': True})

@app.route('/api/analytics/by_location')
def analytics_by_location():
    db = get_db(); fy = request.args.get('fy','')
    locs = db.execute("SELECT * FROM locations ORDER BY code").fetchall()
    result = {}
    for loc in locs:
        emp_ids = [r['emp_id'] for r in db.execute(
            "SELECT emp_id FROM emp_locations WHERE loc_id=?", (loc['id'],))]
        if emp_ids:
            emp_codes = [r['emp_code'] for r in db.execute(
                "SELECT emp_code FROM employees WHERE id IN ({})".format(
                    ','.join('?'*len(emp_ids))), emp_ids)]
        else:
            emp_codes = []
        q2 = "SELECT * FROM perf WHERE 1=1"; args = []
        if fy: q2 += " AND fy=?"; args.append(fy)
        if emp_codes:
            q2 += " AND emp_code IN ({})".format(','.join('?'*len(emp_codes)))
            args += emp_codes
        rows = db.execute(q2, args).fetchall()
        tot  = sum(r['total'] or 1 for r in rows)
        comp = sum(r['compliant'] or (1 if r['status']=='C' else 0) for r in rows)
        nc   = tot - comp
        result[loc['code']] = {
            'id': loc['id'], 'name': loc['name'], 'type': loc['type'],
            'address': loc['address'], 'emp_count': len(emp_ids), 'emp_ids': emp_ids,
            'total': tot, 'compliant': comp, 'nc': nc,
            'pct_c':  round(comp/tot*100, 2) if tot else 0,
            'pct_nc': round(nc/tot*100,   2) if tot else 0,
        }
    return jsonify(result)

'''

old = "@app.route('/')\ndef index():"
src = src.replace(old, location_api + old)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(src)
print("app.py patched OK")

# ── PATCH index.html ──────────────────────────────────────────────────────────
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

changes = 0

# 1. Add locations to state S
old = "currentTab:'dashboard', teamView:'cards', masterSub:'mps',"
new = "locations:[], currentTab:'dashboard', teamView:'cards', masterSub:'mps',"
if old in html: html = html.replace(old, new); changes+=1
else: print("WARN: state S location not found")

# 2. Load locations in loadAll
old = "api.get('/api/roles'), api.get('/api/perf'), api.get('/api/cache')\n\t])\n\tS.employees=e; S.mps=m; S.cps=c; S.roles=r; S.perf=p; S.cache=ca"
new = "api.get('/api/roles'), api.get('/api/perf'), api.get('/api/cache'),\n\t\tapi.get('/api/locations')\n\t])\n\tS.employees=e; S.mps=m; S.cps=c; S.roles=r; S.perf=p; S.cache=ca; S.locations=locs"
if old in html: html = html.replace(old, new); changes+=1
else: print("WARN: loadAll not found - trying alternate")

# 3. Add Locations sub-tab in Master Setup
old = '<button class="sub-tab" onclick="switchMaster(\'links\')">Role Assignments</button>'
new = old + '\n\t\t\t<button class="sub-tab" onclick="switchMaster(\'locations\')">&#128205; Locations</button>'
if old in html: html = html.replace(old, new); changes+=1
else: print("WARN: master links tab not found")

# 4. Add locations case to renderMaster
old = "\telse renderLinks()\n\t}"
new = "\telse if(S.masterSub==='locations') renderLocations()\n\telse renderLinks()\n\t}"
if old in html: html = html.replace(old, new); changes+=1
else: print("WARN: renderMaster else not found")

# 5. Add By Location report sub-tab
old = '<button class="sub-tab" onclick="switchReport(\'mpcp\')">&#127919; MP / CP Drill-down</button>'
new = old + '\n\t\t\t<button class="sub-tab" onclick="switchReport(\'location\')">&#128205; By Location</button>'
if old in html: html = html.replace(old, new); changes+=1
else:
    old2 = "MP / CP Drill-down</button>"
    if old2 in html:
        html = html.replace(old2, old2 + '\n\t\t\t<button class="sub-tab" onclick="switchReport(\'location\')">&#128205; By Location</button>')
        changes+=1
    else: print("WARN: mpcp report tab not found")

# 6. Add location case to renderReport
old = "\tif(S.reportSub==='overview') renderOverview()"
new = "\tif(S.reportSub==='location'){ renderLocationReport(); return }\n\tif(S.reportSub==='overview') renderOverview()"
if old in html: html = html.replace(old, new); changes+=1
else: print("WARN: renderReport overview case not found")

# 7. Inject new JS functions before </script>
new_js = """
// ── LOCATIONS ─────────────────────────────────────────────────────────────────
const LOC_COLORS = {Office:'#1d4ed8',Border:'#b45309',Warehouse:'#047857',Depot:'#6d28d9',Branch:'#0891b2'}

function renderLocations() {
    let html = '<div class="section-head"><div><h2>Workstation Locations</h2><p>'+S.locations.length+' locations &middot; staff can belong to multiple workstations</p></div>'
    html += '<button class="btn btn-primary btn-sm" onclick="openLocForm()">+ New Location</button></div><div class="grid-3">'
    S.locations.forEach(loc => {
        const emps = (loc.emp_ids||[]).map(getEmp).filter(Boolean)
        const color = LOC_COLORS[loc.type]||'#475569'
        html += '<div class="card" style="border-top:3px solid '+color+';padding:16px">'
        html += '<div class="flex justify-between items-start mb-8">'
        html += '<span class="ref-badge" style="font-size:12px;font-weight:900">'+esc(loc.code)+'</span>'
        html += '<span class="badge" style="background:'+color+'20;color:'+color+';font-weight:700">'+esc(loc.type)+'</span></div>'
        html += '<p class="font-black" style="font-size:14px">'+esc(loc.name)+'</p>'
        if(loc.address) html += '<p class="text-xs text-muted mt-4">&#128205; '+esc(loc.address)+'</p>'
        html += '<div class="mt-12 flex gap-4" style="flex-wrap:wrap">'
        if(emps.length) emps.forEach(e=>{ html += '<span class="owner-chip" style="background:'+dc(e.dept)+'" onclick="openProfile(\''+e.id+'\',event)">'+e.name.split(' ')[0]+'</span>' })
        else html += '<span class="text-xs text-muted italic">No staff assigned</span>'
        html += '</div><p class="text-xxs text-muted mt-8">'+emps.length+' staff assigned</p>'
        html += '<div class="flex gap-6 mt-12" style="border-top:1px solid var(--border);padding-top:10px">'
        html += '<button class="btn btn-ghost btn-sm flex-1" onclick="openLocForm(\''+loc.id+'\')">Edit</button>'
        html += '<button class="btn btn-sm flex-1" style="background:#fee2e2;color:#b91c1c" onclick="delLoc(\''+loc.id+'\')">Delete</button>'
        html += '</div></div>'
    })
    html += '</div>'
    q('#master-content').innerHTML = html
}

function openLocForm(id) {
    const loc = id ? S.locations.find(function(l){return l.id===id}) : null
    const TYPES = ['Office','Border','Warehouse','Depot','Branch']
    const typeOpts = TYPES.map(function(t){return '<option'+(loc&&loc.type===t?' selected':'')+'>'+t+'</option>'}).join('')
    const body = '<div class="form-grid-2">'
        + '<div class="form-group"><label class="form-label">Location Code</label>'
        + '<input class="form-input" id="lf-code" value="'+(loc?esc(loc.code):'')+'" placeholder="e.g. BORDER, WH-KTM"></div>'
        + '<div class="form-group"><label class="form-label">Type</label>'
        + '<select class="form-select" id="lf-type">'+typeOpts+'</select></div></div>'
        + '<div class="form-group"><label class="form-label">Location Name</label>'
        + '<input class="form-input" id="lf-name" value="'+(loc?esc(loc.name):'')+'"></div>'
        + '<div class="form-group"><label class="form-label">Address / Description</label>'
        + '<input class="form-input" id="lf-addr" value="'+(loc?esc(loc.address||''):'')+'"></div>'
        + '<div class="form-group"><label class="form-label">Staff at this Location</label>'
        + buildOwnerPicker('lf-emps', loc?loc.emp_ids||[]:[])+' </div>'
    openModal(loc?'Edit Location':'Add Workstation Location', body,
    [{label: loc?'Save Changes':'Create Location', cls:'btn-primary', fn: async function(){
        const d = {code:q('#lf-code').value.trim(), name:q('#lf-name').value.trim(),
                   type:q('#lf-type').value, address:q('#lf-addr').value.trim(),
                   emp_ids: getOwnerPicked('lf-emps')}
        if(!d.code||!d.name){toast('Code and name required','error');return}
        if(loc){d.id=loc.id; await api.put('/api/locations/'+loc.id,d)}
        else await api.post('/api/locations',d)
        toast(loc?'Location updated':'Location created','ok'); closeModal(); await loadAll()
    }}], true)
}

async function delLoc(id){
    if(!confirm('Delete this location? Staff assignments will be removed.'))return
    await api.del('/api/locations/'+id); toast('Deleted','ok'); await loadAll()
}

async function renderLocationReport() {
    setSpinner('report-content')
    const data = await api.get('/api/analytics/by_location?fy='+encodeURIComponent(S.currentFY))
    const entries = Object.entries(data)
    let html = '<div class="section-head mb-20"><div>'
    html += '<h2>Performance by Location &mdash; FY '+esc(S.currentFY)+'</h2>'
    html += '<p>Compliance rates aggregated by workstation. Staff may appear in multiple locations.</p>'
    html += '</div></div>'
    html += '<div class="grid-3 mb-20">'
    entries.forEach(function(kv){
        const loc = kv[1]
        html += compCard({ref:kv[0], title:loc.name+' \u00b7 '+loc.type,
            tot:loc.total, comp:loc.compliant, nc:loc.nc,
            pct_c:loc.pct_c, pct_nc:loc.pct_nc,
            color: LOC_COLORS[loc.type]||'#475569'})
    })
    html += '</div>'
    html += '<div class="card mb-20"><div class="card-head"><p>Staff Assignments by Location</p></div><div class="card-body">'
    html += '<div class="tbl-wrap"><table><thead><tr>'
    html += '<th>Location</th><th>Type</th><th>Address</th><th>Staff</th><th>Compliance</th>'
    html += '</tr></thead><tbody>'
    entries.forEach(function(kv){
        const code=kv[0]; const loc=kv[1]
        const color = LOC_COLORS[loc.type]||'#475569'
        const emps = (loc.emp_ids||[]).map(getEmp).filter(Boolean)
        html += '<tr>'
        html += '<td><span class="ref-badge" style="font-weight:900">'+esc(code)+'</span> <span class="font-bold">'+esc(loc.name)+'</span></td>'
        html += '<td><span class="badge" style="background:'+color+'20;color:'+color+'">'+esc(loc.type)+'</span></td>'
        html += '<td class="text-muted text-xs">'+esc(loc.address||'&mdash;')+'</td>'
        html += '<td>'+emps.map(function(e){return '<span class="owner-chip" style="background:'+dc(e.dept)+'" onclick="openProfile(\''+e.id+'\',event)">'+e.name.split(' ')[0]+'</span>'}).join('')+'</td>'
        if(loc.total>0){
            const col = loc.pct_c>=95?'var(--green)':loc.pct_c>=80?'var(--amber)':'var(--red)'
            html += '<td><span class="font-black" style="color:'+col+'">'+loc.pct_c+'%</span> <span class="text-xs text-muted">('+loc.compliant+'/'+loc.total+')</span></td>'
        } else { html += '<td><span class="text-muted text-xs">No data</span></td>' }
        html += '</tr>'
    })
    html += '</tbody></table></div></div></div>'
    html += '<div class="card"><div class="card-head"><p>Location Compliance Chart</p></div>'
    html += '<div class="card-body"><canvas id="loc-chart" height="80"></canvas></div></div>'
    q('#report-content').innerHTML = html
    destroyChart('loc-chart')
    const labels = entries.map(function(kv){return kv[1].name})
    const pcts   = entries.map(function(kv){return kv[1].pct_c})
    const bgs    = entries.map(function(kv){return LOC_COLORS[kv[1].type]||'#475569'})
    charts['loc-chart'] = new Chart(q('#loc-chart'), {
        type:'bar',
        data:{labels:labels, datasets:[{label:'Compliance %', data:pcts, backgroundColor:bgs, borderRadius:8}]},
        options:{responsive:true, plugins:{legend:{display:false}},
            scales:{y:{min:0,max:100,ticks:{callback:function(v){return v+'%'}},grid:{color:'#f1f5f9'}},
                    x:{grid:{display:false}}}}
    })
}
"""
html = html.replace('</script>', new_js + '\n</script>', 1)
changes += 1

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("index.html patched OK")
print("Total changes applied:", changes)
