with open('index.html','r',encoding='utf-8') as f: lines=f.readlines()

i = 2778  # line 2779, 0-indexed
print('Before:', lines[i].rstrip())
lines[i] = '      html+=\'<button class="btn btn-ghost btn-sm" style="font-size:10px" onclick="switchDept(\'+JSON.stringify(d.code)+\').then(function(){switchTab(\\\"dashboard\\\")})">&#128065; View</button>\'\n'
print('After: ', lines[i].rstrip())

with open('index.html','w',encoding='utf-8') as f: f.writelines(lines)
