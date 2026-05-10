
with open('app.py','r',encoding='utf-8') as f: c=f.read()

# Find ADMIN_HTML and add audit tab button
old_tab = '<a href="#" onclick="showTab(\'users\')">Users</a>'
# Try to find admin tab structure
idx = c.find('ADMIN_HTML = ')
end = c.find('\n"""\n', idx+20)+4
block = c[idx:end]

print('Admin HTML length:', len(block))
# Find a tab nav in admin
for term in ['admin-tab', 'showTab', 'tab-nav', 'Users</a>', 'Users</button>']:
    tidx = block.find(term)
    if tidx > 0:
        print(f'Found {term} at {tidx}:', repr(block[tidx:tidx+80]))
        break
