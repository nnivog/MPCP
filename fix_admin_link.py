with open('index.html','r',encoding='utf-8') as f: c=f.read()

# Add admin panel link in badge for admins
old_logout = '+ \'<a href="/logout" id="logout-btn" title="Sign Out" style="display:flex;align-items:center;justify-content:center;width:28px;height:28px;background:#1a2d4a;border-radius:8px;color:#f87171;font-size:14px;text-decoration:none;border:1px solid #2d4a6b;flex-shrink:0">&#10148;</a>\''

new_logout = """+ (canAdmin() ? '<a href="/admin" target="_blank" title="Admin Panel" style="display:flex;align-items:center;justify-content:center;width:28px;height:28px;background:#1a2d4a;border-radius:8px;color:#60a5fa;font-size:12px;text-decoration:none;border:1px solid #2d4a6b;flex-shrink:0;font-weight:700">&#9881;</a>' : '')
    + '<a href="/logout" id="logout-btn" title="Sign Out" style="display:flex;align-items:center;justify-content:center;width:28px;height:28px;background:#1a2d4a;border-radius:8px;color:#f87171;font-size:14px;text-decoration:none;border:1px solid #2d4a6b;flex-shrink:0">&#10148;</a>'"""

if old_logout in c:
    c=c.replace(old_logout, new_logout)
    print('✓ Admin panel link added to nav badge')
else:
    print('✗ logout btn string not matched')

with open('index.html','w',encoding='utf-8') as f: f.write(c)
