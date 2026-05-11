with open('app.py','r',encoding='utf-8') as f: c=f.read()
count = 0
def patch(old, new, label):
    global c, count
    if old in c:
        c = c.replace(old, new, 1)
        print(f'OK: {label}')
        count += 1
    else:
        print(f'MISS: {label}')

patch(
    'db.execute("INSERT OR REPLACE INTO employees VALUES(?,?,?,?,?,?,?,?)",',
    'log_audit("EMP_CREATE", "employee", eid, f"Created employee {d.get(chr(39)+chr(39))}" )\n    db.execute("INSERT OR REPLACE INTO employees VALUES(?,?,?,?,?,?,?,?)",',
    'EMP_CREATE'
)
patch(
    'db.execute("UPDATE employees SET emp_code=?,name=?,role=?,level=?,dept=?,manager_id=?,email=? WHERE id=?",',
    'log_audit("EMP_UPDATE", "employee", eid, f"Updated employee {eid}")\n    db.execute("UPDATE employees SET emp_code=?,name=?,role=?,level=?,dept=?,manager_id=?,email=? WHERE id=?",',
    'EMP_UPDATE'
)
patch(
    'db.execute(f"DELETE FROM {t} WHERE emp_id=?", (eid,))\n        db.execute("INSERT OR IGNORE INTO emp_roles VALUES(?,?)", (eid, rid))',
    'log_audit("EMP_DELETE", "employee", eid, f"Deleted employee {eid}")\n        db.execute(f"DELETE FROM {t} WHERE emp_id=?", (eid,))\n        db.execute("INSERT OR IGNORE INTO emp_roles VALUES(?,?)", (eid, rid))',
    'EMP_DELETE'
)
patch(
    'db.execute("INSERT OR REPLACE INTO mps VALUES(?,?,?,?,?,?,?,?)",',
    'log_audit("MP_SAVE", "mp", mid, f"Saved MP {d.get(chr(39)+'ref'+chr(39),mid)}")\n    db.execute("INSERT OR REPLACE INTO mps VALUES(?,?,?,?,?,?,?,?)",',
    'MP_SAVE'
)
patch(
    'db.execute("DELETE FROM mps WHERE id=?", (mid,))',
    'log_audit("MP_DELETE", "mp", mid, f"Deleted MP {mid}")\n        db.execute("DELETE FROM mps WHERE id=?", (mid,))',
    'MP_DELETE'
)
patch(
    'db.execute("INSERT OR REPLACE INTO cps VALUES(?,?,?,?,?,?,?)",',
    'log_audit("CP_SAVE", "cp", cid, f"Saved CP {d.get(chr(39)+chr(39),cid)}")\n    db.execute("INSERT OR REPLACE INTO cps VALUES(?,?,?,?,?,?,?)",',
    'CP_SAVE'
)
patch(
    'db.execute("DELETE FROM cps WHERE id=?", (cid,))',
    'log_audit("CP_DELETE", "cp", cid, f"Deleted CP {cid}")\n        db.execute("DELETE FROM cps WHERE id=?", (cid,))',
    'CP_DELETE'
)
patch(
    'db.execute("INSERT INTO departments',
    'log_audit("DEPT_CREATE", "department", "", f"Created dept")\n        db.execute("INSERT INTO departments',
    'DEPT_CREATE'
)
patch(
    'db.execute("INSERT INTO locations',
    'log_audit("LOC_CREATE", "location", "", f"Created location")\n        db.execute("INSERT INTO locations',
    'LOC_CREATE'
)
patch(
    'db.executemany("INSERT OR IGNORE INTO perf VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", perf)',
    'log_audit("PERF_IMPORT", "perf", "", f"Imported {len(perf)} perf records")\n    db.executemany("INSERT OR IGNORE INTO perf VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", perf)',
    'PERF_IMPORT'
)
print(f'Total patches: {count}')
with open('app.py','w',encoding='utf-8') as f: f.write(c)