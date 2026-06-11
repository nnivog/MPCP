lines = open('index.html', encoding='utf-8').read().split('\n')

for i, line in enumerate(lines):
    if 'openDeptForm(' in line and 'Edit</button>' in line and 'html+=' in line:
        lines[i] = "      html+='<button class=\"btn btn-ghost btn-sm\" style=\"font-size:10px\" data-action=\"edit\" data-id=\"'+d.id+'\" data-name=\"'+encodeURIComponent(d.name)+'\" data-active=\"'+d.active+'\">&#9998; Edit</button>'"
        print(f'Fixed Edit button at line {i+1}')

    if 'deleteDept(' in line and 'Delete</button>' in line and 'html+=' in line:
        lines[i] = "      html+='<button class=\"btn btn-ghost btn-sm\" style=\"font-size:10px;color:#dc2626;border-color:#fca5a5\" data-action=\"delete\" data-id=\"'+d.id+'\" data-name=\"'+encodeURIComponent(d.name)+'\">&#128465; Delete</button>'"
        print(f'Fixed Delete button at line {i+1}')

content = '\n'.join(lines)

# Add event delegation handler inside renderDepartments, after the innerHTML assignment
old = "    }).catch(function(){q('#master-content').innerHTML=html})\n  })\n}\n\nfunction deleteDept"
new = """    }).catch(function(){q('#master-content').innerHTML=html})
    // Event delegation for dept buttons
    setTimeout(function(){
      var mc = q('#master-content')
      if(mc) mc.addEventListener('click', function handler(e){
        var btn = e.target.closest('[data-action]')
        if(!btn) return
        var action = btn.dataset.action
        var id = btn.dataset.id
        var name = decodeURIComponent(btn.dataset.name)
        var active = btn.dataset.active
        if(action==='delete') deleteDept(id, name)
        if(action==='edit') openDeptForm(id, name, active==='1')
        mc.removeEventListener('click', handler)
      },{ once: false })
    }, 100)
  })
}

function deleteDept"""

if old in content:
    content = content.replace(old, new)
    print('Added event delegation handler')
else:
    print('Event delegation target not found - checking...')
    idx = content.find("}).catch(function(){q('#master-content').innerHTML=html})")
    print(f'catch block at char: {idx}')

open('index.html', 'w', encoding='utf-8').write(content)
print('Done')
