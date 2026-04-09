import re

with open('app.py','r',encoding='utf-8') as f:
    src=f.read()

changes=0

# ── 1. Replace BS calendar section ──────────────────────────────────────────
CAL_NEW = (
"# -- BIKRAM SAMWAT CALENDAR (precise dates) -----------------------------------\n"
"BS_MONTHS = ['Baisakh','Jestha','Ashadh','Shrawan','Bhadra','Ashwin',\n"
"             'Kartik','Mangsir','Poush','Magh','Falgun','Chaitra']\n"
"BS_MONTH_DAYS = {\n"
"    2078:[31,31,32,32,31,30,30,29,30,29,30,30],\n"
"    2079:[31,32,31,32,31,30,30,30,29,29,30,30],\n"
"    2080:[31,32,31,32,31,30,30,30,29,30,29,31],\n"
"    2081:[31,31,32,32,31,30,30,30,29,30,30,30],\n"
"    2082:[31,32,31,32,31,30,30,30,29,30,29,31],\n"
"}\n"
"BS_DEFAULT_DAYS=[31,32,31,32,31,30,30,30,29,30,29,31]\n"
"BS_FY_Q={'Shrawan':'Q1','Bhadra':'Q1','Ashwin':'Q1',\n"
"         'Kartik':'Q2','Mangsir':'Q2','Poush':'Q2',\n"
"         'Magh':'Q3','Falgun':'Q3','Chaitra':'Q3',\n"
"         'Baisakh':'Q4','Jestha':'Q4','Ashadh':'Q4'}\n"
"AD_TO_BS={\n"
"    'Jul':'Shrawan','Aug':'Bhadra','Sep':'Ashwin','Oct':'Kartik','Nov':'Mangsir','Dec':'Poush',\n"
"    'Jan':'Magh','Feb':'Falgun','Mar':'Chaitra','Apr':'Baisakh','May':'Jestha','Jun':'Ashadh',\n"
"    'July':'Shrawan','August':'Bhadra','September':'Ashwin','October':'Kartik',\n"
"    'November':'Mangsir','December':'Poush','January':'Magh','February':'Falgun',\n"
"    'March':'Chaitra','April':'Baisakh','June':'Ashadh'}\n"
"\n"
"def bs_days_in_month(year,month_idx):\n"
"    return (BS_MONTH_DAYS.get(year,BS_DEFAULT_DAYS))[month_idx]\n"
"\n"
"def bs_month_idx(mn):\n"
"    try: return BS_MONTHS.index(mn)\n"
"    except: return 0\n"
"\n"
"def norm_month(m):\n"
"    m=str(m or '').strip()\n"
"    if m in BS_MONTHS: return m\n"
"    if m in AD_TO_BS: return AD_TO_BS[m]\n"
"    for bs in BS_MONTHS:\n"
"        if m.lower()==bs.lower(): return bs\n"
"    for ad,bs in AD_TO_BS.items():\n"
"        if m.lower()==ad.lower(): return bs\n"
"    try:\n"
"        idx=int(m)-1\n"
"        if 0<=idx<12: return BS_MONTHS[idx]\n"
"    except: pass\n"
"    return m or 'Shrawan'\n"
"\n"
"def bs_date_str(year,month_name,day):\n"
"    idx=bs_month_idx(month_name)\n"
"    return f'{year}-{idx+1:02d}-{int(day):02d}'\n"
"\n"
"def today_bs():\n"
"    import datetime\n"
"    ad=datetime.date.today()\n"
"    bs_year=ad.year+56\n"
"    ad_to_bs_m=[\n"
"        (1,1,'Poush'),(2,1,'Magh'),(3,1,'Falgun'),\n"
"        (4,1,'Chaitra'),(4,14,'Baisakh'),(5,15,'Jestha'),\n"
"        (6,16,'Ashadh'),(7,1,'Shrawan'),(8,1,'Bhadra'),\n"
"        (9,1,'Ashwin'),(10,1,'Kartik'),(11,1,'Mangsir'),(12,1,'Poush')\n"
"    ]\n"
"    bs_month='Shrawan'\n"
"    for (m,d,bsm) in reversed(ad_to_bs_m):\n"
"        if (ad.month,ad.day)>=(m,d): bs_month=bsm; break\n"
"    return bs_date_str(bs_year,bs_month,ad.day)\n"
"\n"
"def current_bs_fy():\n"
"    import datetime\n"
"    ad=datetime.date.today()\n"
"    bs_year=ad.year+56\n"
"    if ad.month<4 or (ad.month==4 and ad.day<14): bs_year-=1\n"
"    return f'{bs_year}-{str(bs_year+1)[-2:]}'\n"
"\n"
"def bs_q(month): return BS_FY_Q.get(month,'Q1')\n"
)

# Find and replace the old calendar block
import re
cal_pattern = re.compile(
    r'# ──[^\n]*(?:NEPALI|BIKRAM)[^\n]*\n.*?def bs_q\(month\)[^\n]*\n',
    re.DOTALL
)
if cal_pattern.search(src):
    src=cal_pattern.sub(CAL_NEW.rstrip('\n')+'\n', src)
    changes+=1; print("P1 OK: BS calendar replaced")
else:
    # Fallback: match from BS_MONTHS= to end of bs_q function
    cal_fallback = re.compile(
        r'BS_MONTHS\s*=\s*\[.*?\ndef bs_q\(month\)[^\n]*\n',
        re.DOTALL
    )
    if cal_fallback.search(src):
        src=cal_fallback.sub(CAL_NEW.rstrip('\n')+'\n', src)
        changes+=1; print("P1 OK: BS calendar replaced (fallback)")
    else:
        print("WARN P1: calendar pattern not found — skipping, already updated?")

# ── 2. Add bs_date column to perf table ──────────────────────────────────────
old2="  unit TEXT DEFAULT '%', status TEXT DEFAULT 'C', notes TEXT DEFAULT '',\n  location TEXT DEFAULT '', bs_date TEXT DEFAULT '');"
if old2 not in src:
    old2b="  unit TEXT DEFAULT '%', status TEXT DEFAULT 'C', notes TEXT DEFAULT '', location TEXT DEFAULT '');"
    new2="  unit TEXT DEFAULT '%', status TEXT DEFAULT 'C', notes TEXT DEFAULT '',\n  location TEXT DEFAULT '', bs_date TEXT DEFAULT '');"
    if old2b in src: src=src.replace(old2b,new2); changes+=1; print("P2 OK: bs_date column added")
    else: print("WARN P2: perf table not found")
else: print("P2 SKIP: bs_date already present")

# ── 3. Add new API routes ─────────────────────────────────────────────────────
NEW_ROUTES = '''
# -- BS DATE & ORG TREE API ----------------------------------------------------
@app.route('/api/bs_today')
def bs_today():
    return jsonify({'date':today_bs(),'fy':current_bs_fy(),
        'months':BS_MONTHS,'quarter_map':BS_FY_Q,
        'month_days':{str(k):v for k,v in BS_MONTH_DAYS.items()}})

@app.route('/api/bs_calendar/<int:year>')
def bs_calendar(year):
    return jsonify({'year':year,'months':[
        {'name':m,'index':i+1,'days':bs_days_in_month(year,i),'quarter':BS_FY_Q.get(m,'Q1')}
        for i,m in enumerate(BS_MONTHS)]})

@app.route('/api/org/tree')
def org_tree():
    db=get_db()
    fy=request.args.get('fy',''); loc=request.args.get('loc',''); sect=request.args.get('sect','')
    def get_perf(eid,ec):
        q2="SELECT * FROM perf WHERE (emp_id=? OR emp_code=?)"; args=[eid,ec]
        if fy: q2+=" AND fy=?"; args.append(fy)
        if loc: q2+=" AND location=?"; args.append(loc)
        rows=db.execute(q2,args).fetchall()
        tot=sum(r['total'] or 1 for r in rows)
        comp=sum(r['compliant'] or (1 if r['status']=='C' else 0) for r in rows)
        return {'tot':tot,'comp':comp,'nc':tot-comp,
                'pct':round(comp/tot*100,2) if tot else None,'records':len(rows)}
    def build(eid,depth=0,visited=None):
        if visited is None: visited=set()
        if eid in visited or depth>10: return None
        visited.add(eid)
        emp=db.execute("SELECT * FROM employees WHERE id=?",(eid,)).fetchone()
        if not emp: return None
        emp=dict(emp)
        if sect and emp.get('dept','')!=sect: return None
        own=get_perf(eid,emp.get('emp_code',''))
        roles=[dict(r) for r in db.execute(
            "SELECT r.* FROM roles r JOIN emp_roles er ON r.id=er.role_id WHERE er.emp_id=?",(eid,))]
        mps=[]
        for mp in db.execute(
            "SELECT m.* FROM mps m JOIN mp_owners mo ON m.id=mo.mp_id WHERE mo.emp_id=?",(eid,)).fetchall():
            mp=dict(mp); mp['cps']=[dict(c) for c in db.execute("SELECT * FROM cps WHERE mp_id=?",(mp['id'],))]
            mps.append(mp)
        locs=[dict(l) for l in db.execute(
            "SELECT lo.* FROM locations lo JOIN emp_locations el ON lo.id=el.loc_id WHERE el.emp_id=?",(eid,))]
        subs=db.execute("SELECT id FROM employees WHERE manager_id=?",(eid,)).fetchall()
        children=[]; sub_tot=0; sub_comp=0
        for s in subs:
            node=build(s['id'],depth+1,visited)
            if node:
                children.append(node)
                sub_tot+=node['rollup']['tot']; sub_comp+=node['rollup']['comp']
        rt=own['tot']+sub_tot; rc=own['comp']+sub_comp
        return {'id':emp['id'],'name':emp['name'],'emp_code':emp.get('emp_code',''),
                'role':emp.get('role',''),'dept':emp.get('dept','Ops'),'level':emp.get('level',3),
                'roles':roles,'mps':mps,'locations':locs,'own':own,
                'rollup':{'tot':rt,'comp':rc,'nc':rt-rc,'pct':round(rc/rt*100,2) if rt else None},
                'children':children,'depth':depth}
    roots=db.execute("SELECT id FROM employees WHERE manager_id IS NULL OR manager_id=''").fetchall()
    tree=[build(r['id']) for r in roots]; tree=[t for t in tree if t]
    return jsonify(tree)

@app.route('/api/org/move',methods=['POST'])
def org_move():
    db=get_db(); d=request.json
    eid=d.get('emp_id'); new_mgr=d.get('new_manager_id') or None
    if not eid: return jsonify({'error':'emp_id required'}),400
    def is_sub(root,target):
        subs=db.execute("SELECT id FROM employees WHERE manager_id=?",(root,)).fetchall()
        for s in subs:
            if s['id']==target: return True
            if is_sub(s['id'],target): return True
        return False
    if new_mgr and is_sub(eid,new_mgr): return jsonify({'error':'Cannot assign subordinate as manager'}),400
    db.execute("UPDATE employees SET manager_id=? WHERE id=?",(new_mgr,eid))
    db.commit(); return jsonify({'ok':True})

@app.route('/api/org/assign_mp',methods=['POST'])
def org_assign_mp():
    db=get_db(); d=request.json
    eid=d.get('emp_id'); mid=d.get('mp_id'); loc_id=d.get('loc_id','')
    if not eid or not mid: return jsonify({'error':'emp_id and mp_id required'}),400
    db.execute("INSERT OR IGNORE INTO mp_owners VALUES(?,?)",(mid,eid))
    db.execute("INSERT OR IGNORE INTO emp_mps VALUES(?,?)",(eid,mid))
    if loc_id: db.execute("INSERT OR IGNORE INTO mp_locations VALUES(?,?)",(mid,loc_id))
    db.commit(); return jsonify({'ok':True})

@app.route('/api/org/assign_cp',methods=['POST'])
def org_assign_cp():
    db=get_db(); d=request.json
    eid=d.get('emp_id'); cid=d.get('cp_id'); loc_id=d.get('loc_id','')
    if not eid or not cid: return jsonify({'error':'emp_id and cp_id required'}),400
    db.execute("INSERT OR IGNORE INTO cp_owners VALUES(?,?)",(cid,eid))
    db.execute("INSERT OR IGNORE INTO emp_cps VALUES(?,?)",(eid,cid))
    if loc_id: db.execute("INSERT OR IGNORE INTO cp_locations VALUES(?,?)",(cid,loc_id))
    db.commit(); return jsonify({'ok':True})

@app.route('/api/org/cascade_assign',methods=['POST'])
def org_cascade_assign():
    db=get_db(); d=request.json
    parent_cp_id=d.get('parent_cp_id'); child_emp_id=d.get('child_emp_id')
    child_mp_id=d.get('child_mp_id')
    if not parent_cp_id or not child_emp_id: return jsonify({'error':'parent_cp_id and child_emp_id required'}),400
    cp=db.execute("SELECT * FROM cps WHERE id=?",(parent_cp_id,)).fetchone()
    if not cp: return jsonify({'error':'CP not found'}),404
    if not child_mp_id:
        mid=uid()
        db.execute("INSERT OR IGNORE INTO mps VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (mid,cp['ref'],cp['title'],cp['target'],'Monthly',0,0,0,parent_cp_id,2))
        child_mp_id=mid
    else:
        db.execute("UPDATE mps SET parent_cp_id=? WHERE id=?",(parent_cp_id,child_mp_id))
    link_id=uid()
    db.execute("INSERT OR REPLACE INTO cascade_links VALUES(?,?,?,?,?)",
               (link_id,d.get('parent_emp_id',''),parent_cp_id,child_emp_id,child_mp_id))
    db.execute("INSERT OR IGNORE INTO mp_owners VALUES(?,?)",(child_mp_id,child_emp_id))
    db.commit(); return jsonify({'ok':True,'mp_id':child_mp_id,'link_id':link_id})

'''

idx_route="@app.route('/')\ndef index():"
# Remove old duplicate routes if they exist, then inject fresh
for old_fn in ["def bs_today","def org_tree","def org_move","def org_assign_mp",
               "def org_assign_cp","def org_cascade_assign","def org_node"]:
    if old_fn in src:
        # Find the route decorator before this function and remove until next route
        pattern=re.compile(r'@app\.route[^\n]*\n(?:def (?:bs_today|org_tree|org_move|org_assign_mp|org_assign_cp|org_cascade_assign|org_node|bs_calendar|analytics_by_location_old)\b.*?)(?=\n@app\.route|\Z)',re.DOTALL)
        src=pattern.sub('',src)
        print(f"  Removed old {old_fn}")

if idx_route in src:
    src=src.replace(idx_route, NEW_ROUTES+idx_route)
    changes+=1; print("P3 OK: new API routes injected")
else: print("WARN P3: index route not found")

with open('app.py','w',encoding='utf-8') as f: f.write(src)
print(f"\napp.py done. {changes} major patches applied.")

# Quick verify
with open('app.py', encoding='utf-8') as f: v=f.read()
for c in ["def today_bs","def bs_q","def org_tree","def org_move","def org_cascade_assign","bs_date_str"]:
    print(("  OK  " if c in v else "  MISS  ")+c)
