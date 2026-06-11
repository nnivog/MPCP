content = open('index.html', encoding='utf-8').read()

old = """html+='<button class="btn btn-ghost btn-sm" style="font-size:10px" onclick="switchDept('+JSON.stringify(d.code)+').then(function(){switchTab(\\"dashboard\\")})">&#128065; View</button>'"""

new = """html+='<button class="btn btn-ghost btn-sm" style="font-size:10px" onclick="switchDept('+JSON.stringify(d.code)+').then(function(){switchTab(\'dashboard\')})">&#128065; View</button>'"""

if old in content:
    content = content.replace(old, new, 1)
    open('index.html', 'w', encoding='utf-8').write(content)
    print('✅ Fixed View button onclick')
else:
    # Try finding the actual line
    for i, line in enumerate(content.split('\n'), 1):
        if 'switchDept' in line and 'View' in line:
            print(f'Line {i}: {repr(line)}')
    print('❌ Pattern not found - check line above')
