import urllib.request, json, urllib.error

base = 'http://localhost:5050'

payload = json.dumps({
    'code': 'TEST-01',
    'name': 'Test Branch',
    'address': 'Kathmandu',
    'type': 'Branch',
    'dept': 'Ops',
    'active': True,
    'emp_ids': []
}).encode('utf-8')

req = urllib.request.Request(
    base + '/api/locations',
    data=payload,
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    res = urllib.request.urlopen(req)
    print("SUCCESS:", json.loads(res.read()))
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code, e.reason)
    print("Body:", e.read().decode())
except Exception as e:
    print("ERROR:", e)
