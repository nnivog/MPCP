
with open('app.py','r',encoding='utf-8') as f: c=f.read()
count = 0

def patch(old, new, label):
    global c, count
    if old in c:
        c = c.replace(old, new, 1)
        print("OK:", label)
        count += 1
    else:
        print("MISS:", label)

# EMP CREATE
patch(
    'db.execute("INSERT OR REPLACE INTO employees VALUES(?,?,?,?,?,?,?,?)",',
    'log_audit("EMP_CREATE","employee",eid,"Created/updated employee "+str(eid))\n    db.execute("INSERT OR REPLACE INTO employees VALUES(?,?,?,?,?,?,?,?)",',
    "EMP_CREATE"
)

# EMP UPDATE
patch(
    'db.execute("UPDATE employees SET emp_code=?,name=?,role=?,level=?,dept=?,manager_id=?,email=? WHERE id=?",',
    'log_audit("EMP_UPDATE","employee",eid,"Updated employee "+str(eid))\n    db.execute("UPDATE employees SET emp_code=?,name=?,role=?,level=?,dept=?,manager_id=?,email=? WHERE id=?",',
    "EMP_UPDATE"
)

# MP SAVE
patch(
    'db.execute("INSERT OR REPLACE INTO mps VALUES(?,?,?,?,?,?,?,?)",',
    'log_audit("MP_SAVE","mp",mid,"Saved MP "+str(mid))\n    db.execute("INSERT OR REPLACE INTO mps VALUES(?,?,?,?,?,?,?,?)",',
    "MP_SAVE"
)

# MP DELETE
patch(
    'db.execute("DELETE FROM mps WHERE id=?", (mid,))\n        db.execute("DELETE FROM mp_owners WHERE mp_id=?", (mid,))',
    'log_audit("MP_DELETE","mp",mid,"Deleted MP "+str(mid))\n        db.execute("DELETE FROM mps WHERE id=?", (mid,))\n        db.execute("DELETE FROM mp_owners WHERE mp_id=?", (mid,))',
    "MP_DELETE"
)

# CP SAVE
patch(
    'db.execute("INSERT OR REPLACE INTO cps VALUES(?,?,?,?,?,?,?)",',
    'log_audit("CP_SAVE","cp",cid,"Saved CP "+str(cid))\n    db.execute("INSERT OR REPLACE INTO cps VALUES(?,?,?,?,?,?,?)",',
    "CP_SAVE"
)

# CP DELETE
patch(
    'db.execute("DELETE FROM cps WHERE id=?", (cid,))',
    'log_audit("CP_DELETE","cp",cid,"Deleted CP "+str(cid))\n        db.execute("DELETE FROM cps WHERE id=?", (cid,))',
    "CP_DELETE"
)

# PERF IMPORT
patch(
    'db.executemany("INSERT OR IGNORE INTO perf VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", perf)',
    'log_audit("PERF_IMPORT","perf","",str(len(perf))+" records imported")\n    db.executemany("INSERT OR IGNORE INTO perf VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", perf)',
    "PERF_IMPORT"
)

# DEPT CREATE
patch(
    'db.execute("INSERT INTO departments',
    'log_audit("DEPT_CREATE","department","","Created department")\n        db.execute("INSERT INTO departments',
    "DEPT_CREATE"
)

# LOCATION CREATE/UPDATE
patch(
    'db.execute("INSERT OR REPLACE INTO locations',
    'log_audit("LOC_SAVE","location","","Saved location")\n        db.execute("INSERT OR REPLACE INTO locations',
    "LOC_SAVE"
)

print("Total patches:", count)
with open('app.py','w',encoding='utf-8') as f: f.write(c)
