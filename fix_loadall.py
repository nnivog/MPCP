with open('index.html', 'r', encoding='utf-8') as f:
    txt = f.read()

# Find the exact current loadAll lines and print them for diagnosis
import re
match = re.search(r'(const \[.*?\] = await Promise\.all\(\[.*?\]\))', txt, re.DOTALL)
if match:
    print("FOUND Promise.all block:")
    print(match.group(1))
else:
    print("Promise.all block NOT found - searching nearby...")
    idx = txt.find('Promise.all')
    if idx > -1:
        print(txt[idx-50:idx+300])
