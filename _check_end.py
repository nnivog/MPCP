with open('app.py','r',encoding='utf-8') as f: c=f.read()

idx = c.find('ADMIN_HTML = """')
end = c.rfind('"""', idx+20)
print('ADMIN_HTML ends at line:', c[:end].count(chr(10)))
print('Last 150 chars before end:', repr(c[end-150:end+5]))