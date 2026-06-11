"""
Patch: Add Department Management Table (Add + Delete) to MPCP Admin Panel
Run from repo root: python patch_dept_mgmt.py
"""

content = open('app.py', encoding='utf-8').read()

# ── PATCH 1: Add department management section to ADMIN_HTML ─────────────────
# Insert before the closing </body> tag in ADMIN_HTML

old_audit = """        <thead><tr><th style="width:130px">Time</th><th style="width:28px"></th><th>Activity</th><th style="text-align:right">IP</th></tr></thead>"""

# Find the card that contains audit log - insert dept section before it
# First find the audit card header
old_audit_card = """<div class="card">
      <div class="card-head">"""

# Better target - find the audit log card specifically
audit_card_target = 'id="audit-tbody"'
audit_card_idx = content.find(audit_card_target)
if audit_card_idx == -1:
    print("❌ Could not find audit tbody - checking alternative...")
else:
    print(f"✅ Found audit tbody at index {audit_card_idx}")

# Find the card div that wraps the audit section (search backwards)
search_from = audit_card_idx
card_pos = content.rfind('<div class="card">', 0, search_from)
print(f"✅ Found audit card start at index {card_pos}")
audit_card_str = content[card_pos:card_pos+50]
print(f"   Context: {audit_card_str}")

DEPT_SECTION = """
      <!-- ── DEPARTMENT MANAGEMENT ─────────────────────────────────────── -->
      {% if current_user_role == 'master_admin' %}
      <div class="card">
        <div class="card-head">
          <h2>🏢 Department Management</h2>
          <button class="btn btn-primary" onclick="document.getElementById('add-dept-modal').classList.add('open')" style="font-size:10px">+ Add Department</button>
        </div>
        <table id="dept-table">
          <thead><tr>
            <th>Code</th>
            <th>Name</th>
            <th>Status</th>
            <th>Users</th>
            <th style="text-align:center">Actions</th>
          </tr></thead>
          <tbody id="dept-tbody">
            <tr><td colspan="5" style="text-align:center;padding:20px;color:#999">Loading...</td></tr>
          </tbody>
        </table>
      </div>

      <!-- Add Department Modal -->
      <div id="add-dept-modal" class="modal-overlay" onclick="if(event.target===this)this.classList.remove('open')">
        <div class="modal-box" style="max-width:400px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
            <h3 style="font-family:'Montserrat',sans-serif;font-size:13px;font-weight:700;text-transform:uppercase">Add Department</h3>
            <button onclick="document.getElementById('add-dept-modal').classList.remove('open')" style="background:none;border:none;font-size:18px;cursor:pointer;color:#999">&times;</button>
          </div>
          <div style="display:flex;flex-direction:column;gap:10px">
            <input id="new-dept-code" placeholder="Code (e.g. logistics)" style="padding:8px 12px;border:1.5px solid #DDD;border-radius:3px;font-size:12px;font-family:'Open Sans',sans-serif" onfocus="this.style.borderColor='#ED1C24'" onblur="this.style.borderColor='#DDD'">
            <input id="new-dept-name" placeholder="Full Name (e.g. Logistics Department)" style="padding:8px 12px;border:1.5px solid #DDD;border-radius:3px;font-size:12px;font-family:'Open Sans',sans-serif" onfocus="this.style.borderColor='#ED1C24'" onblur="this.style.borderColor='#DDD'">
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:6px">
              <button class="btn btn-ghost" onclick="document.getElementById('add-dept-modal').classList.remove('open')">Cancel</button>
              <button class="btn btn-primary" onclick="submitAddDept()">Create Department</button>
            </div>
            <div id="dept-msg" style="display:none;padding:8px 12px;border-radius:3px;font-size:11px;font-family:'Montserrat',sans-serif;font-weight:600"></div>
          </div>
        </div>
      </div>
      {% endif %}

"""

# ── PATCH 2: Add JS for department management ────────────────────────────────

DEPT_JS = """
// ── Department Management ──────────────────────────────────────────────────
function loadDepts() {
  var tb = document.getElementById('dept-tbody');
  if (!tb) return;
  fetch('/api/departments')
    .then(function(r){ return r.json(); })
    .then(function(depts) {
      if (!depts.length) {
        tb.innerHTML = "<tr><td colspan='5' style='text-align:center;padding:20px;color:#999'>No departments found</td></tr>";
        return;
      }
      tb.innerHTML = depts.map(function(d) {
        var statusBadge = d.active
          ? "<span style='color:#166534;background:#F0FDF4;border:1px solid #BBF7D0;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:700;font-family:Montserrat,sans-serif'>ACTIVE</span>"
          : "<span style='color:#991B1B;background:#FFF0F0;border:1px solid #FECACA;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:700;font-family:Montserrat,sans-serif'>INACTIVE</span>";
        return "<tr>"
          + "<td style='font-family:monospace;font-size:11px;color:#1D4ED8'>" + d.code + "</td>"
          + "<td style='font-weight:600'>" + d.name + "</td>"
          + "<td>" + statusBadge + "</td>"
          + "<td style='text-align:center'>" + (d.user_count||0) + "</td>"
          + "<td style='text-align:center'>"
          + "<button class='btn btn-danger' style='font-size:10px;background:#dc2626;color:#fff' onclick='deleteDept(\"" + d.id + "\",\"" + d.name + "\")'>&#128465; Delete</button>"
          + "</td>"
          + "</tr>";
      }).join('');
    })
    .catch(function(e){ tb.innerHTML = "<tr><td colspan='5' style='color:#ED1C24;padding:12px'>Error: "+e.message+"</td></tr>"; });
}

function deleteDept(id, name) {
  if (!confirm('Delete department "' + name + '"? This cannot be undone.')) return;
  fetch('/api/departments/' + id, { method: 'DELETE' })
    .then(function(r){ return r.json(); })
    .then(function(data) {
      if (data.ok) { loadDepts(); }
      else { alert('Error: ' + (data.error||'Unknown error')); }
    })
    .catch(function(e){ alert('Error: ' + e.message); });
}

function submitAddDept() {
  var code = document.getElementById('new-dept-code').value.trim();
  var name = document.getElementById('new-dept-name').value.trim();
  var msg  = document.getElementById('dept-msg');
  if (!code || !name) {
    msg.style.display='block'; msg.style.background='#FFF0F0'; msg.style.color='#ED1C24';
    msg.textContent = 'Code and name are required'; return;
  }
  fetch('/api/departments', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({code: code, name: name})
  })
  .then(function(r){ return r.json(); })
  .then(function(data) {
    if (data.id) {
      msg.style.display='block'; msg.style.background='#F0FDF4'; msg.style.color='#166534';
      msg.textContent = 'Department created successfully!';
      document.getElementById('new-dept-code').value='';
      document.getElementById('new-dept-name').value='';
      loadDepts();
      setTimeout(function(){ document.getElementById('add-dept-modal').classList.remove('open'); msg.style.display='none'; }, 1500);
    } else {
      msg.style.display='block'; msg.style.background='#FFF0F0'; msg.style.color='#ED1C24';
      msg.textContent = data.error||'Failed to create department';
    }
  })
  .catch(function(e){ msg.style.display='block'; msg.textContent='Error: '+e.message; });
}

// Load departments on page load
document.addEventListener('DOMContentLoaded', function(){ loadDepts(); });
"""

# Insert dept section before audit card
content = content[:card_pos] + DEPT_SECTION + content[card_pos:]
print("✅ Patch 1: Department management section inserted")

# Insert JS before closing </script> tag in ADMIN_HTML
# Find the last </script> before </body> in ADMIN_HTML
admin_end = content.rfind('</body>', content.find('ADMIN_HTML'))
script_end = content.rfind('</script>', 0, admin_end)
if script_end != -1:
    content = content[:script_end] + DEPT_JS + content[script_end:]
    print("✅ Patch 2: Department JS inserted")
else:
    print("❌ Patch 2 failed - </script> not found before </body>")

# ── Write file ───────────────────────────────────────────────────────────────
open('app.py', 'w', encoding='utf-8').write(content)
print("\n✅ All patches applied. Now run:")
print("   git add app.py")
print("   git commit -m 'feat: add department management with add/delete'")
print("   git push origin main")
