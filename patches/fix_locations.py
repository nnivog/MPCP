with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# The JS to inject - goes before loadAll() at end of script
NEW_JS = """
// ── LOCATIONS & SECTORS ───────────────────────────────────────────────────────
const LOC_COLORS = {
    Office:    '#1d4ed8',
    Border:    '#b45309',
    Warehouse: '#047857',
    Depot:     '#6d28d9',
    Branch:    '#0891b2'
}
const SECTOR_COLORS = {
    Vehicle:      '#1d4ed8',
    Registration: '#6d28d9',
    Warehouse:    '#047857',
    Stock:        '#b45309',
    Ops:          '#475569',
    HOD:          '#0f2540',
    Finance:      '#0e7490',
    HR:           '#be185d'
}

// ── RENDER LOCATIONS TAB ──────────────────────────────────────────────────────
function renderLocations() {
    const TYPES = ['Office','Border','Warehouse','Depot','Branch']

    // Group employees by dept = sector
    const sectors = {}
    S.employees.forEach(e => {
        if (!sectors[e.dept]) sectors[e.dept] = []
        sectors[e.dept].push(e)
    })

    let html = `
    <div class="section-head">
        <div><h2>Workstations &amp; Sectors</h2>
        <p>${S.locations.length} locations &middot; ${Object.keys(sectors).length} sectors &middot; ${S.employees.length} staff</p></div>
        <button class="btn btn-primary btn-sm" onclick="openLocForm()">+ New Location</button>
    </div>`

    // ── SECTOR OVERVIEW ──
    html += `<div class="card mb-20">
        <div class="card-head"><p>Sectors / Departments</p></div>
        <div class="card-body">
        <div class="grid-4">`
    Object.entries(sectors).forEach(function(kv) {
        const sect = kv[0]; const emps = kv[1]
        const col = SECTOR_COLORS[sect] || '#475569'
        const myMPs = S.mps.filter(m => emps.some(e => (m.owner_ids||[]).includes(e.id))).length
        const myCPs = S.cps.filter(c => emps.some(e => (c.owner_ids||[]).includes(e.id))).length
        const fyPerf = S.perf.filter(p => p.fy === S.currentFY && emps.some(e => e.emp_code === p.emp_code))
        const tot  = fyPerf.reduce((s,r) => s + (r.total||1), 0)
        const comp = fyPerf.reduce((s,r) => s + (r.compliant||(r.status==='C'?1:0)), 0)
        const pct  = tot ? (comp/tot*100).toFixed(1) : null
        html += `<div class="stat-box" style="border-left:4px solid ${col};text-align:left;padding:14px 16px">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                <span class="dept-badge" style="background:${col}">${sect}</span>
            </div>
            <div style="display:flex;gap:12px;flex-wrap:wrap">
                <span class="text-xs text-muted"><strong>${emps.length}</strong> staff</span>
                <span class="text-xs text-muted"><strong>${myMPs}</strong> MPs</span>
                <span class="text-xs text-muted"><strong>${myCPs}</strong> CPs</span>
            </div>
            ${pct !== null
                ? `<div style="margin-top:8px;font-size:18px;font-weight:900;font-family:'Syne',sans-serif;color:${pct>=95?'var(--green)':pct>=80?'var(--amber)':'var(--red)'}">${pct}%</div>
                   <div class="text-xxs text-muted">FY ${S.currentFY} compliance</div>`
                : '<div class="text-xs text-muted italic mt-8">No performance data</div>'}
            <div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:4px">
                ${emps.map(e => `<span class="owner-chip" style="background:${col}" onclick="openProfile('${e.id}',event)">${e.name.split(' ')[0]}</span>`).join('')}
            </div>
        </div>`
    })
    html += '</div></div></div>'

    // ── LOCATION CARDS ──
    html += `<div class="section-head mt-20">
        <div><h2>Workstation Locations</h2><p>Physical sites where staff operate</p></div>
    </div>`

    if (S.locations.length === 0) {
        html += `<div class="info-box"><p>No locations configured yet. Click <strong>+ New Location</strong> above to add your first workstation.</p></div>`
    } else {
        html += '<div class="grid-3">'
        S.locations.forEach(function(loc) {
            const emps = (loc.emp_ids||[]).map(getEmp).filter(Boolean)
            const col  = LOC_COLORS[loc.type] || '#475569'
            // sector breakdown for this location
            const sectBreak = {}
            emps.forEach(e => { sectBreak[e.dept] = (sectBreak[e.dept]||0)+1 })
            // FY compliance for staff at this location
            const fyPerf = S.perf.filter(p => p.fy===S.currentFY && emps.some(e=>e.emp_code===p.emp_code))
            const tot  = fyPerf.reduce((s,r)=>s+(r.total||1),0)
            const comp = fyPerf.reduce((s,r)=>s+(r.compliant||(r.status==='C'?1:0)),0)
            const pct  = tot ? (comp/tot*100).toFixed(1) : null

            html += `<div class="card" style="border-top:4px solid ${col}">
                <div class="card-body">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
                        <span class="ref-badge" style="font-size:13px;font-weight:900;background:#0f2540;color:#fff">${esc(loc.code)}</span>
                        <span class="badge" style="background:${col}20;color:${col};font-weight:700">${esc(loc.type)}</span>
                    </div>
                    <p style="font-size:15px;font-weight:900;font-family:'Syne',sans-serif;margin-bottom:4px">${esc(loc.name)}</p>
                    ${loc.address ? `<p class="text-xs text-muted">&#128205; ${esc(loc.address)}</p>` : ''}

                    ${pct !== null ? `
                    <div style="margin:12px 0 8px">
                        <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                            <span class="text-xs text-muted font-bold">FY ${S.currentFY} Compliance</span>
                            <span style="font-weight:900;color:${pct>=95?'var(--green)':pct>=80?'var(--amber)':'var(--red)'}">${pct}%</span>
                        </div>
                        <div class="cc-bar"><span class="cc-bar-c" style="width:${Math.min(pct,100)}%;background:${pct>=95?'var(--green)':pct>=80?'var(--amber)':'var(--red)'}"></span></div>
                        <div class="text-xxs text-muted mt-4">${comp} compliant / ${tot} total</div>
                    </div>` : ''}

                    <div style="margin:12px 0 6px">
                        <p class="text-xxs text-muted font-bold" style="text-transform:uppercase;letter-spacing:.6px;margin-bottom:6px">${emps.length} Staff</p>
                        <div style="display:flex;flex-wrap:wrap;gap:4px">
                            ${emps.map(e => `<span class="owner-chip" style="background:${dc(e.dept)}" onclick="openProfile('${e.id}',event)" title="${e.role}">${e.name.split(' ')[0]}</span>`).join('')}
                            ${emps.length===0 ? '<span class="text-xs text-muted italic">No staff assigned</span>' : ''}
                        </div>
                    </div>

                    ${Object.keys(sectBreak).length > 0 ? `
                    <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:8px">
                        ${Object.entries(sectBreak).map(kv=>`<span class="dept-badge" style="background:${SECTOR_COLORS[kv[0]]||'#475569'};font-size:9px">${kv[0]}: ${kv[1]}</span>`).join('')}
                    </div>` : ''}

                    <div style="display:flex;gap:6px;margin-top:14px;padding-top:12px;border-top:1px solid var(--border)">
                        <button class="btn btn-ghost btn-sm flex-1" onclick="openLocForm('${loc.id}')">Edit</button>
                        <button class="btn btn-sm flex-1" style="background:#fee2e2;color:#b91c1c" onclick="delLoc('${loc.id}')">Delete</button>
                    </div>
                </div>
            </div>`
        })
        html += '</div>'
    }

    q('#master-content').innerHTML = html
}

function openLocForm(id) {
    const loc  = id ? S.locations.find(function(l){return l.id===id}) : null
    const TYPES = ['Office','Border','Warehouse','Depot','Branch']
    const typeOpts = TYPES.map(function(t){
        return '<option'+(loc&&loc.type===t?' selected':'')+'>'+t+'</option>'
    }).join('')
    const body =
        '<div class="form-grid-2">'
        + '<div class="form-group"><label class="form-label">Location Code</label>'
        + '<input class="form-input" id="lf-code" value="'+(loc?esc(loc.code):'')+'" placeholder="e.g. BORDER, WH-KTM, HQ"></div>'
        + '<div class="form-group"><label class="form-label">Type</label>'
        + '<select class="form-select" id="lf-type">'+typeOpts+'</select></div></div>'
        + '<div class="form-group"><label class="form-label">Location / Workstation Name</label>'
        + '<input class="form-input" id="lf-name" value="'+(loc?esc(loc.name):'')+'"></div>'
        + '<div class="form-group"><label class="form-label">Address / Description</label>'
        + '<input class="form-input" id="lf-addr" value="'+(loc?esc(loc.address||''):'')+'" placeholder="City or full address"></div>'
        + '<div class="form-group"><label class="form-label">Assign Staff to this Location</label>'
        + '<p class="text-xs text-muted mb-8">Staff can belong to multiple locations (e.g. border + HQ).</p>'
        + buildOwnerPicker('lf-emps', loc?loc.emp_ids||[]:[])+'</div>'

    openModal(loc?'Edit Location':'Add Workstation Location', body,
    [{label: loc?'Save Changes':'Create Location', cls:'btn-primary', fn: async function(){
        const d = {
            code:    q('#lf-code').value.trim(),
            name:    q('#lf-name').value.trim(),
            type:    q('#lf-type').value,
            address: q('#lf-addr').value.trim(),
            emp_ids: getOwnerPicked('lf-emps')
        }
        if (!d.code||!d.name) { toast('Code and name required','error'); return }
        if (loc) { d.id=loc.id; await api.put('/api/locations/'+loc.id, d) }
        else await api.post('/api/locations', d)
        toast(loc?'Location updated':'Location created','ok')
        closeModal(); await loadAll()
    }}], true)
}

async function delLoc(id) {
    if (!confirm('Delete this location? Staff assignments will be removed.')) return
    await api.del('/api/locations/'+id)
    toast('Location deleted','ok')
    await loadAll()
}

// ── LOCATION REPORT ───────────────────────────────────────────────────────────
async function renderLocationReport() {
    setSpinner('report-content')
    const data = await api.get('/api/analytics/by_location?fy='+encodeURIComponent(S.currentFY))
    const entries = Object.entries(data)

    // Also build sector summary from live S.perf
    const fyPerf = perfByFY(S.currentFY)
    const sectors = {}
    S.employees.forEach(function(e) {
        if (!sectors[e.dept]) sectors[e.dept] = { emps:[], tot:0, comp:0, nc:0 }
        sectors[e.dept].emps.push(e)
    })
    fyPerf.forEach(function(r) {
        const emp = getEmpByCode(r.emp_code)
        if (!emp) return
        const s = sectors[emp.dept]
        if (!s) return
        s.tot  += (r.total||1)
        s.comp += (r.compliant||(r.status==='C'?1:0))
        s.nc   += (r.non_compliant||(r.status==='NC'?1:0))
    })

    let html = `<div class="section-head mb-16"><div>
        <h2>Performance by Location &amp; Sector &mdash; FY ${esc(S.currentFY)}</h2>
        <p>Compliance rates broken down by workstation and by department/sector.</p>
    </div></div>`

    // ── SECTOR COMPLIANCE ──
    html += `<div class="card mb-20">
        <div class="card-head"><p>By Sector / Department</p></div>
        <div class="card-body"><div class="grid-4">`
    Object.entries(sectors).forEach(function(kv) {
        const sect=kv[0]; const s=kv[1]
        const col = SECTOR_COLORS[sect]||'#475569'
        const pct = s.tot ? (s.comp/s.tot*100).toFixed(1) : null
        html += `<div class="compliance-card" style="border-left:4px solid ${col}">
            <div class="cc-title">
                <span class="dept-badge" style="background:${col}">${sect}</span>
                <span class="flex-1 text-xs text-muted">${s.emps.length} staff</span>
                <span class="cc-pct" style="color:${pct?( pct>=95?'var(--green)':pct>=80?'var(--amber)':'var(--red)'):'#94a3b8'}">${pct!==null?pct+'%':'—'}</span>
            </div>
            ${pct!==null?`<div class="cc-bar"><span class="cc-bar-c" style="width:${Math.min(pct,100)}%;background:${pct>=95?'var(--green)':pct>=80?'var(--amber)':'var(--red)'}"></span></div>
            <div class="cc-nums">
                <span class="cc-total">Total: <strong>${s.tot}</strong></span>
                <span class="cc-c">&#10003; ${s.comp}</span>
                <span class="cc-nc">&#10007; ${s.nc}</span>
            </div>`:'<p class="text-xs text-muted italic">No data this FY</p>'}
        </div>`
    })
    html += '</div></div></div>'

    // ── LOCATION COMPLIANCE ──
    html += `<div class="card mb-20">
        <div class="card-head"><p>By Workstation Location</p></div>
        <div class="card-body"><div class="grid-3">`
    if (entries.length === 0) {
        html += '<p class="text-sm text-muted italic">No locations configured. Add locations in Master Setup → Locations.</p>'
    } else {
        entries.forEach(function(kv) {
            const code=kv[0]; const loc=kv[1]
            html += compCard({
                ref:   code,
                title: loc.name + ' \u00b7 ' + loc.type,
                tot:   loc.total, comp: loc.compliant, nc: loc.nc,
                pct_c: loc.pct_c, pct_nc: loc.pct_nc,
                color: LOC_COLORS[loc.type]||'#475569'
            })
        })
    }
    html += '</div></div></div>'

    // ── COMBINED TABLE ──
    html += `<div class="card mb-20">
        <div class="card-head"><p>Staff &rarr; Location &rarr; Sector Mapping</p></div>
        <div class="card-body"><div class="tbl-wrap"><table>
        <thead><tr>
            <th>Location</th><th>Type</th><th>Address</th>
            <th>Sectors Present</th><th>Staff</th><th>Compliance</th>
        </tr></thead><tbody>`
    if (entries.length === 0) {
        html += '<tr><td colspan="6" class="text-muted text-xs" style="text-align:center;padding:20px">No locations configured</td></tr>'
    } else {
        entries.forEach(function(kv) {
            const code=kv[0]; const loc=kv[1]
            const col  = LOC_COLORS[loc.type]||'#475569'
            const emps = (loc.emp_ids||[]).map(getEmp).filter(Boolean)
            const sects = [...new Set(emps.map(e=>e.dept))]
            const pct  = loc.pct_c
            html += `<tr>
                <td><span class="ref-badge" style="font-weight:900;background:#0f2540;color:#fff">${esc(code)}</span><br><span class="font-bold text-sm">${esc(loc.name)}</span></td>
                <td><span class="badge" style="background:${col}20;color:${col}">${esc(loc.type)}</span></td>
                <td class="text-xs text-muted">${esc(loc.address||'—')}</td>
                <td>${sects.map(s=>`<span class="dept-badge" style="background:${SECTOR_COLORS[s]||'#475569'};font-size:9px;margin:2px">${s}</span>`).join('')}</td>
                <td>${emps.map(e=>`<span class="owner-chip" style="background:${dc(e.dept)}" onclick="openProfile('${e.id}',event)">${e.name.split(' ')[0]}</span>`).join('')||'<span class="text-xs text-muted">—</span>'}</td>
                <td>${loc.total>0
                    ?`<span style="font-weight:900;color:${pct>=95?'var(--green)':pct>=80?'var(--amber)':'var(--red)'}">${pct}%</span> <span class="text-xs text-muted">(${loc.compliant}/${loc.total})</span>`
                    :'<span class="text-xs text-muted">No data</span>'}</td>
            </tr>`
        })
    }
    html += '</tbody></table></div></div></div>'

    // ── CHARTS ──
    html += `<div class="grid-2">
        <div class="card"><div class="card-head"><p>Location Compliance Chart</p></div>
        <div class="card-body"><canvas id="loc-chart" height="120"></canvas></div></div>
        <div class="card"><div class="card-head"><p>Sector Compliance Chart</p></div>
        <div class="card-body"><canvas id="sec-chart" height="120"></canvas></div></div>
    </div>`

    q('#report-content').innerHTML = html
    destroyChart('loc-chart'); destroyChart('sec-chart')

    // Location bar chart
    if (entries.length) {
        charts['loc-chart'] = new Chart(q('#loc-chart'), {
            type:'bar',
            data:{
                labels: entries.map(function(kv){return kv[1].name}),
                datasets:[{
                    label:'Compliance %',
                    data:  entries.map(function(kv){return kv[1].pct_c}),
                    backgroundColor: entries.map(function(kv){return LOC_COLORS[kv[1].type]||'#475569'}),
                    borderRadius:8
                }]
            },
            options:{responsive:true,plugins:{legend:{display:false}},
                scales:{y:{min:0,max:100,ticks:{callback:function(v){return v+'%'}},grid:{color:'#f1f5f9'}},x:{grid:{display:false}}}}
        })
    }

    // Sector bar chart
    const sectEntries = Object.entries(sectors).filter(function(kv){return kv[1].tot>0})
    if (sectEntries.length) {
        charts['sec-chart'] = new Chart(q('#sec-chart'), {
            type:'bar',
            data:{
                labels: sectEntries.map(function(kv){return kv[0]}),
                datasets:[{
                    label:'Compliance %',
                    data:  sectEntries.map(function(kv){const s=kv[1];return s.tot?(s.comp/s.tot*100).toFixed(1):0}),
                    backgroundColor: sectEntries.map(function(kv){return SECTOR_COLORS[kv[0]]||'#475569'}),
                    borderRadius:8
                }]
            },
            options:{responsive:true,plugins:{legend:{display:false}},
                scales:{y:{min:0,max:100,ticks:{callback:function(v){return v+'%'}},grid:{color:'#f1f5f9'}},x:{grid:{display:false}}}}
        })
    }
}
"""

# Inject before the INIT comment (safe anchor that won't match twice)
ANCHOR = "// ── INIT ─────────────────────────────────────────────────────────────────────"
if ANCHOR in html:
    html = html.replace(ANCHOR, NEW_JS + "\n" + ANCHOR)
    print("JS injected OK before INIT block")
else:
    # Fallback: inject before loadAll()
    if "\nloadAll()\n" in html:
        html = html.replace("\nloadAll()\n", NEW_JS + "\nloadAll()\n")
        print("JS injected OK before loadAll()")
    else:
        print("FAIL: could not find injection point")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

# Verify
checks = ["LOC_COLORS","SECTOR_COLORS","function renderLocations","function openLocForm",
          "function delLoc","async function renderLocationReport"]
print("\nVerification:")
for c in checks:
    print(("  OK  " if c in html else "  MISSING  ") + c)
