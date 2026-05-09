with open('app.py','r',encoding='utf-8') as f: lines=f.readlines()

start = next(i for i,l in enumerate(lines) if 'LOGIN_HTML = """' in l)
end   = next(i for i,l in enumerate(lines) if '@app.route(\'/login\'' in l)

print(f'Replacing LOGIN_HTML: lines {start+1}–{end}')

new_html = [
    'LOGIN_HTML = """\n',
    '<!DOCTYPE html><html><head><meta charset="UTF-8">\n',
    '<meta name="viewport" content="width=device-width,initial-scale=1">\n',
    '<title>MPCP Login</title>\n',
    '<style>\n',
    '*{box-sizing:border-box;margin:0;padding:0}\n',
    'body{font-family:Arial,sans-serif;background:linear-gradient(135deg,#0a1628,#1a2d4a);min-height:100vh;display:flex;align-items:center;justify-content:center}\n',
    '.card{background:#fff;border-radius:16px;padding:36px;width:380px;box-shadow:0 24px 80px rgba(0,0,0,.5)}\n',
    '.logo{text-align:center;margin-bottom:24px}\n',
    '.logo h1{font-size:20px;font-weight:900;color:#0a1628}\n',
    '.logo p{font-size:11px;color:#6b7a99;margin-top:3px}\n',
    '.fg{margin-bottom:14px}\n',
    'label{display:block;font-size:10px;font-weight:700;color:#374151;margin-bottom:5px;text-transform:uppercase;letter-spacing:.6px}\n',
    'input,select{width:100%;padding:10px 14px;border:1.5px solid #e5e7eb;border-radius:8px;font-size:13px;outline:none;transition:.2s;color:#0f1a2e}\n',
    'input:focus,select:focus{border-color:#1d4ed8;box-shadow:0 0 0 3px #1d4ed820}\n',
    '.btn{width:100%;padding:12px;background:#0a1628;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;margin-top:6px}\n',
    '.btn:hover{background:#1d4ed8}\n',
    '.err{background:#fef2f2;border:1px solid #fecaca;color:#dc2626;padding:10px 14px;border-radius:8px;font-size:12px;margin-bottom:14px}\n',
    '.divider{text-align:center;font-size:10px;color:#9ca3af;margin:14px 0;position:relative}\n',
    '.divider::before{content:"";position:absolute;top:50%;left:0;right:0;height:1px;background:#e5e7eb}\n',
    '.divider span{background:#fff;padding:0 10px;position:relative}\n',
    '.alt-link{display:block;text-align:center;font-size:12px;color:#6b7a99;text-decoration:none;padding:9px;border:1.5px solid #e5e7eb;border-radius:8px;font-weight:600}\n',
    '.alt-link:hover{border-color:#0a1628;color:#0a1628}\n',
    '.foot{text-align:center;margin-top:18px;font-size:10px;color:#9ca3af}\n',
    '</style></head><body>\n',
    '<div class="card">\n',
    '  <div class="logo"><h1>&#128200; SC-MPCP System</h1><p>Sipradi Trading Pvt. Ltd.</p></div>\n',
    '  {% if error %}<div class="err">&#9888; {{ error }}</div>{% endif %}\n',
    '  <form method="POST" action="/login">\n',
    '    {% if not admin_mode %}\n',
    '    <div class="fg"><label>Department</label>\n',
    '      <select name="dept_hint" id="dept-sel">\n',
    '        <option value="">&#8212; Select your department &#8212;</option>\n',
    '        {% for d in departments %}\n',
    '        <option value="{{ d.code }}"{% if d.code == selected_dept %} selected{% endif %}>{{ d.name }}</option>\n',
    '        {% endfor %}\n',
    '      </select>\n',
    '    </div>\n',
    '    {% endif %}\n',
    '    <div class="fg"><label>Username</label>\n',
    '      <input type="text" name="username" placeholder="Enter username" autofocus required value="{{ prefill_username }}"></div>\n',
    '    <div class="fg"><label>Password</label>\n',
    '      <input type="password" name="password" placeholder="Enter password" required></div>\n',
    '    {% if admin_mode %}<input type="hidden" name="admin_mode" value="1">{% endif %}\n',
    '    <button class="btn">{% if admin_mode %}&#128274; Sign In as Admin{% else %}Sign In{% endif %}</button>\n',
    '  </form>\n',
    '  <div class="divider"><span>or</span></div>\n',
    '  {% if not admin_mode %}\n',
    '  <a href="/login?admin=1" class="alt-link">&#128274; Master Admin Login</a>\n',
    '  {% else %}\n',
    '  <a href="/login" class="alt-link">&#8592; Back to Department Login</a>\n',
    '  {% endif %}\n',
    '  <div class="foot">SC-MPCP &copy; {{ year }} Sipradi Trading Pvt. Ltd.</div>\n',
    '</div></body></html>\n',
    '"""\n',
]

lines[start:end] = new_html

with open('app.py','w',encoding='utf-8') as f: f.writelines(lines)
print('Done')
