with open('index.html','r',encoding='utf-8') as f: c=f.read()
n=0

# ── 1. Wrap #nav in flex container and inject user-badge ─────────────────
old_nav = '  <div id="nav">\n    <button class="nav-tab active" onclick="switchTab(\'dashboard\')">📊 Dashboard</button>\n    <button class="nav-tab" onclick="switchTab(\'team\')">👥 Team</button>\n    <button class="nav-tab tab-admin-only" onclick="switchTab(\'master\')">🔧 Master Setup</button>\n    <button class="nav-tab tab-mod-only" onclick="switchTab(\'master\')">🔧 Master Setup</button>\n    <button class="nav-tab" onclick="switchTab(\'data\')">📁 Data Manager</button>\n    <button class="nav-tab" onclick="switchTab(\'reports\')">📈 Reports</button>\n      <button class="nav-tab tab-admin-only" onclick="switchTab(\'org\')">&#127970; Org &amp; Cascade</button>\n  </div>'

new_nav = '  <div style="display:flex;align-items:center;justify-content:space-between;background:#0a1628">\n  <div id="nav">\n    <button class="nav-tab active" onclick="switchTab(\'dashboard\')">📊 Dashboard</button>\n    <button class="nav-tab" onclick="switchTab(\'team\')">👥 Team</button>\n    <button class="nav-tab tab-admin-only" onclick="switchTab(\'master\')">🔧 Master Setup</button>\n    <button class="nav-tab tab-mod-only" onclick="switchTab(\'master\')">🔧 Master Setup</button>\n    <button class="nav-tab" onclick="switchTab(\'data\')">📁 Data Manager</button>\n    <button class="nav-tab" onclick="switchTab(\'reports\')">📈 Reports</button>\n    <button class="nav-tab tab-admin-only" onclick="switchTab(\'org\')">&#127970; Org &amp; Cascade</button>\n  </div>\n  <div id="user-badge" style="flex-shrink:0;padding:4px 12px"></div>\n  </div>'

if old_nav in c:
    c = c.replace(old_nav, new_nav)
    n+=1; print('1 nav wrapped with flex + user-badge injected')
else:
    print('1 SKIP - trying loose match')
    # Try to find and patch more loosely
    import re
    m = re.search(r'(<div id="nav">.*?</div>)(\s*</div>\s*<div id="app">)', c, re.DOTALL)
    if m:
        nav_block = m.group(1)
        # Remove duplicate Org button if present
        nav_block = re.sub(r'\s*<button[^>]*tab-admin-only[^>]*switchTab\(\'org\'\)[^>]*>.*?</button>', '', nav_block)
        new_block = (
            '<div style="display:flex;align-items:center;justify-content:space-between;background:#0a1628">\n'
            + nav_block
            + '\n    <button class="nav-tab tab-admin-only" onclick="switchTab(\'org\')">&#127970; Org &amp; Cascade</button>\n  </div>\n'
            + '  <div id="user-badge" style="flex-shrink:0;padding:4px 12px"></div>\n  </div>'
        )
        c = c[:m.start()] + new_block + c[m.start(1)+len(m.group(1)):]
        n+=1; print('1 nav wrapped (loose match)')
    else:
        print('1 FAILED')

# ── 2. Add CSS for #logout-btn hover and badge link ──────────────────────
hover_css = '\n#logout-btn:hover{background:#dc2626!important;color:#fff!important}\n#nav-admin-link:hover{background:#1d4ed8!important}\n'
if '#logout-btn:hover' not in c:
    c = c.replace('</style>', hover_css + '</style>', 1)
    n+=1; print('2 logout hover CSS added')
else:
    print('2 SKIP hover CSS')

# ── 3. Ensure tab-admin-only / tab-mod-only start hidden ─────────────────
# They'll be shown by applyRoleVisibility after auth
hide_css = '\n.tab-admin-only,.tab-mod-only{display:none}\n'
if '.tab-admin-only,.tab-mod-only{display:none}' not in c:
    c = c.replace('</style>', hide_css + '</style>', 1)
    n+=1; print('3 role tabs hidden by default CSS added')
else:
    print('3 SKIP')

with open('index.html','w',encoding='utf-8') as f: f.write(c)
print(f'\nDone — {n} changes applied')
