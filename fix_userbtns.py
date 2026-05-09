with open('index.html','r',encoding='utf-8') as f: lines=f.readlines()

for i,l in enumerate(lines):
    if "openUserForm(''+u.id+'')" in l:
        print(f'Before: {l.rstrip()}')
        lines[i] = '      html+=\'<button class="btn btn-ghost btn-sm" onclick="openUserForm(\'+JSON.stringify(u.id)+\')" style="font-size:10px;margin-right:4px">Edit</button>\'\n'
        print(f'After:  {lines[i].rstrip()}')
    if "resetUserPw(''+u.id" in l:
        print(f'Before: {l.rstrip()}')
        lines[i] = '      html+=\'<button class="btn btn-ghost btn-sm" style="color:var(--red);font-size:10px" onclick="resetUserPw(\'+JSON.stringify(u.id)+\',\'+JSON.stringify(u.username)+\')">Reset PW</button>\'\n'
        print(f'After:  {lines[i].rstrip()}')

with open('index.html','w',encoding='utf-8') as f: f.writelines(lines)
print('Done')
