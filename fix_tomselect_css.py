from pathlib import Path
import shutil
shutil.copy('index.html','index.html.bak10')
html = Path('index.html').read_text(encoding='utf-8')

old = """/* Tom Select theme overrides to match MPCP dark UI */
.ts-wrapper.form-select{padding:0!important}
.ts-control{background:var(--surface)!important;border:1px solid var(--border)!important;color:var(--text)!important;border-radius:6px!important;font-size:12px!important;min-height:32px!important;padding:4px 8px!important}
.ts-dropdown{background:var(--surface)!important;border:1px solid var(--border)!important;color:var(--text)!important;font-size:12px!important;z-index:9999!important}
.ts-dropdown .option{padding:6px 10px!important;color:var(--text)!important}
.ts-dropdown .option:hover,.ts-dropdown .option.active{background:#ED1C2420!important;color:#ED1C24!important}
.ts-dropdown .option.selected{background:#ED1C2430!important}
.ts-wrapper .ts-control input{color:var(--text)!important;font-size:12px!important}
.ts-dropdown .ts-dropdown-content{max-height:200px!important}"""

new = """/* Tom Select theme overrides to match MPCP dark UI */
.ts-wrapper{padding:0!important}
.ts-wrapper.form-select{padding:0!important}
.ts-control{background:#0f1a2e!important;border:1px solid #1e3a5f!important;color:#e2e8f0!important;border-radius:6px!important;font-size:12px!important;min-height:32px!important;padding:4px 8px!important;box-shadow:none!important}
.ts-control input{color:#e2e8f0!important;background:transparent!important;font-size:12px!important}
.ts-control input::placeholder{color:#64748b!important}
.ts-dropdown{background:#0f1a2e!important;border:1px solid #1e3a5f!important;color:#e2e8f0!important;font-size:12px!important;z-index:9999!important;box-shadow:0 8px 24px rgba(0,0,0,.4)!important}
.ts-dropdown .option{padding:7px 12px!important;color:#cbd5e1!important;border-bottom:1px solid rgba(30,58,95,.2)!important}
.ts-dropdown .option:hover{background:rgba(237,28,36,.1)!important;color:#fff!important}
.ts-dropdown .option.active{background:rgba(237,28,36,.15)!important;color:#fff!important}
.ts-dropdown .option.selected{background:rgba(237,28,36,.2)!important;color:#ED1C24!important}
.ts-dropdown-content{max-height:220px!important;overflow-y:auto!important}
.ts-dropdown .no-results{color:#64748b!important;padding:8px 12px!important}"""

if old in html:
    Path('index.html').write_text(html.replace(old, new, 1), encoding='utf-8')
    print('v Tom Select CSS updated')
else:
    print('x not matched — searching for partial...')
    idx = html.find('Tom Select theme')
    if idx != -1:
        print('Found at:', idx)
        print(repr(html[idx:idx+300]))
