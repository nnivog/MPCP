with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
print("\n--- FIRST 30 LINES ---")
for i, l in enumerate(lines[:30], 1):
    print(f"{i:4d} | {l}", end='')

print("\n--- LAST 30 LINES ---")
for i, l in enumerate(lines[-30:], len(lines)-29):
    print(f"{i:4d} | {l}", end='')
