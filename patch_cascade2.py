with open('app.py','r',encoding='utf-8') as f: lines=f.readlines()

# Find all def lines for cascade_link handlers
defs = [(i,l) for i,l in enumerate(lines) if 'def cascade_link' in l]
print('Found:', [(i+1,l.strip()) for i,l in defs])

# Find the one that only has DELETE (not PUT) — it's the older one
for i,l in defs:
    # Look at the @app.route line above it
    route_line = lines[i-1] if i>0 else ''
    if "'DELETE'" in route_line and "'PUT'" not in route_line:
        # Find route decorator start
        start = i-1
        while start > 0 and '@app.route' not in lines[start]: start -= 1
        # Find function end
        end = i+1
        while end < len(lines):
            if lines[end].startswith('@app.route') or ("if __name__" in lines[end] and not lines[end].startswith(' ')):
                break
            end += 1
        print(f'Removing DELETE-only route at lines {start+1}–{end}')
        del lines[start:end]
        break

with open('app.py','w',encoding='utf-8') as f: f.writelines(lines)
print('Done')
