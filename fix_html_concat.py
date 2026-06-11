content = open('index.html', encoding='utf-8').read()

old = "      +(u.username!=='admin'?'<button"
new = "      html+=(u.username!=='admin'?'<button"

if old in content:
    content = content.replace(old, new, 1)
    open('index.html', 'w', encoding='utf-8').write(content)
    print('Fixed: html+= added')
else:
    print('Not found - already fixed or different content')
