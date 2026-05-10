
with open('app.py','r',encoding='utf-8') as f: c=f.read()

# 1. Add tab nav CSS + audit table CSS after existing styles
old_css = '</style></head><body>'
new_css = '''.tab-bar{display:flex;gap:4px;margin-bottom:20px;border-bottom:2px solid #EEEEEE;padding-bottom:0}
.tab-btn{font-family:'Montserrat',sans-serif;font-size:11px;font-weight:700;padding:8px 18px;border:none;background:none;cursor:pointer;color:#777;border-bottom:3px solid transparent;margin-bottom:-2px;text-transform:uppercase;letter-spacing:.3px}
.tab-btn.active{color:#ED1C24;border-bottom-color:#ED1C24}
.tab-btn:hover{color:#ED1C24}
.tab-panel{display:none}.tab-panel.active{display:block}
.audit-table td{font-size:11px;padding:8px 12px}
.audit-action{font-family:'Montserrat',sans-serif;font-weight:700;font-size:10px;padding:2px 7px;border-radius:3px;background:#F0FDF4;color:#166534}
.audit-action.login{background:#EFF6FF;color:#1D4ED8}
.audit-action.delete,.audit-action.disable{background:#FFF0F0;color:#ED1C24}
.audit-action.edit{background:#FFFBEB;color:#92400E}
</style></head><body>'''

if old_css in c:
    c = c.replace(old_css, new_css)
    print('1. CSS added')
else:
    print('1. CSS NOT MATCHED')

# 2. Add tab bar after container div + msg block
old_container = '<div class="container">\n  {% if msg %}'
new_container = '''<div class="container">
  {% if msg %}<div class="{{ 'msg-ok' if msg_type=='ok' else 'msg-err' }}">{{ '\u2713' if msg_type=='ok' else '\u26a0' }}&nbsp; {{ msg }}</div>{% endif %}
  <div class="tab-bar">
    <button class="tab-btn active" onclick="switchTab('users')">&#128100; Users</button>
    <button class="tab-btn" onclick="switchTab('audit')">&#128203; Audit Log</button>
  </div>
  <div id="tab-users" class="tab-panel active">
  {% if msg_REMOVE %}'''

# simpler - just add tab bar before first card
old_first_card = '  <div class="card">\n    <div class="card-head"><h2>&#43; Create New User</h2></div>'
new_first_card = '''  <div class="tab-bar">
    <button class="tab-btn active" onclick="switchAdminTab('users',this)">&#128100; Users</button>
    <button class="tab-btn" onclick="switchAdminTab('audit',this)">&#128203; Audit Log</button>
  </div>
  <div id="admin-tab-users" class="tab-panel active">
  <div class="card">
    <div class="card-head"><h2>&#43; Create New User</h2></div>'''

if old_first_card in c:
    c = c.replace(old_first_card, new_first_card)
    print('2. Tab bar added')
else:
    print('2. Tab bar NOT MATCHED')

with open('app.py','w',encoding='utf-8') as f: f.write(c)
