with open('index.html', 'r', encoding='utf-8') as f:
    txt = f.read()

# Check router
idx = txt.find('renderCurrent')
print("=== renderCurrent function ===")
print(txt[idx:idx+400])

# Check nav tab
idx2 = txt.find("switchTab('locations')")
if idx2 > -1:
    print("\n=== Nav tab found ===")
    print(txt[idx2-50:idx2+80])
else:
    print("\nNav tab MISSING")

# Check tab panel
idx3 = txt.find('id="tab-locations"')
if idx3 > -1:
    print("\n=== Tab panel found ===")
    print(txt[idx3-10:idx3+60])
else:
    print("\nTab panel MISSING")

# Check renderLocations
count = txt.count('function renderLocations')
print(f"\nrenderLocations defined: {count} time(s)")

# Check the error line area (around line 548)
lines = txt.splitlines()
print(f"\n=== Lines 540-555 ===")
for i, l in enumerate(lines[539:555], 540):
    print(f"{i}: {l[:120]}")
