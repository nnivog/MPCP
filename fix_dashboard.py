with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

broken = "switchTab('dashboard')"
fixed  = 'switchTab(\\"dashboard\\")'

count = content.count(broken)
print(f"Found '{broken}' {count} time(s)")

if count > 0:
    content = content.replace(broken, fixed)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Fixed")
else:
    # Show what's actually there
    idx = content.find('switchTab')
    while idx != -1:
        print(f"  Found switchTab at char {idx}: {repr(content[idx:idx+40])}")
        idx = content.find('switchTab', idx+1)
        if idx > content.find('switchTab') + 5000:
            break
