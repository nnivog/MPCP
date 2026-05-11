with open('app.py','r',encoding='utf-8') as f: c=f.read()
count = 0

old = 'db.execute("INSERT OR REPLACE INTO employees VALUES(?,?,?,?,?,?,?,?)",\n            (eid, d[\'emp_code\'].strip(), d[\'name\'].strip(), d.get(\'role\')'
idx = c.find('INSERT OR REPLACE INTO employees VALUES')
print('emp insert at line:', c[:idx].count('\n')+1 if idx>0 else 'NOT FOUND')

print('Script check done')