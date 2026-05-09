with open('app.py','r',encoding='utf-8') as f: c=f.read()
n=0

# Fix master summary to also count mps/cps
old_sum = "        mps  = d.execute(\"SELECT COUNT(*) c FROM mps\").fetchone()['c']\n        cps  = d.execute(\"SELECT COUNT(*) c FROM cps\").fetchone()['c']"
if old_sum in c: print('master summary already correct')
else:
    # Find and patch the summary function
    old_s2 = "        emps = d.execute(\"SELECT COUNT(*) c FROM employees\").fetchone()['c']"
    new_s2 = "        emps = d.execute(\"SELECT COUNT(*) c FROM employees\").fetchone()['c']\n        mps2 = d.execute(\"SELECT COUNT(*) c FROM mps\").fetchone()['c'] if d.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='mps'\").fetchone() else 0\n        cps2 = d.execute(\"SELECT COUNT(*) c FROM cps\").fetchone()['c'] if d.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='cps'\").fetchone() else 0"
    if old_s2 in c:
        c=c.replace(old_s2, new_s2)
        c=c.replace("summary.append({**dept,'employees':emps,'mps':mps,'cps':cps,'compliance':pct})",
                    "summary.append({**dept,'employees':emps,'mps':mps2,'cps':cps2,'compliance':pct})")
        n+=1; print('1 master summary mp/cp counts fixed')

# Add perf isolation — inject emp_code filter for 'user' role in perf GET
old_perf = "@app.route('/api/perf')\ndef perf_api():"
if old_perf in c:
    idx = c.find(old_perf)
    # Find the db.execute for perf
    chunk = c[idx:idx+600]
    if 'perf_emp_filter' not in chunk:
        # Find the query line
        old_q = "    rows = R(db.execute(q2 + ' ORDER BY"
        if old_q not in c[idx:idx+800]:
            print('2 perf query pattern not matched - check manually')
        else:
            old_pq = '    rows = R(db.execute(q2'
            new_pq = '    q2, args = perf_emp_filter(q2, args)\n    rows = R(db.execute(q2'
            # Only replace within perf_api
            end_idx = c.find('\n@app.route', idx+10)
            segment = c[idx:end_idx]
            if old_pq in segment:
                new_segment = segment.replace(old_pq, new_pq, 1)
                c = c[:idx] + new_segment + c[end_idx:]
                n+=1; print('2 perf isolation (user role) added')

with open('app.py','w',encoding='utf-8') as f: f.write(c)
print(f'\nDone — {n} changes applied')
