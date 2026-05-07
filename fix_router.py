with open('index.html', 'r', encoding='utf-8') as f:
    txt = f.read()

# Fix both renderCurrent functions to include locations
old = "  else if(S.currentTab==='reports') renderReport()\n  else if(S.currentTab==='org') renderOrgTab()\n}"
new = "  else if(S.currentTab==='reports') renderReport()\n  else if(S.currentTab==='org') renderOrgTab()\n  else if(S.currentTab==='locations') renderLocations()\n}"

count = txt.count(old)
print(f"Pattern found {count} time(s)")

if count > 0:
    txt = txt.replace(old, new)
    print("Fixed renderCurrent")
else:
    # Try without org tab
    old2 = "  else if(S.currentTab==='reports') renderReport()\n}"
    count2 = txt.count(old2)
    print(f"Alt pattern found {count2} time(s)")
    if count2 > 0:
        txt = txt.replace(old2, "  else if(S.currentTab==='reports') renderReport()\n  else if(S.currentTab==='locations') renderLocations()\n}")
        print("Fixed renderCurrent (alt)")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(txt)

# Verify
import re
for m in re.finditer(r'function renderCurrent\(\) \{.*?\}', txt, re.DOTALL):
    print("\n=== renderCurrent after fix ===")
    print(m.group(0)[:300])
