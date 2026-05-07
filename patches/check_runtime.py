import subprocess
result = subprocess.run(['python', 'app.py'], capture_output=True, text=True, timeout=10)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
