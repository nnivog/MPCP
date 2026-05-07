with open('app.py', 'r', encoding='utf-8') as f:
    txt = f.read()

print("Total lines:", len(txt.splitlines()))
print("locations_api in file:", 'def locations_api' in txt)
print("location_api in file:", 'def location_api' in txt)
print("/api/locations route:", "'/api/locations'" in txt)

# Show all routes
import re
routes = re.findall(r"@app\.route\('([^']+)'", txt)
print("\nAll routes:")
for r in routes:
    print(" ", r)
