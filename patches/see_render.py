with open('index.html', 'r', encoding='utf-8') as f:
    txt = f.read()

# Find the full renderCurrent function
idx = txt.find('function renderCurrent')
print("=== renderCurrent ===")
print(txt[idx:idx+500])

# Find switchTab function
idx2 = txt.find('function switchTab')
print("\n=== switchTab ===")
print(txt[idx2:idx2+400])

# See what API url the locations post is hitting
idx3 = txt.find('api.post')
while idx3 != -1:
    line = txt[idx3:idx3+80]
    if 'locat' in line.lower():
        print("\n=== locations api.post call ===")
        print(txt[idx3-200:idx3+200])
    idx3 = txt.find('api.post', idx3+1)
