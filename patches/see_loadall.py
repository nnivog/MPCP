with open('index.html', 'r', encoding='utf-8') as f:
    txt = f.read()

idx = txt.find('Promise.all')
print(txt[idx-100:idx+600])
