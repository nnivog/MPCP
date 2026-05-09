with open('index.html','r',encoding='utf-8') as f: lines=f.readlines()

for i,l in enumerate(lines):
    if 'onmouseover="this.style.background=' in l and 'dc2626' in l:
        print(f'Found at line {i+1}')
        lines[i] = "    + '<a href=\"/logout\" title=\"Logout\" style=\"display:flex;align-items:center;justify-content:center;width:28px;height:28px;background:#1a2d4a;border-radius:8px;color:#f87171;font-size:14px;text-decoration:none;font-weight:700;border:1px solid #2d4a6b;flex-shrink:0\" id=\"logout-btn\">&#10148;</a>'\n"
        print(f'Fixed  at line {i+1}')
        break

with open('index.html','w',encoding='utf-8') as f: f.writelines(lines)
print('Done')
