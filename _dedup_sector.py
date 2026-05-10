with open('app.py','r',encoding='utf-8') as f: c=f.read()

# Find both occurrences
idx1 = c.find("@app.route('/api/analytics/by_sector')")
idx2 = c.find("@app.route('/api/analytics/by_sector')", idx1+10)

if idx2 > 0:
    # Remove the second duplicate - find its end
    end2 = c.find("\n@app.route", idx2+10)
    if end2 < 0:
        end2 = c.find("\n\ndef ", idx2+10)
    c = c[:idx2] + c[end2:]
    print(f'Removed duplicate at {idx2}, kept first at {idx1}')
else:
    print('No duplicate found')

with open('app.py','w',encoding='utf-8') as f: f.write(c)
