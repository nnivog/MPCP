"""
Run this script ONCE from your MPCP folder in Git Bash:
    python apply_updates.py

It replaces app.py and index.html with the fully patched versions,
then stages and commits everything ready to push.
"""
import os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))

def run(cmd):
    r = subprocess.run(cmd, shell=True, cwd=HERE)
    if r.returncode != 0:
        print(f"ERROR running: {cmd}")
        sys.exit(1)

print("Applying updates...")

# The patched files sit next to this script
shutil.copy(os.path.join(HERE, 'app.py'),     os.path.join(HERE, 'app.py'))
shutil.copy(os.path.join(HERE, 'index.html'), os.path.join(HERE, 'index.html'))

# Quick syntax check
r = subprocess.run(
    [sys.executable, '-c',
     "import ast; ast.parse(open('app.py', encoding='utf-8').read()); print('app.py syntax OK')"],
    cwd=HERE
)
if r.returncode != 0:
    print("Syntax error in app.py — aborting")
    sys.exit(1)

run('git add app.py index.html')
run('git commit -m "feat+fix: multi-sector/location model, cascade save, sector edit, api errors"')
print("\nDone! Now run:  git push origin main")
