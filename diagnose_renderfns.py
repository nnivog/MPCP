import pathlib, re

raw  = pathlib.Path("index.html").read_bytes()
html = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n").decode("utf-8")
lines = html.splitlines()

def show(label, lineno, count):
    end = min(len(lines), lineno + count)
    print(f"\n=== {label} (lines {lineno+1}–{end}) ===")
    print(repr("\n".join(lines[lineno:end])))

# Find each render function and show first 8 lines
targets = {
    "renderMPs":            "function renderMPs()",
    "renderCPs":            "function renderCPs()",
    "renderLinks":          "function renderLinks()",
    "renderCascadeBuilder": "function renderCascadeBuilder()",
    "renderAssignPanel":    "function renderAssignPanel()",
    "renderOrgTab":         "function renderOrgTab()",
    "renderMPCP":           "function renderMPCP()",
    "switchMPCP":           "function switchMPCP(",
}

for label, needle in targets.items():
    for i, ln in enumerate(lines):
        if needle in ln:
            show(label, i, 12)
            break
    else:
        print(f"\n=== {label} — NOT FOUND ===")
