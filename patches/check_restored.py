with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
print(f"Total lines: {len(lines)}")
print("First line:", lines[0].strip())
print("Last line:", lines[-1].strip())
