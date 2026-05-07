with open('app.py', 'r', encoding='utf-8') as f:
    txt = f.read()

idx = txt.find("@app.route('/api/locations'")
print(txt[idx:idx+1500])
