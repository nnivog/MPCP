with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix \"dashboard\" in raw JS code (not inside string literals)
# These should be 'dashboard' not \"dashboard\"
fixes = [
    ('switchTab(\\"dashboard\\")', "switchTab('dashboard')"),
    ('switchTab(\\"team\\")',       "switchTab('team')"),
    ('switchTab(\\"master\\")',     "switchTab('master')"),
    ('switchTab(\\"data\\")',       "switchTab('data')"),
    ('switchTab(\\"reports\\")',    "switchTab('reports')"),
    ('switchTab(\\"org\\")',        "switchTab('org')"),
]

total = 0
for old, new in fixes:
    count = content.count(old)
    if count:
        content = content.replace(old, new)
        print(f'Fixed {count}x: {old} -> {new}')
        total += count

# But we must NOT fix the one inside the html+='...' string in renderDepartments
# That one needs \" to escape inside the onclick attribute
# So re-fix that specific one back
render_broken = "switchTab('dashboard\")}"  # won't exist, just safety
# The renderDepartments line uses it inside onclick="..." so it needs the backslash
# Find and restore it
old_render = """').then(function(){switchTab('dashboard')})">&#128065; View</button>'"""
new_render = """').then(function(){switchTab(\\"dashboard\\")})">&#128065; View</button>'"""
if old_render in content:
    content = content.replace(old_render, new_render)
    print(f'Restored escaped version in renderDepartments onclick')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\n✅ Total fixes: {total}')
