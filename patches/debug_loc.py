import urllib.request, json

base = 'http://localhost:5050'

# Test GET locations
try:
    res = urllib.request.urlopen(base + '/api/locations')
    data = json.loads(res.read())
    print("GET /api/locations OK — count:", len(data))
except Exception as e:
    print("GET /api/locations FAILED:", e)

# Test POST location
try:
    payload = json.dumps({
        'code': 'TEST-01',
        'name': 'Test Location',
        'address': '123 Test St',
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
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    print("POST /api/locations OK:", data)
except Exception as e:
    print("POST /api/locations FAILED:", e)
