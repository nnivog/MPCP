with open('index.html','r',encoding='utf-8') as f: lines=f.readlines()

i = 2858  # line 2859
print('Before:', lines[i].rstrip())
lines[i] = '      html+=\'<button class="btn btn-ghost btn-sm" onclick="openUserForm(\'+JSON.stringify(u.id)+\')" style="font-size:10px;margin-right:4px">Edit</button>\'\n'
print('After: ', lines[i].rstrip())

i2 = 2859  # line 2860
print('Before:', lines[i2].rstrip())
lines[i2] = '      html+=\'<button class="btn btn-ghost btn-sm" style="color:var(--red);font-size:10px" onclick="resetUserPw(\'+JSON.stringify(u.id)+\',\'+JSON.stringify(u.username)+\')">Reset PW</button>\'\n'
print('After: ', lines[i2].rstrip())

with open('index.html','w',encoding='utf-8') as f: f.writelines(lines)
print('Done')
