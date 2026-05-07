import urllib.request

url = 'https://raw.githubusercontent.com/nnivog/MPCP/main/app.py'
print("Downloading original app.py from GitHub...")
urllib.request.urlretrieve(url, 'app.py')

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f"Downloaded OK — {len(lines)} lines")
