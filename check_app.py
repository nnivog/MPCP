import ast, sys

with open('app.py', 'r', encoding='utf-8') as f:
    source = f.read()

try:
    ast.parse(source)
    print("app.py syntax: OK")
except SyntaxError as e:
    print("SYNTAX ERROR at line", e.lineno)
    print("Message:", e.msg)
    print("Text:", e.text)
    
    # Show context around the error
    lines = source.splitlines()
    start = max(0, e.lineno - 5)
    end   = min(len(lines), e.lineno + 5)
    print("\nContext:")
    for i, line in enumerate(lines[start:end], start=start+1):
        marker = ">>>" if i == e.lineno else "   "
        print(f"{marker} {i:4d} | {line}")
