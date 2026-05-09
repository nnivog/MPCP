with open('app.py','r',encoding='utf-8') as f: lines=f.readlines()

# Find the login function start and end
start = next(i for i,l in enumerate(lines) if 'def login():' in l)
end   = next(i for i,l in enumerate(lines) if '@app.route(\'/logout\')' in l)

print(f'Replacing lines {start+1}–{end} ({end-start} lines)')

new_fn = [
    "def login():\n",
    "    error = None\n",
    "    admin_mode = request.args.get('admin')=='1' or request.form.get('admin_mode')=='1'\n",
    "    db = get_master_conn()\n",
    "    departments = R(db.execute('SELECT code,name FROM departments WHERE active=1 ORDER BY name').fetchall())\n",
    "    db.close()\n",
    "    selected_dept = request.form.get('dept_hint','') or request.args.get('dept','')\n",
    "    if request.method == 'POST':\n",
    "        username = request.form.get('username','').strip().lower()\n",
    "        password = request.form.get('password','')\n",
    "        db = get_master_conn()\n",
    "        user = db.execute(\n",
    "            'SELECT u.*,d.name dept_name FROM users u '\n",
    "            'LEFT JOIN departments d ON d.code=u.dept_code '\n",
    "            'WHERE u.username=? AND u.active=1', (username,)\n",
    "        ).fetchone()\n",
    "        db.close()\n",
    "        if user and verify_password(password, user['password_hash']):\n",
    "            session.permanent = True\n",
    "            session['mpcp_user'] = {\n",
    "                'id':        user['id'],\n",
    "                'username':  user['username'],\n",
    "                'full_name': user['full_name'],\n",
    "                'role':      user['role'],\n",
    "                'dept_code': user['dept_code'],\n",
    "                'dept_name': dict(user).get('dept_name') or 'All Departments',\n",
    "                'emp_code':  user['emp_code'] or '',\n",
    "                'active_dept': user['dept_code']\n",
    "            }\n",
    "            return redirect('/')\n",
    "        error = 'Invalid username or password'\n",
    "    import datetime as _dt\n",
    "    return render_template_string(LOGIN_HTML,\n",
    "        error=error, admin_mode=admin_mode,\n",
    "        departments=departments, selected_dept=selected_dept,\n",
    "        prefill_username='admin' if admin_mode else '',\n",
    "        year=_dt.datetime.now().year)\n",
]

lines[start:end] = new_fn

with open('app.py','w',encoding='utf-8') as f: f.writelines(lines)
print('Done')
