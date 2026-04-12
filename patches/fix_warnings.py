with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

changes = 0

# Fix 1: loadAll (2-space indent)
old = "  const [e,m,c,r,p,ca] = await Promise.all([\n    api.get('/api/employees'), api.get('/api/mps'), api.get('/api/cps'),\n    api.get('/api/roles'), api.get('/api/perf'), api.get('/api/cache')\n  ])\n  S.employees=e; S.mps=m; S.cps=c; S.roles=r; S.perf=p; S.cache=ca"
new = "  const [e,m,c,r,p,ca,locs] = await Promise.all([\n    api.get('/api/employees'), api.get('/api/mps'), api.get('/api/cps'),\n    api.get('/api/roles'), api.get('/api/perf'), api.get('/api/cache'),\n    api.get('/api/locations')\n  ])\n  S.employees=e; S.mps=m; S.cps=c; S.roles=r; S.perf=p; S.cache=ca; S.locations=locs"
if old in html: html=html.replace(old,new); changes+=1; print("Fix 1 OK: loadAll")
else: print("Fix 1 SKIP: already done or not found")

# Fix 2: renderMaster (2-space indent)
old = "  else renderLinks()\n}"
new = "  else if(S.masterSub==='locations') renderLocations()\n  else renderLinks()\n}"
if old in html: html=html.replace(old,new,1); changes+=1; print("Fix 2 OK: renderMaster")
else: print("Fix 2 SKIP: already done or not found")

# Fix 3: renderReport
old = "async function renderReport(){\n  if(S.reportSub==='overview') renderOverviewReport()\n  else if(S.reportSub==='yoy') await renderYoYReport()\n  else if(S.reportSub==='employee') renderEmpReport()\n  else renderMPCPReport()\n}"
new = "async function renderReport(){\n  if(S.reportSub==='location'){ renderLocationReport(); return }\n  if(S.reportSub==='overview') renderOverviewReport()\n  else if(S.reportSub==='yoy') await renderYoYReport()\n  else if(S.reportSub==='employee') renderEmpReport()\n  else renderMPCPReport()\n}"
if old in html: html=html.replace(old,new); changes+=1; print("Fix 3 OK: renderReport")
else: print("Fix 3 SKIP: already done or not found")

# Fix 4: Locations master tab button
old = "<button class=\"sub-tab\" onclick=\"switchMaster('links')\">Role Assignments</button>"
new = old + "\n\t\t\t<button class=\"sub-tab\" onclick=\"switchMaster('locations')\">&#128205; Locations</button>"
if old in html and "switchMaster('locations')" not in html: html=html.replace(old,new); changes+=1; print("Fix 4 OK: Locations tab button")
else: print("Fix 4 SKIP: already done or not found")

# Fix 5: By Location report tab button
old = "<button class=\"sub-tab\" onclick=\"switchReport('mpcp')\">🎯 MP / CP Drill-down</button>"
new = old + "\n\t\t\t<button class=\"sub-tab\" onclick=\"switchReport('location')\">&#128205; By Location</button>"
if old in html and "switchReport('location')" not in html: html=html.replace(old,new); changes+=1; print("Fix 5 OK: By Location tab button")
else: print("Fix 5 SKIP: already done or not found")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("\nAll done. Changes applied:", changes)
