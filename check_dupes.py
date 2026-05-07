import re

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

routes = {}
funcs  = {}

for i, line in enumerate(lines, 1):
    # Check duplicate routes
    rm = re.search(r"@app\.route\('([^']+)'", line)
    if rm:
        route = rm.group(1)
        if route in routes:
            print(f"DUPLICATE ROUTE: '{route}' at line {i} (first at line {routes[route]})")
        else:
            routes[route] = i

    # Check duplicate function names
    fm = re.search(r'^def (\w+)\(', line)
    if fm:
        fname = fm.group(1)
        if fname in funcs:
            print(f"DUPLICATE FUNCTION: '{fname}' at line {i} (first at line {funcs[fname]})")
        else:
            funcs[fname] = i

print("Check complete. Total routes:", len(routes), "| Total functions:", len(funcs))
