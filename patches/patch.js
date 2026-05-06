/**
 * MPCP patch.js  v2.4  —  ZERO interference with original app
 *
 * Rules:
 *   1. NEVER redefine or call loadAll / renderMPs / renderCPs / openModal / switchMaster
 *   2. Sectors & Locations fetch their own data independently
 *   3. Checkboxes are injected via MutationObserver AFTER original renders — read-only DOM changes
 *   4. All new functions prefixed _p_ or on window._p* to avoid collision
 *
 * Install: add  <script src="patch.js"></script>  before </body> in index.html
 */
(function () {
  'use strict';

  /* ── boot: wait for S and api to exist ─────────────────────────────── */
  function _boot() {
    if (typeof S === 'undefined' || typeof api === 'undefined') {
      return setTimeout(_boot, 80);
    }
    /* Extend S with new keys only */
    if (!S.sectors)   S.sectors   = [];
    if (!S.locations) S.locations = [];

    _addMasterTabs();
    _watchMasterContent();
    _watchDataContent();
    _fetchSectorsLocations();   // initial silent load
  }
  setTimeout(_boot, 80);

  /* ── load sectors & locations independently (never touches S.mps etc.) */
  async function _fetchSectorsLocations() {
    try {
      const [sec, loc] = await Promise.all([
        fetch('/api/sectors').then(r => r.json()),
        fetch('/api/locations').then(r => r.json()),
      ]);
      S.sectors   = sec;
      S.locations = loc;
    } catch (e) { /* silently ignore if server not ready */ }
  }

  /* ══════════════════════════════════════════════════════════════════════
     PART A — Add Sectors / Locations tabs to Master Setup
     ══════════════════════════════════════════════════════════════════════ */
  function _addMasterTabs() {
    const bar = document.getElementById('master-tabs');
    if (!bar || bar.dataset.pv4) return;
    bar.dataset.pv4 = '1';

    [['sectors', '🏷 Sectors'], ['locations', '📍 Locations']].forEach(([key, label]) => {
      const btn = document.createElement('button');
      btn.className   = 'sub-tab';
      btn.textContent = label;
      btn.addEventListener('click', function () {
        /* deactivate all tabs (original + new) */
        bar.querySelectorAll('.sub-tab').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        /* blank master-content so MutationObserver knows it changed */
        const mc = document.getElementById('master-content');
        if (mc) mc.innerHTML = '<div class="spinner"></div>';
        /* then render */
        if (key === 'sectors')   _renderSectors();
        if (key === 'locations') _renderLocations();
      });
      bar.appendChild(btn);
    });
  }

  /* ══════════════════════════════════════════════════════════════════════
     PART B — MutationObserver: inject checkboxes into original MP/CP tables
     Completely passive — only adds DOM nodes, never replaces innerHTML
     ══════════════════════════════════════════════════════════════════════ */
  const _mpSel = new Set();
  const _cpSel = new Set();

  function _watchMasterContent() {
    const mc = document.getElementById('master-content');
    if (!mc) return;
    new MutationObserver(function () {
      /* Use rAF so the original render finishes painting first */
      requestAnimationFrame(function () {
        _tryInjectMP();
        _tryInjectCP();
      });
    }).observe(mc, { childList: true });
  }

  function _activeTabText() {
    const a = document.querySelector('#master-tabs .sub-tab.active');
    return a ? a.textContent : '';
  }

  function _tryInjectMP() {
    if (!_activeTabText().includes('Managing') &&
        !_activeTabText().includes('Points')) return;
    const mc    = document.getElementById('master-content');
    const table = mc && mc.querySelector('table');
    if (!table || table.dataset.pmpChk) return;
    table.dataset.pmpChk = '1';
    _mpSel.clear();
    _injectIntoTable(table, 'openMPForm', _mpSel, 'pmp-bar', 'pmp-cnt',
                     '_pDeleteMPs', '_pClearMP');
  }

  function _tryInjectCP() {
    if (!_activeTabText().includes('Checking')) return;
    const mc    = document.getElementById('master-content');
    const table = mc && mc.querySelector('table');
    if (!table || table.dataset.pcpChk) return;
    table.dataset.pcpChk = '1';
    _cpSel.clear();
    _injectIntoTable(table, 'openCPForm', _cpSel, 'pcp-bar', 'pcp-cnt',
                     '_pDeleteCPs', '_pClearCP');
  }

  function _injectIntoTable(table, openFn, selSet, barId, cntId, deleteFn, clearFn) {
    /* header th */
    const hrow = table.querySelector('thead tr');
    if (hrow && !hrow.querySelector('.p-chk-th')) {
      const th = document.createElement('th');
      th.className = 'p-chk-th';
      th.style.width = '34px';
      const ca = _chk('p-chk-all', '', function () {
        table.querySelectorAll('.p-row-chk').forEach(c => {
          c.checked = this.checked;
          this.checked ? selSet.add(c.dataset.id) : selSet.delete(c.dataset.id);
        });
        _bar(barId, cntId, selSet);
      });
      th.appendChild(ca);
      hrow.insertBefore(th, hrow.firstChild);
    }

    /* body rows */
    table.querySelectorAll('tbody tr').forEach(function (tr) {
      if (tr.querySelector('.p-row-chk')) return;
      /* find button/link with openMPForm / openCPForm in onclick */
      const btn = [...tr.querySelectorAll('[onclick]')]
        .find(b => b.getAttribute('onclick').includes(openFn));
      if (!btn) return;
      const m = btn.getAttribute('onclick').match(/'([^']+)'/);
      if (!m) return;
      const id = m[1];
      const td = document.createElement('td');
      const c  = _chk('p-row-chk', id, function () {
        this.checked ? selSet.add(id) : selSet.delete(id);
        _bar(barId, cntId, selSet);
      });
      td.appendChild(c);
      tr.insertBefore(td, tr.firstChild);
    });

    /* bulk action bar — insert before tbl-wrap */
    const mc = document.getElementById('master-content');
    if (mc && !mc.querySelector('#' + barId)) {
      const tblWrap = table.closest('.tbl-wrap') || table.parentNode;
      const bar = document.createElement('div');
      bar.id = barId;
      bar.style.cssText =
        'display:none;background:#fef3c7;border:1.5px solid #fcd34d;' +
        'border-radius:10px;padding:9px 14px;margin-bottom:10px;' +
        'align-items:center;gap:10px;flex-wrap:wrap';
      bar.innerHTML =
        '<span id="' + cntId + '" style="font-weight:700;font-size:12px;' +
        'color:#92400e;font-family:Syne,sans-serif;"></span>' +
        '<button style="background:#dc2626;color:#fff;border:none;padding:4px 13px;' +
        'border-radius:7px;font-size:11px;font-weight:700;cursor:pointer;' +
        'font-family:Syne,sans-serif" onclick="window[\''+deleteFn+'\']()">🗑 Delete Selected</button>' +
        '<button style="background:transparent;border:1.5px solid #e2e6ef;color:#6b7a99;' +
        'padding:4px 11px;border-radius:7px;font-size:11px;font-weight:700;cursor:pointer" ' +
        'onclick="window[\''+clearFn+'\']()">✕ Clear</button>';
      tblWrap.parentNode.insertBefore(bar, tblWrap);
    }
  }

  function _chk(cls, id, handler) {
    const c = document.createElement('input');
    c.type = 'checkbox';
    c.className = cls;
    if (id) c.dataset.id = id;
    c.style.cssText = 'width:14px;height:14px;accent-color:#1d4ed8;cursor:pointer;vertical-align:middle';
    c.addEventListener('change', handler);
    return c;
  }

  function _bar(barId, cntId, selSet) {
    const bar = document.getElementById(barId);
    const cnt = document.getElementById(cntId);
    if (!bar) return;
    bar.style.display = selSet.size > 0 ? 'flex' : 'none';
    if (cnt) cnt.textContent = selSet.size + ' selected';
  }

  /* Bulk delete — exposed on window so inline onclick works */
  window._pDeleteMPs = async function () {
    const ids = [..._mpSel];
    if (!ids.length) return;
    if (!confirm('Delete ' + ids.length + ' Managing Point(s)?\nLinked CPs will be unlinked.')) return;
    const r = await fetch('/api/mps/bulk_delete', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ids})
    }).then(x => x.json());
    _mpSel.clear();
    if (typeof toast === 'function') toast('Deleted ' + r.deleted + ' MP(s)', 'ok');
    /* Let original app refresh — call its switchMaster via the tab click */
    const mpTab = document.querySelector('#master-tabs .sub-tab');
    if (mpTab) mpTab.click();
  };
  window._pClearMP = function () {
    _mpSel.clear();
    document.querySelectorAll('.p-row-chk,.p-chk-all').forEach(c => c.checked = false);
    _bar('pmp-bar','pmp-cnt',_mpSel);
  };

  window._pDeleteCPs = async function () {
    const ids = [..._cpSel];
    if (!ids.length) return;
    if (!confirm('Delete ' + ids.length + ' Checking Point(s)?')) return;
    const r = await fetch('/api/cps/bulk_delete', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ids})
    }).then(x => x.json());
    _cpSel.clear();
    if (typeof toast === 'function') toast('Deleted ' + r.deleted + ' CP(s)', 'ok');
    const cpTab = document.querySelectorAll('#master-tabs .sub-tab')[1];
    if (cpTab) cpTab.click();
  };
  window._pClearCP = function () {
    _cpSel.clear();
    document.querySelectorAll('.p-row-chk,.p-chk-all').forEach(c => c.checked = false);
    _bar('pcp-bar','pcp-cnt',_cpSel);
  };

  /* ══════════════════════════════════════════════════════════════════════
     PART C — Sectors CRUD
     ══════════════════════════════════════════════════════════════════════ */
  async function _renderSectors() {
    await _fetchSectorsLocations();
    const mc = document.getElementById('master-content');
    if (!mc) return;
    const secs = S.sectors;
    mc.innerHTML =
      '<div class="section-head"><div><h2>Sectors / Departments</h2>' +
      '<p>' + secs.length + ' sectors — employee grouping & colour coding</p></div>' +
      '<button class="btn btn-primary btn-sm" onclick="window._pOpenSectorForm()">+ Add Sector</button></div>' +
      (secs.length === 0
        ? '<p class="text-muted text-sm" style="margin-top:12px">No sectors yet. Add one above.</p>'
        : '<div class="grid-auto" style="margin-top:4px">' +
          secs.map(function(s) {
            return '<div class="card" style="border-left:4px solid '+_e(s.color)+'">' +
              '<div class="card-body" style="padding:14px 16px">' +
              '<div class="flex items-center gap-8 mb-8">' +
              '<span style="width:13px;height:13px;border-radius:50%;background:'+_e(s.color)+';display:inline-block;flex-shrink:0"></span>' +
              '<span class="font-black" style="font-size:13px">'+_e(s.name)+'</span>' +
              '<span class="badge badge-blue" style="margin-left:auto">'+_e(s.code)+'</span></div>' +
              '<p class="text-xs text-muted" style="margin-bottom:12px;min-height:14px">'+(_e(s.description)||'—')+'</p>' +
              '<div class="flex gap-6">' +
              '<button class="btn btn-ghost btn-sm flex-1" onclick="window._pOpenSectorForm(\''+s.id+'\')">✏ Edit</button>' +
              '<button class="btn btn-danger btn-sm" onclick="window._pDeleteSector(\''+s.id+'\',\''+_e(s.name)+'\')">🗑</button>' +
              '</div></div></div>';
          }).join('') + '</div>');
  }

  window._pOpenSectorForm = function(sid) {
    var s = sid ? (S.sectors||[]).find(function(x){return x.id===sid;}) : null;
    _pMod(s ? 'Edit Sector':'Add Sector',
      '<div class="form-group"><label class="form-label">Code *</label>' +
      '<input class="form-input" id="___sc" value="'+_e(s&&s.code||'')+'" placeholder="e.g. Vehicle (no spaces)"></div>' +
      '<div class="form-group"><label class="form-label">Name *</label>' +
      '<input class="form-input" id="___sn" value="'+_e(s&&s.name||'')+'" placeholder="e.g. Vehicle Operations"></div>' +
      '<div class="form-group"><label class="form-label">Colour</label>' +
      '<div style="display:flex;gap:8px;align-items:center">' +
      '<input type="color" id="___scol" value="'+(s&&s.color||'#475569')+'" ' +
      'style="width:44px;height:36px;border:1.5px solid var(--border);border-radius:8px;cursor:pointer;padding:2px" ' +
      'oninput="document.getElementById(\'___scolh\').value=this.value">' +
      '<input class="form-input" id="___scolh" value="'+_e(s&&s.color||'#475569')+'" ' +
      'oninput="document.getElementById(\'___scol\').value=this.value"></div></div>' +
      '<div class="form-group"><label class="form-label">Description</label>' +
      '<input class="form-input" id="___sd" value="'+_e(s&&s.description||'')+'" placeholder="Optional"></div>',
      s ? 'Save Changes':'Create Sector', 'window._pSaveSector("'+(sid||'')+'")');
  };

  window._pSaveSector = async function(sid) {
    var d = {
      code: document.getElementById('___sc').value.trim(),
      name: document.getElementById('___sn').value.trim(),
      color: document.getElementById('___scolh').value.trim() || document.getElementById('___scol').value,
      description: document.getElementById('___sd').value.trim()
    };
    if (!d.code||!d.name) { if(typeof toast==='function') toast('Code and Name required','err'); return; }
    var res = await fetch(sid?'/api/sectors/'+sid:'/api/sectors',
      {method:sid?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
    if (!res.ok) { if(typeof toast==='function') toast('Save failed','err'); return; }
    _pCloseMod();
    if(typeof toast==='function') toast(sid?'Sector updated':'Sector created','ok');
    await _renderSectors();
  };

  window._pDeleteSector = async function(sid, name) {
    if (!confirm('Delete sector "'+name+'"?\nEmployees will have their department cleared.')) return;
    await fetch('/api/sectors/'+sid,{method:'DELETE'});
    if(typeof toast==='function') toast('Sector deleted','ok');
    await _renderSectors();
  };

  /* ══════════════════════════════════════════════════════════════════════
     PART D — Locations CRUD
     ══════════════════════════════════════════════════════════════════════ */
  async function _renderLocations() {
    await _fetchSectorsLocations();
    const mc = document.getElementById('master-content');
    if (!mc) return;
    const locs = S.locations;
    var rows = locs.length === 0
      ? '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:24px">No locations yet.</td></tr>'
      : locs.map(function(l){
          var sec=(S.sectors||[]).find(function(s){return s.id===l.sector_id;});
          return '<tr>'+
            '<td><span class="ref-badge">'+_e(l.code)+'</span></td>'+
            '<td class="font-bold">'+_e(l.name)+'</td>'+
            '<td class="text-muted text-xs">'+(_e(l.address)||'—')+'</td>'+
            '<td>'+(sec?'<span class="dept-badge" style="background:'+_e(sec.color)+'">'+_e(sec.name)+'</span>':'<span class="text-muted text-xs">—</span>')+'</td>'+
            '<td>'+(l.active?'<span class="badge badge-c">Active</span>':'<span class="badge badge-nc">Inactive</span>')+'</td>'+
            '<td><div style="display:flex;gap:6px">'+
            '<button class="btn-icon" onclick="window._pOpenLocForm(\''+l.id+'\')" title="Edit">✏</button>'+
            '<button class="btn-icon" style="color:var(--red)" onclick="window._pDeleteLoc(\''+l.id+'\',\''+_e(l.name)+'\')" title="Delete">🗑</button>'+
            '</div></td></tr>';
        }).join('');

    mc.innerHTML =
      '<div class="section-head"><div><h2>Locations</h2>'+
      '<p>'+locs.length+' locations — depots, border points, warehouses</p></div>'+
      '<button class="btn btn-primary btn-sm" onclick="window._pOpenLocForm()">+ Add Location</button></div>'+
      '<div class="tbl-wrap"><table><thead><tr>'+
      '<th>Code</th><th>Name</th><th>Address</th><th>Sector</th><th>Status</th><th>Actions</th>'+
      '</tr></thead><tbody>'+rows+'</tbody></table></div>';
  }

  window._pOpenLocForm = function(lid) {
    var l = lid ? (S.locations||[]).find(function(x){return x.id===lid;}) : null;
    var secOpts = (S.sectors||[]).map(function(s){
      return '<option value="'+s.id+'"'+(l&&l.sector_id===s.id?' selected':'')+'>'+_e(s.name)+'</option>';
    }).join('');
    _pMod(l?'Edit Location':'Add Location',
      '<div class="form-grid-2">'+
      '<div class="form-group"><label class="form-label">Code *</label>'+
      '<input class="form-input" id="___lc" value="'+_e(l&&l.code||'')+'" placeholder="e.g. BRT-BP"></div>'+
      '<div class="form-group"><label class="form-label">Sector</label>'+
      '<select class="form-select" id="___ls"><option value="">— None —</option>'+secOpts+'</select></div></div>'+
      '<div class="form-group"><label class="form-label">Location Name *</label>'+
      '<input class="form-input" id="___ln" value="'+_e(l&&l.name||'')+'" placeholder="e.g. Birgunj Border Point"></div>'+
      '<div class="form-group"><label class="form-label">Address / District</label>'+
      '<input class="form-input" id="___la" value="'+_e(l&&l.address||'')+'" placeholder="e.g. Birgunj, Parsa"></div>'+
      '<div class="form-group"><label class="form-label">Status</label>'+
      '<select class="form-select" id="___lact">'+
      '<option value="1"'+(l&&l.active===0?'':' selected')+'>Active</option>'+
      '<option value="0"'+(l&&l.active===0?' selected':'')+'>Inactive</option></select></div>',
      l?'Save Changes':'Create Location', 'window._pSaveLoc("'+(lid||'')+'")');
  };

  window._pSaveLoc = async function(lid) {
    var d = {
      code:      document.getElementById('___lc').value.trim(),
      name:      document.getElementById('___ln').value.trim(),
      address:   document.getElementById('___la').value.trim(),
      sector_id: document.getElementById('___ls').value,
      active:    document.getElementById('___lact').value==='1'
    };
    if (!d.code||!d.name) { if(typeof toast==='function') toast('Code and Name required','err'); return; }
    var res = await fetch(lid?'/api/locations/'+lid:'/api/locations',
      {method:lid?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
    if (!res.ok) { if(typeof toast==='function') toast('Save failed','err'); return; }
    _pCloseMod();
    if(typeof toast==='function') toast(lid?'Location updated':'Location created','ok');
    await _renderLocations();
  };

  window._pDeleteLoc = async function(lid, name) {
    if (!confirm('Delete location "'+name+'"?')) return;
    await fetch('/api/locations/'+lid,{method:'DELETE'});
    if(typeof toast==='function') toast('Location deleted','ok');
    await _renderLocations();
  };

  /* ══════════════════════════════════════════════════════════════════════
     PART E — Private modal  (uses existing DOM — NO override of openModal)
     ══════════════════════════════════════════════════════════════════════ */
  function _pMod(title, body, btnLabel, btnFn) {
    var o  = document.getElementById('modal-overlay');
    var mT = document.getElementById('modal-title');
    var mB = document.getElementById('modal-body');
    var mF = document.getElementById('modal-foot');
    if (!o) return;
    mT.textContent = title;
    mB.innerHTML   = body;
    mF.innerHTML   =
      '<button class="btn btn-ghost" onclick="window._pCloseMod()">Cancel</button>' +
      '<button class="btn btn-primary" onclick="'+btnFn+'">'+btnLabel+'</button>';
    o.classList.remove('hidden');
  }
  window._pCloseMod = function() {
    var o = document.getElementById('modal-overlay');
    if (o) o.classList.add('hidden');
  };

  /* ══════════════════════════════════════════════════════════════════════
     PART F — Smart sample banner (data-content observer)
     ══════════════════════════════════════════════════════════════════════ */
  function _watchDataContent() {
    var dc = document.getElementById('data-content');
    if (!dc) return;
    new MutationObserver(function(){
      requestAnimationFrame(_patchSampleBanner);
    }).observe(dc, {childList:true, subtree:true});
  }

  function _patchSampleBanner() {
    document.querySelectorAll('.sample-files').forEach(function(div){
      if (div.dataset.pv4) return;
      div.dataset.pv4 = '1';
      div.innerHTML = [
        {key:'employees', label:'👥 Employees ('+(S.employees||[]).length+')', ext:'xlsx'},
        {key:'mps',       label:'🎯 Managing Points ('+(S.mps||[]).length+')', ext:'xlsx'},
        {key:'cps',       label:'✅ Checking Points ('+(S.cps||[]).length+')', ext:'xlsx'},
        {key:'sectors',   label:'🏷 Sectors ('+(S.sectors||[]).length+')',     ext:'xlsx'},
        {key:'locations', label:'📍 Locations ('+(S.locations||[]).length+')', ext:'xlsx'},
        {key:'perf',      label:'📊 Performance Template',                     ext:'csv'},
      ].map(function(f){
        return '<a class="sample-link" href="/api/samples/'+f.key+'" download>'+
               f.label+' <span class="text-xxs" style="opacity:.6">.'+f.ext+'</span></a>';
      }).join('');
    });
  }

  /* ── util ───────────────────────────────────────────────────────────── */
  function _e(s) {
    return String(s||'')
      .replace(/&/g,'&amp;').replace(/</g,'&lt;')
      .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }

})();
