with open('index.html', 'r', encoding='utf-8') as f:
    txt = f.read()
print("Lines:", len(txt.splitlines()))
print("</script> count:", txt.count('</script>'))
print("renderLocations:", txt.count('renderLocations'))
print("loadAll present:", 'async function loadAll' in txt or 'function loadAll' in txt)
print("Promise.all present:", 'Promise.all' in txt)
