with open('app.py', 'r', encoding='utf-8') as f:
    src = f.read()

changes = 0

# Fix 1: P() return value - add empty location
old = "        return (pid,fy,bsm,bs_q(bsm),eid,ec,mpr,cpr,metric,tot,comp,nc,pct_c,pct_nc,tgt,act,unit,st,notes)"
new = "        return (pid,fy,bsm,bs_q(bsm),eid,ec,mpr,cpr,metric,tot,comp,nc,pct_c,pct_nc,tgt,act,unit,st,notes,'')"
if old in src: src=src.replace(old,new); changes+=1; print("Fix 1 OK: P() return value")
else: print("Fix 1 SKIP: already done")

# Fix 2: seed INSERT - 19 placeholders -> 20
old = 'db.executemany("INSERT OR IGNORE INTO perf VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",perf)'
new = 'db.executemany("INSERT OR IGNORE INTO perf VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",perf)'
if old in src: src=src.replace(old,new); changes+=1; print("Fix 2 OK: INSERT placeholders")
else: print("Fix 2 SKIP: already done")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(src)
print("Done. Changes:", changes)
