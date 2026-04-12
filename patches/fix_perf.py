with open('app.py', 'r', encoding='utf-8') as f:
    src = f.read()

# Fix P() to include empty location as 20th value
old = '        return (pid,fy,bsm,bs_q(bsm),eid,ec,mpr,cpr,metric,tot,comp,nc,pct_c,pct_nc,tgt,act,unit,st,notes)'
new = '        return (pid,fy,bsm,bs_q(bsm),eid,ec,mpr,cpr,metric,tot,comp,nc,pct_c,pct_nc,tgt,act,unit,st,notes,\'\')'

if old in src:
    src = src.replace(old, new)
    print("Fix OK: P() now returns 20 values")
else:
    print("FAIL: P() return line not found")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(src)
