with open('app.py', 'r', encoding='utf-8') as f:
    txt = f.read()

# Find custom 404 handler
import re
matches = re.findall(r'.{100}Route not found.{100}', txt)
for m in matches:
    print("Found 404 handler context:")
    print(m)
    print()

# Find where locations route is defined - show surrounding code
idx = txt.find("@app.route('/api/locations'")
if idx > -1:
    print("Locations route at char", idx)
    print(txt[idx-200:idx+300])
else:
    print("LOCATIONS ROUTE NOT FOUND IN FILE")
