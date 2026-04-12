# ═══════════════════════════════════════════════════════════════════════════════
# CASCADE BUILDER — patches app.py and index.html
# Adds: parent_cp_id on MPs, level on roles, cascade API, Cascade Builder UI
# ═══════════════════════════════════════════════════════════════════════════════

# ── APP.PY ────────────────────────────────────────────────────────────────────
with open('app.py', 'r', encoding='utf-8') as f:
    src = f.read()

# 1. Add parent_cp_id and level to mps table
old = """CREATE TABLE IF NOT EXISTS mps(
  id TEXT PRIMARY KEY, ref TEXT NOT NULL, title TEXT NOT NULL,
  target TEXT DEFAULT '', freq TEXT DEFAULT 'Monthly',
  kpi_c INTEGER DEFAULT 0, kpi_nc INTEGER DEFAULT 0, kpi_total INTEGER DEFAULT 0);"""
new = """CREATE TABLE IF NOT EXISTS mps(
  id TEXT PRIMARY KEY, ref TEXT NOT NULL, title TEXT NOT NULL,
  target TEXT DEFAULT '', freq TEXT DEFAULT 'Monthly',
  kpi_c INTEGER DEFAULT 0, kpi_nc INTEGER DEFAULT 0, kpi_total INTEGER DEFAULT 0,
  parent_cp_id TEXT DEFAULT '', emp_level INTEGER DEFAULT 1);"""
if old in src: src=src.replace(old,new); print("patch 1 OK: mps table")
else: print("WARN 1: mps table not found")

# 2. Add level to roles table
old = """CREATE TABLE IF NOT EXISTS roles(
  id TEXT PRIMARY KEY, code TEXT NOT NULL, name TEXT NOT NULL,
  description TEXT DEFAULT '', color TEXT DEFAULT '#1d4ed8');"""
new = """CREATE TABLE IF NOT EXISTS roles(
  id TEXT PRIMARY KEY, code TEXT NOT NULL, name TEXT NOT NULL,
  description TEXT DEFAULT '', color TEXT DEFAULT '#1d4ed8',
  emp_level INTEGER DEFAULT 1, parent_role_id TEXT DEFAULT '');"""
if old in src: src=src.replace(old,new); print("patch 2 OK: roles table")
else: print("WARN 2: roles table not found")

# 3. Add cascade table
old = "CREATE TABLE IF NOT EXISTS emp_roles(emp_id TEXT, role_id TEXT, PRIMARY KEY(emp_id,role_id));"
new = """CREATE TABLE IF NOT EXISTS emp_roles(emp_id TEXT, role_id TEXT, PRIMARY KEY(emp_id,role_id));
CREATE TABLE IF NOT EXISTS cascade_links(
  id TEXT PRIMARY KEY,
  parent_emp_id TEXT NOT NULL, parent_cp_id TEXT NOT NULL,
  child_emp_id  TEXT NOT NULL, child_mp_id   TEXT NOT NULL);"""
if old in src: src=src.replace(old,new); print("patch 3 OK: cascade_links table")
else: print("WARN 3: emp_roles not found")

# 4. Enrich mps to include parent_cp_id and emp_level
old = "def enrich_mp(m,db):\n    r=dict(m); r['owner_ids']=[x['emp_id'] for x in db.execute(\"SELECT emp_id FROM mp_owners WHERE mp_id=?\",(r['id'],))]\n    r['pct']=round(r['kpi_c']/r['kpi_total']*100,1) if r['kpi_total'] else None; return r"
new = "def enrich_mp(m,db):\n    r=dict(m); r['owner_ids']=[x['emp_id'] for x in db.execute(\"SELECT emp_id FROM mp_owners WHERE mp_id=?\",(r['id'],))]\n    r['pct']=round(r['kpi_c']/r['kpi_total']*100,1) if r['kpi_total'] else None\n    r['parent_cp_id']=r.get('parent_cp_id','')\n    r['emp_level']=r.get('emp_level',1)\n    r['cascade_children']=[dict(x) for x in db.execute(\"SELECT cl.*,e.name as child_name,e.emp_code as child_code FROM cascade_links cl LEFT JOIN employees e ON cl.child_emp_id=e.id WHERE cl.parent_cp_id IN (SELECT id FROM cps WHERE mp_id=?)\", (r['id'],))]\n    return r"
if old in src: src=src.replace(old,new); print("patch 4 OK: enrich_mp")
else: print("WARN 4: enrich_mp not found")

# 5. Update mps POST to include parent_cp_id and emp_level
old = "    db.execute(\"INSERT OR REPLACE INTO mps VALUES(?,?,?,?,?,?,?,?)\",\n        (mid,d['ref'],d['title'],d.get('target',''),d.get('freq','Monthly'),d.get('kpi_c',0),d.get('kpi_nc',0),d.get('kpi_total',0)))"
new = "    db.execute(\"INSERT OR REPLACE INTO mps VALUES(?,?,?,?,?,?,?,?,?,?)\",\n        (mid,d['ref'],d['title'],d.get('target',''),d.get('freq','Monthly'),d.get('kpi_c',0),d.get('kpi_nc',0),d.get('kpi_total',0),d.get('parent_cp_id',''),d.get('emp_level',1)))"
if old in src: src=src.replace(old,new); print("patch 5 OK: mps POST insert")
else: print("WARN 5: mps POST insert not found")

# 6. Update mps PUT to include parent_cp_id and emp_level
old = "    db.execute(\"UPDATE mps SET ref=?,title=?,target=?,freq=?,kpi_c=?,kpi_nc=?,kpi_total=? WHERE id=?\",\n        (d['ref'],d['title'],d.get('target',''),d.get('freq','Monthly'),d.get('kpi_c',0),d.get('kpi_nc',0),d.get('kpi_total',0),mid))"
new = "    db.execute(\"UPDATE mps SET ref=?,title=?,target=?,freq=?,kpi_c=?,kpi_nc=?,kpi_total=?,parent_cp_id=?,emp_level=? WHERE id=?\",\n        (d['ref'],d['title'],d.get('target',''),d.get('freq','Monthly'),d.get('kpi_c',0),d.get('kpi_nc',0),d.get('kpi_total',0),d.get('parent_cp_id',''),d.get('emp_level',1),mid))"
if old in src: src=src.replace(old,new); print("patch 6 OK: mps PUT update")
else: print("WARN 6: mps PUT update not found")

# 7. Update roles POST to include emp_level and parent_role_id
old = "    db.execute(\"INSERT OR REPLACE INTO roles VALUES(?,?,?,?,?)\",(rid,d['code'],d['name'],d.get('description',''),d.get('color','#1d4ed8')))"
new = "    db.execute(\"INSERT OR REPLACE INTO roles VALUES(?,?,?,?,?,?,?)\",(rid,d['code'],d['name'],d.get('description',''),d.get('color','#1d4ed8'),d.get('emp_level',1),d.get('parent_role_id','')))"
if old in src: src=src.replace(old,new); print("patch 7 OK: roles POST insert")
else: print("WARN 7: roles POST insert not found")

# 8. Update roles PUT
old = "    db.execute(\"UPDATE roles SET code=?,name=?,description=?,color=? WHERE id=?\",(d['code'],d['name'],d.get('description',''),d.get('color','#1d4ed8'),rid))"
new = "    db.execute(\"UPDATE roles SET code=?,name=?,description=?,color=?,emp_level=?,parent_role_id=? WHERE id=?\",(d['code'],d['name'],d.get('description',''),d.get('color','#1d4ed8'),d.get('emp_level',1),d.get('parent_role_id',''),rid))"
if old in src: src=src.replace(old,new); print("patch 8 OK: roles PUT update")
else: print("WARN 8: roles PUT update not found")

# 9. Inject cascade API routes before index route
CASCADE_API = '''
# ── CASCADE ────────────────────────────────────────────────────────────────────
@app.route('/api/cascade', methods=['GET','POST'])
def cascade_api():
    db = get_db()
    if request.method == 'GET':
        rows = db.execute("""
            SELECT cl.*,
                   pe.name as parent_name, pe.emp_code as parent_code,
                   ce.name as child_name,  ce.emp_code as child_code,
                   cp.ref as cp_ref, cp.title as cp_title,
                   mp.ref as mp_ref, mp.title as mp_title
            FROM cascade_links cl
            LEFT JOIN employees pe ON cl.parent_emp_id = pe.id
            LEFT JOIN employees ce ON cl.child_emp_id  = ce.id
            LEFT JOIN cps cp ON cl.parent_cp_id = cp.id
            LEFT JOIN mps mp ON cl.child_mp_id  = mp.id
            ORDER BY pe.level, pe.name
        """).fetchall()
        return jsonify([dict(r) for r in rows])
    d = request.json
    lid = d.get('id') or uid()
    db.execute("INSERT OR REPLACE INTO cascade_links VALUES(?,?,?,?,?)",
               (lid, d['parent_emp_id'], d['parent_cp_id'],
                d['child_emp_id'],  d['child_mp_id']))
    # Also update the child MP's parent_cp_id field
    db.execute("UPDATE mps SET parent_cp_id=? WHERE id=?",
               (d['parent_cp_id'], d['child_mp_id']))
    db.commit()
    return jsonify({'id': lid})

@app.route('/api/cascade/<lid>', methods=['DELETE'])
def cascade_delete(lid):
    db = get_db()
    # Clear parent_cp_id on the child MP
    row = db.execute("SELECT child_mp_id FROM cascade_links WHERE id=?", (lid,)).fetchone()
    if row:
        db.execute("UPDATE mps SET parent_cp_id='' WHERE id=?", (row['child_mp_id'],))
    db.execute("DELETE FROM cascade_links WHERE id=?", (lid,))
    db.commit()
    return jsonify({'ok': True})

@app.route('/api/cascade/tree')
def cascade_tree():
    """Returns the full cascade tree from any employee downward"""
    db = get_db()
    emp_id = request.args.get('emp_id','')
    def build_node(eid, depth=0):
        if depth > 6: return []   # safety limit
        emp = db.execute("SELECT * FROM employees WHERE id=?", (eid,)).fetchone()
        if not emp: return []
        emp = dict(emp)
        # Get this employee's role
        roles = [dict(r) for r in db.execute(
            "SELECT r.* FROM roles r JOIN emp_roles er ON r.id=er.role_id WHERE er.emp_id=?", (eid,))]
        # Get MPs owned by this employee
        mps = [dict(m) for m in db.execute(
            "SELECT m.* FROM mps m JOIN mp_owners mo ON m.id=mo.mp_id WHERE mo.emp_id=?", (eid,))]
        for mp in mps:
            # Get CPs under this MP
            mp['cps'] = [dict(c) for c in db.execute(
                "SELECT c.* FROM cps c WHERE c.mp_id=?", (mp['id'],))]
            for cp in mp['cps']:
                cp['owners'] = [dict(e) for e in db.execute(
                    "SELECT e.* FROM employees e JOIN cp_owners co ON e.id=co.emp_id WHERE co.cp_id=?",
                    (cp['id'],))]
                # Find cascade children — sub-employees whose MP derives from this CP
                links = db.execute(
                    "SELECT * FROM cascade_links WHERE parent_cp_id=?", (cp['id'],)).fetchall()
                cp['cascade_children'] = []
                for lnk in links:
                    child_nodes = build_node(lnk['child_emp_id'], depth+1)
                    cp['cascade_children'].extend(child_nodes)
        emp['roles'] = roles
        emp['mps']   = mps
        return [emp]

    if emp_id:
        tree = build_node(emp_id)
    else:
        # Start from top-level employees (no manager)
        roots = db.execute(
            "SELECT id FROM employees WHERE manager_id IS NULL OR manager_id=''").fetchall()
        tree = []
        for r in roots:
            tree.extend(build_node(r['id']))
    return jsonify(tree)

'''
old = "@app.route('/')\ndef index():"
if old in src: src=src.replace(old, CASCADE_API+old); print("patch 9 OK: cascade API routes")
else: print("WARN 9: index route not found")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(src)
print("\napp.py done.")

# ── INDEX.HTML ────────────────────────────────────────────────────────────────
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add cascade to state S and loadAll
old = "  employees:[], mps:[], cps:[], roles:[], perf:[], cache:[],"
new = "  employees:[], mps:[], cps:[], roles:[], perf:[], cache:[], cascade:[],"
if old in html: html=html.replace(old,new); print("patch A OK: state S")
else: print("WARN A: state S not found")

old = "    api.get('/api/locations')\n  ])\n  S.employees=e; S.mps=m; S.cps=c; S.roles=r; S.perf=p; S.cache=ca; S.locations=locs"
new = "    api.get('/api/locations'),\n    api.get('/api/cascade')\n  ])\n  S.employees=e; S.mps=m; S.cps=c; S.roles=r; S.perf=p; S.cache=ca; S.locations=locs; S.cascade=casc"
if old in html: html=html.replace(old,new); print("patch B OK: loadAll")
else: print("WARN B: loadAll not found")

old = "  const [e,m,c,r,p,ca,locs] = await Promise.all(["
new = "  const [e,m,c,r,p,ca,locs,casc] = await Promise.all(["
if old in html: html=html.replace(old,new); print("patch C OK: destructure")
else: print("WARN C: destructure not found")

# 2. Add Cascade Builder nav tab
old = '<button class="nav-tab" onclick="switchTab(\'reports\')">📈 Reports</button>'
new = old + '\n      <button class="nav-tab" onclick="switchTab(\'cascade\')">🔗 Cascade</button>'
if old in html: html=html.replace(old,new); print("patch D OK: cascade nav tab")
else: print("WARN D: nav tab not found")

# 3. Add cascade tab panel after reports panel
old = '</div>\n\n<div class="modal-overlay hidden"'
new = '''</div>

<div id="tab-cascade" class="tab-panel">
  <div class="sub-tabs" id="cascade-tabs">
    <button class="sub-tab active" onclick="switchCascade('builder')">🔗 Cascade Builder</button>
    <button class="sub-tab" onclick="switchCascade('tree')">🌳 Full Tree View</button>
  </div>
  <div id="cascade-content"><div class="spinner"></div></div>
</div>

<div class="modal-overlay hidden"'''
if old in html: html=html.replace(old,new); print("patch E OK: cascade panel")
else: print("WARN E: tab panel anchor not found")

# 4. Add cascade to renderCurrent
old = "  else if(S.currentTab==='reports') renderReport()"
new = "  else if(S.currentTab==='reports') renderReport()\n  else if(S.currentTab==='cascade') renderCascadeTab()"
if old in html: html=html.replace(old,new); print("patch F OK: renderCurrent")
else: print("WARN F: renderCurrent not found")

# 5. Add cascade tab CSS
old = ".hidden{display:none!important}"
new = """.hidden{display:none!important}
.cascade-node{border-left:3px solid var(--border);padding-left:16px;margin-left:8px}
.cascade-role-box{background:linear-gradient(135deg,#0a1628,#0f2540);color:#fff;border-radius:12px;padding:12px 16px;margin-bottom:10px}
.cascade-mp-box{background:#f0f9ff;border:1.5px solid #bae6fd;border-radius:10px;padding:10px 14px;margin-bottom:8px}
.cascade-cp-row{display:flex;align-items:center;gap:8px;padding:8px 12px;border:1px solid var(--border);border-radius:8px;margin-bottom:6px;background:#fff;cursor:pointer;transition:.15s}
.cascade-cp-row:hover{border-color:#60a5fa;background:#f0f9ff}
.cascade-cp-row.linked{border-color:#16a34a;background:#f0fdf4}
.cascade-arrow{font-size:20px;color:#94a3b8;text-align:center;margin:4px 0}
.level-badge{display:inline-block;font-size:9px;font-weight:900;padding:2px 7px;border-radius:20px;font-family:'Syne',sans-serif;letter-spacing:.4px;text-transform:uppercase}
.level-1{background:#0f2540;color:#fff}
.level-2{background:#1d4ed8;color:#fff}
.level-3{background:#6d28d9;color:#fff}"""
if old in html: html=html.replace(old,new); print("patch G OK: cascade CSS")
else: print("WARN G: CSS anchor not found")

# 6. Inject all cascade JS before INIT
CASCADE_JS = """
// ── CASCADE BUILDER ───────────────────────────────────────────────────────────
let cascadeSub = 'builder'
function switchCascade(s) {
    cascadeSub = s
    qq('#cascade-tabs .sub-tab').forEach(t=>t.classList.remove('active'))
    event.target.classList.add('active')
    renderCascadeTab()
}
function renderCascadeTab() {
    if (cascadeSub==='tree') renderCascadeTree()
    else renderCascadeBuilder()
}

// ── BUILDER VIEW ──────────────────────────────────────────────────────────────
function renderCascadeBuilder() {
    const levels = [1,2,3]
    let html = `
    <div class="info-box mb-16">
      <p><strong>How the cascade works:</strong> Your <strong>CP</strong> becomes your subordinate's <strong>MP</strong>.
      Select a parent employee, pick one of their CPs, then select which subordinate's MP it maps to.
      The system will draw the full chain automatically.</p>
    </div>
    <div class="section-head">
      <div><h2>Cascade Builder</h2>
      <p>Link a superior's CP to a subordinate's MP to build the performance cascade chain</p></div>
      <button class="btn btn-primary btn-sm" onclick="openCascadeForm()">+ New Cascade Link</button>
    </div>`

    // Show existing links grouped by parent
    const byParent = {}
    S.cascade.forEach(function(lnk) {
        if (!byParent[lnk.parent_emp_id]) byParent[lnk.parent_emp_id] = []
        byParent[lnk.parent_emp_id].push(lnk)
    })

    if (S.cascade.length === 0) {
        html += `<div class="card"><div class="card-body">
            <p class="text-sm text-muted italic" style="text-align:center;padding:20px">
            No cascade links yet. Click <strong>+ New Cascade Link</strong> to start mapping the hierarchy.</p>
        </div></div>`
    } else {
        html += '<div style="display:flex;flex-direction:column;gap:12px">'
        Object.entries(byParent).forEach(function(kv) {
            const parentId = kv[0]; const links = kv[1]
            const parent = getEmp(parentId)
            if (!parent) return
            const col = dc(parent.dept)
            html += `<div class="card">
              <div class="card-head" style="background:${col}10;border-bottom-color:${col}40">
                <div style="display:flex;align-items:center;gap:10px">
                  <div class="avatar avatar-sm" style="background:${col}">${av(parent.name)}</div>
                  <div>
                    <p style="font-weight:900;font-family:'Syne',sans-serif">${esc(parent.name)}</p>
                    <p class="text-xs text-muted">${esc(parent.role)} &middot; ${esc(parent.emp_code||'')}</p>
                  </div>
                  <span class="level-badge level-${parent.level}">Level ${parent.level}</span>
                </div>
              </div>
              <div class="card-body">`

            links.forEach(function(lnk) {
                const childEmp = getEmp(lnk.child_emp_id)
                const childCol = childEmp ? dc(childEmp.dept) : '#475569'
                html += `<div style="display:flex;align-items:flex-start;gap:0;margin-bottom:10px">
                  <div style="flex:1">
                    <div class="cascade-cp-row linked" style="cursor:default">
                      <span class="ref-badge ref-badge-blue">${esc(lnk.cp_ref||'CP')}</span>
                      <span class="text-sm font-bold flex-1">${esc(lnk.cp_title||'')}</span>
                      <span class="badge badge-c text-xxs">CP</span>
                    </div>
                    <div class="cascade-arrow">&#8595; becomes MP for &#8595;</div>
                    <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:#f0fdf4;border:1.5px solid #86efac;border-radius:8px">
                      ${childEmp?`<div class="avatar avatar-sm" style="background:${childCol}">${av(childEmp.name)}</div>
                      <div>
                        <p class="text-xs font-bold">${esc(childEmp.name)}</p>
                        <p class="text-xxs text-muted">${esc(childEmp.emp_code||'')} &middot; ${esc(childEmp.role||'')}</p>
                      </div>`:'<span class="text-xs text-muted">Unknown employee</span>'}
                      <div style="flex:1">
                        <span class="ref-badge">${esc(lnk.mp_ref||'MP')}</span>
                        <span class="text-xs font-bold ml-4">${esc(lnk.mp_title||'')}</span>
                      </div>
                      <span class="badge" style="background:#dcfce7;color:#15803d">MP</span>
                    </div>
                  </div>
                  <button class="btn-icon ml-8" style="color:var(--red);margin-left:8px;margin-top:4px" onclick="delCascadeLink('${lnk.id}')" title="Remove link">&#128465;</button>
                </div>`
            })

            html += '</div></div>'
        })
        html += '</div>'
    }
    q('#cascade-content').innerHTML = html
}

function openCascadeForm() {
    // Step 1: pick parent employee
    const empOpts = S.employees.map(function(e) {
        return `<option value="${e.id}">${esc(e.name)} (${esc(e.emp_code||'')}) — L${e.level} ${esc(e.dept)}</option>`
    }).join('')

    const body = `
    <div class="info-box mb-12">
      <p>Select the <strong>superior</strong> employee, then pick which of their <strong>CPs</strong> cascades down.
      Then select the <strong>subordinate</strong> and which of their <strong>MPs</strong> it maps to.</p>
    </div>
    <div class="form-group">
      <label class="form-label">&#8593; Superior Employee (CP owner)</label>
      <select class="form-select" id="cl-parent" onchange="refreshCascadeCP()">
        <option value="">— Select superior —</option>${empOpts}
      </select>
    </div>
    <div class="form-group" id="cl-cp-group" style="display:none">
      <label class="form-label">Their CP (this will cascade down)</label>
      <select class="form-select" id="cl-cp">
        <option value="">— Select CP —</option>
      </select>
    </div>
    <div class="form-group" id="cl-child-group" style="display:none">
      <label class="form-label">&#8595; Subordinate Employee (MP owner)</label>
      <select class="form-select" id="cl-child" onchange="refreshCascadeMP()">
        <option value="">— Select subordinate —</option>${empOpts}
      </select>
    </div>
    <div class="form-group" id="cl-mp-group" style="display:none">
      <label class="form-label">Their MP (derived from superior's CP)</label>
      <select class="form-select" id="cl-mp">
        <option value="">— Select MP —</option>
      </select>
    </div>
    <div id="cl-preview" style="display:none;margin-top:12px"></div>`

    openModal('New Cascade Link', body, [{
        label: 'Create Link', cls: 'btn-primary', fn: async function() {
            const pid = q('#cl-parent').value
            const cid = q('#cl-cp').value
            const eid = q('#cl-child').value
            const mid = q('#cl-mp').value
            if (!pid||!cid||!eid||!mid) { toast('All fields required','error'); return }
            await api.post('/api/cascade', {
                parent_emp_id: pid, parent_cp_id: cid,
                child_emp_id:  eid, child_mp_id:  mid
            })
            toast('Cascade link created','ok')
            closeModal(); await loadAll()
        }
    }], true)

    // show child group immediately
    q('#cl-child-group').style.display = ''
}

function refreshCascadeCP() {
    const pid = q('#cl-parent').value
    const sel = q('#cl-cp')
    if (!pid) { q('#cl-cp-group').style.display='none'; return }
    const myCPs = S.cps.filter(function(c) {
        return (c.owner_ids||[]).includes(pid)
    })
    sel.innerHTML = '<option value="">— Select CP —</option>' +
        myCPs.map(function(c) {
            const mp = S.mps.find(function(m){return m.id===c.mp_id})
            return `<option value="${c.id}">[${esc(c.ref)}] ${esc(c.title)} ${mp?'(under '+esc(mp.ref)+')':''}</option>`
        }).join('')
    q('#cl-cp-group').style.display = ''
}

function refreshCascadeMP() {
    const eid = q('#cl-child').value
    const sel = q('#cl-mp')
    if (!eid) { q('#cl-mp-group').style.display='none'; return }
    const myMPs = S.mps.filter(function(m) {
        return (m.owner_ids||[]).includes(eid)
    })
    sel.innerHTML = '<option value="">— Select MP —</option>' +
        myMPs.map(function(m) {
            return `<option value="${m.id}">[${esc(m.ref)}] ${esc(m.title)}</option>`
        }).join('')
    q('#cl-mp-group').style.display = ''
    updateCascadePreview()
}

function updateCascadePreview() {
    const pid = q('#cl-parent')?.value
    const cid = q('#cl-cp')?.value
    const eid = q('#cl-child')?.value
    const mid = q('#cl-mp')?.value
    const prev = q('#cl-preview')
    if (!prev) return
    if (pid&&cid&&eid&&mid) {
        const pe = getEmp(pid); const cp = S.cps.find(function(c){return c.id===cid})
        const ce = getEmp(eid); const mp = S.mps.find(function(m){return m.id===mid})
        prev.style.display=''
        prev.innerHTML = `<div style="background:#f8fafc;border:1.5px solid var(--border);border-radius:10px;padding:12px">
            <p class="text-xxs text-muted font-bold" style="text-transform:uppercase;margin-bottom:8px">Preview</p>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
              <div class="avatar avatar-sm" style="background:${pe?dc(pe.dept):'#475569'}">${pe?av(pe.name):'?'}</div>
              <span class="text-sm font-bold">${pe?esc(pe.name):''}</span>
              <span class="text-xxs text-muted">CP:</span>
              <span class="ref-badge ref-badge-blue">${cp?esc(cp.ref):''}</span>
              <span class="text-xs">${cp?esc(cp.title.slice(0,40)):''}</span>
            </div>
            <div class="cascade-arrow">&#8595; cascades to &#8595;</div>
            <div style="display:flex;align-items:center;gap:8px">
              <div class="avatar avatar-sm" style="background:${ce?dc(ce.dept):'#475569'}">${ce?av(ce.name):'?'}</div>
              <span class="text-sm font-bold">${ce?esc(ce.name):''}</span>
              <span class="text-xxs text-muted">MP:</span>
              <span class="ref-badge">${mp?esc(mp.ref):''}</span>
              <span class="text-xs">${mp?esc(mp.title.slice(0,40)):''}</span>
            </div>
        </div>`
    } else { prev.style.display='none' }
}

async function delCascadeLink(id) {
    if (!confirm('Remove this cascade link?')) return
    await api.del('/api/cascade/'+id)
    toast('Link removed','ok'); await loadAll()
}

// ── TREE VIEW ─────────────────────────────────────────────────────────────────
async function renderCascadeTree() {
    setSpinner('cascade-content')
    // Pick starting employee (default: Level 1)
    const roots = S.employees.filter(function(e){return e.level===1})
    const empOpts = S.employees.map(function(e){
        return `<option value="${e.id}">${esc(e.name)} (L${e.level} ${esc(e.dept)})</option>`
    }).join('')

    let html = `<div class="section-head mb-16">
        <div><h2>Full Cascade Tree</h2><p>Visualise the complete CP&#8594;MP chain from any employee downward</p></div>
        <div style="display:flex;gap:8px;align-items:center">
            <select class="form-select" id="tree-root" style="width:220px">
                <option value="">All top-level</option>${empOpts}
            </select>
            <button class="btn btn-primary btn-sm" onclick="loadTree()">View Tree</button>
        </div>
    </div>
    <div id="tree-output"><div class="info-box"><p>Select an employee above and click <strong>View Tree</strong>, or leave blank to see the full organisation tree.</p></div></div>`

    q('#cascade-content').innerHTML = html
}

async function loadTree() {
    const eid = q('#tree-root').value
    setSpinner('tree-output')
    const url = '/api/cascade/tree' + (eid ? '?emp_id='+eid : '')
    const tree = await api.get(url)
    q('#tree-output').innerHTML = tree.length
        ? '<div style="overflow-x:auto">'+renderTreeNodes(tree, 0)+'</div>'
        : '<p class="text-sm text-muted italic">No data found.</p>'
}

function renderTreeNodes(nodes, depth) {
    if (!nodes||!nodes.length) return ''
    return nodes.map(function(emp) {
        const col = dc(emp.dept||'Ops')
        const lvlBadge = `<span class="level-badge level-${emp.level||1}">Level ${emp.level||1}</span>`
        const roles = (emp.roles||[]).map(function(r){
            return `<span class="badge" style="background:${r.color||'#1d4ed8'};color:#fff;margin:2px">${esc(r.code)}</span>`
        }).join('')

        let mpHtml = ''
        ;(emp.mps||[]).forEach(function(mp) {
            const mpPct = mp.kpi_total ? (mp.kpi_c/mp.kpi_total*100).toFixed(1) : null
            mpHtml += `<div class="cascade-mp-box">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                    <span class="ref-badge" style="background:#0f2540;color:#fff;font-weight:900">${esc(mp.ref)}</span>
                    <span class="font-bold text-sm flex-1">${esc(mp.title)}</span>
                    ${mpPct!==null?`<span class="badge" style="background:${mpPct>=95?'#dcfce7':mpPct>=80?'#fef3c7':'#fee2e2'};color:${mpPct>=95?'#15803d':mpPct>=80?'#92400e':'#b91c1c'}">${mpPct}%</span>`:''}
                    <span class="badge badge-blue">⌖ ${esc(mp.target||'')}</span>
                </div>`

            ;(mp.cps||[]).forEach(function(cp) {
                const hasCascade = cp.cascade_children && cp.cascade_children.length > 0
                mpHtml += `<div class="cascade-cp-row${hasCascade?' linked':''}">
                    <span class="ref-badge ref-badge-blue">${esc(cp.ref)}</span>
                    <span class="text-sm flex-1">${esc(cp.title)}</span>
                    <span class="badge badge-gray">${esc(cp.target||'')}</span>
                    ${hasCascade?'<span class="badge badge-c text-xxs">&#8595; cascades</span>':''}
                </div>`
                if (hasCascade) {
                    mpHtml += `<div class="cascade-arrow">&#8595; CP becomes MP for:</div>`
                    mpHtml += renderTreeNodes(cp.cascade_children, depth+1)
                }
            })
            mpHtml += '</div>'
        })

        return `<div style="margin-bottom:${depth===0?'24':'12'}px">
            <div class="cascade-role-box" style="border-left:4px solid ${col}">
                <div style="display:flex;align-items:center;gap:12px">
                    <div class="avatar avatar-md" style="background:${col}">${av(emp.name)}</div>
                    <div style="flex:1">
                        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                            <span style="font-size:15px;font-weight:900;font-family:'Syne',sans-serif">${esc(emp.name)}</span>
                            ${lvlBadge}
                            <span class="emp-code" style="background:rgba(255,255,255,.15);color:#fff;border-color:transparent">${esc(emp.emp_code||'')}</span>
                        </div>
                        <p style="font-size:11px;color:#93c5fd;margin-top:2px">${esc(emp.role||'')}</p>
                        ${roles?`<div style="margin-top:6px">${roles}</div>`:''}
                    </div>
                </div>
            </div>
            ${mpHtml ? `<div class="cascade-node">${mpHtml}</div>` : ''}
        </div>`
    }).join('')
}
"""

ANCHOR = "// ── INIT ─────────────────────────────────────────────────────────────────────"
if ANCHOR in html:
    html = html.replace(ANCHOR, CASCADE_JS + "\n" + ANCHOR)
    print("patch H OK: cascade JS injected")
else:
    print("WARN H: INIT anchor not found")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("\n=== Verification ===")
checks_html = ["cascade:[]","api.get('/api/cascade')","tab-cascade","renderCascadeTab",
               "renderCascadeBuilder","renderCascadeTree","openCascadeForm",
               "loadTree","cascade-node","level-badge"]
for c in checks_html:
    print(("  OK  " if c in html else "  MISSING  ") + c)

checks_py = ["cascade_links","def cascade_api","def cascade_tree",
             "parent_cp_id","emp_level","parent_role_id"]
with open('app.py') as f: apysrc = f.read()
for c in checks_py:
    print(("  OK  " if c in apysrc else "  MISSING  ") + c)
