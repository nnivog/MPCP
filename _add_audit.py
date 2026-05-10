
with open('app.py','r',encoding='utf-8') as f: c=f.read()

old_schema = 'CREATE TABLE IF NOT EXISTS audit_log'
if old_schema in c:
    print('audit_log table already exists')
else:
    target = "  created_at TEXT DEFAULT '');\n\"\"\")"
    new_target = "  created_at TEXT DEFAULT '');\nCREATE TABLE IF NOT EXISTS audit_log(\n  id INTEGER PRIMARY KEY AUTOINCREMENT,\n  ts TEXT NOT NULL,\n  actor_id TEXT,\n  actor_name TEXT,\n  action TEXT NOT NULL,\n  target_type TEXT,\n  target_id TEXT,\n  detail TEXT,\n  ip TEXT);\n\"\"\")"
    if target in c:
        c = c.replace(target, new_target)
        print('audit_log table schema added')
    else:
        print('NOT MATCHED - checking...')
        idx = c.find("created_at TEXT DEFAULT ''")
        print(repr(c[idx:idx+30]))

helper = '''

def log_audit(action, target_type='', target_id='', detail=''):
    try:
        import datetime as _dt
        mdb = get_master_conn()
        u = session.get('mpcp_user') or {}
        mdb.execute(
            "INSERT INTO audit_log(ts,actor_id,actor_name,action,target_type,target_id,detail,ip) VALUES(?,?,?,?,?,?,?,?)",
            (_dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
             u.get('id',''), u.get('full_name','system'),
             action, target_type, str(target_id), detail,
             request.remote_addr if request else '')
        )
        mdb.commit()
        mdb.close()
    except Exception:
        pass

'''

if 'def log_audit(' not in c:
    idx = c.find('\ndef get_master_conn()')
    end = c.find('\ndef ', idx+10)
    c = c[:end] + helper + c[end:]
    print('log_audit() helper added')
else:
    print('log_audit already exists')

with open('app.py','w',encoding='utf-8') as f: f.write(c)
