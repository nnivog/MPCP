/**
 * MPCP patch.js  v2.3  —  NON-INVASIVE
 *
 * Strategy: NEVER redefine renderMPs / renderCPs / openModal / switchMaster.
 * Instead:
 *   - MutationObserver watches #master-content and INJECTS checkboxes
 *     into whatever table the original code renders.
 *   - Sectors / Locations use completely separate _p_-prefixed functions.
 *   - loadAll is extended by chaining, not overriding.
 *   - Modal uses existing DOM ids but with string onclick, not fn.toString().
 *
 * ONE LINE to add before </body> in index.html:
 *   <script src="patch.js"></script>
 */

(function () {
  'use strict';

  function _boot() {
    if (typeof S === 'undefined' || typeof loadAll === 'undefined') {
      return setTimeout(_boot, 100);
    }
    S.sectors   = [];
    S.locations = [];
    _hookLoadAll();
    _addMasterTabs();
    _observeMasterContent();
    _observeSampleBanner();
  }
  setTimeout(_boot, 50);

  /* ── 1  Extend loadAll ─────────────────────────────────────────────── */
  function _hookLoadAll() {
    const _orig = window.loadAll;
    window.loadAll = async function () {
      await _orig();
      const [sec, loc] = await Promise.all([
        fetch('/api/sectors').then(r => r.json()),
        fetch('/api/locations').then(r => r.json()),
      ]);
      S.sectors   = sec;
      S.locations = loc;
      _refreshSampleBanner();
    };
    window.loadAll();
  }

  /* ── 2  New Master tabs ────────────────────────────────────────────── */
  function _addMasterTabs() {
    const bar = document.getElementById('master-tabs');
    if (!bar || bar.dataset.pPatched) return;
    bar.dataset.pPatched = '1';
    [['sectors','🏷 Sectors / Depts'], ['locations','📍 Locations']].forEach(([key, label]) => {
      const btn = document.createElement('button');
      btn.className = 'sub-tab';
      btn.textContent = label;
      btn.dataset.pKey = key;
      btn.addEventListener('click', () => {
        bar.querySelectorAll('.sub-tab').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        key === 'sectors' ? _renderSectors() : _renderLocations();
      });
      bar.appendChild(btn);
    });
  }

  /* ── 3  MutationObserver → inject checkboxes ───────────────────────── */
  const _sel = { mps: new Set(), cps: new Set() };

  function _observeMasterContent() {
    const target = document.getElementById('master-content');
    if (!target) return;
    new MutationObserver(() => {
      setTimeout(() => {
        _injectCheckboxes('mp', '.sub-tab.active', 'Managing', 'openMPForm', _sel.mps, 'p-mp-bulk-bar', 'p-mp-bulk-count', '_pBulkDeleteMPs', '_pClearMPSel');
        _injectCheckboxes('cp', '.sub-tab.active', 'Checking', 'openCPForm', _sel.cps, 'p-cp-bulk-bar', 'p-cp-bulk-count', '_pBulkDeleteCPs', '_pClearCPSel');
      }, 60);
    }).observe(target, { childList: true });
  }

  function _injectCheckboxes(type, activeSelector, labelContains, openFn, selSet, barId, countId, deleteFn, clearFn) {
    const content = document.getElementById('master-content');
    if (!content) return;
    const active = document.querySelector('#master-tabs ' + activeSelector);
    if (!active || !active.textContent.includes(labelContains)) return;
    const table = content.querySelector('table');
    if (!table || table.dataset['p_' + type]) return;
    table.dataset['p_' + type] = '1';
    selSet.clear();

    /* header checkbox */
    const thead = table.querySelector('thead tr');
    if (thead) {
      const th = document.createElement('th');
      th.style.width = '36px';
      const chkAll = document.createElement('input');
      chkAll.type  = 'checkbox';
      chkAll.className = 'p-chk-all-' + type;
      chkAll.style.cssText = 'width:15px;height:15px;accent-color:#1d4ed8;cursor:pointer';
      chkAll.title = 'Select all';
      chkAll.addEventListener('change', function () {
        content.querySelectorAll('.p-row-chk-' + type).forEach(c => {
          c.checked = this.checked;
          this.checked ? selSet.add(c.dataset.id) : selSet.delete(c.dataset.id);
        });
        _updateBar(barId, countId, selSet);
      });
      th.appendChild(chkAll);
      thead.insertBefore(th, thead.firstChild);
    }

    /* per-row checkboxes */
    table.querySelectorAll('tbody tr').forEach(tr => {
      const editBtn = [...tr.querySelectorAll('button,a')].find(b =>
        (b.getAttribute('onclick') || '').includes(openFn));
      if (!editBtn) return;
      const match = (editBtn.getAttribute('onclick') || '').match(/'([^']+)'/);
      if (!match) return;
      const id = match[1];
      const td = document.createElement('td');
      const chk = document.createElement('input');
      chk.type = 'checkbox';
      chk.className = 'p-row-chk-' + type;
      chk.dataset.id = id;
      chk.style.cssText = 'width:15px;height:15px;accent-color:#1d4ed8;cursor:pointer';
      chk.addEventListener('change', function () {
        this.checked ? selSet.add(id) : selSet.delete(id);
        _updateBar(barId, countId, selSet);
      });
      td.appendChild(chk);
      tr.insertBefore(td, tr.firstChild);
    });

    /* bulk action bar */
    if (!content.querySelector('#' + barId)) {
      const bar = document.createElement('div');
      bar.id = barId;
      bar.style.cssText = 'display:none;background:#fef3c7;border:1.5px solid #fcd34d;' +
        'border-radius:10px;padding:10px 16px;margin-bottom:12px;align-items:center;gap:12px;flex-wrap:wrap';
      const label = type.toUpperCase();
      bar.innerHTML =
        '<span id="' + countId + '" style="font-weight:700;font-size:12px;color:#92400e;font-family:Syne,sans-serif"></span>' +
        '<button style="background:#dc2626;color:#fff;border:none;padding:5px 14px;border-radius:8px;' +
        'font-size:11px;font-weight:700;cursor:pointer;font-family:Syne,sans-serif" ' +
        'onclick="window.' + deleteFn + '()">🗑 Delete Selected</button>' +
        '<button style="background:transparent;border:1.5px solid #e2e6ef;color:#6b7a99;' +
        'padding:5px 12px;border-radius:8px;font-size:11px;font-weight:700;cursor:pointer" ' +
        'onclick="window.' + clearFn + '()">✕ Clear</button>';
      const tblWrap = content.querySelector('.tbl-wrap') || table.parentElement;
      tblWrap.parentNode.insertBefore(bar, tblWrap);
    }
  }

  function _updateBar(barId, countId, selSet) {
    const bar = document.getElementById(barId);
    const cnt = document.getElementById(countId);
    if (!bar) return;
    bar.style.display = selSet.size > 0 ? 'flex' : 'none';
    if (cnt) cnt.textContent = selSet.size + ' item(s) selected';
  }

  /* ── Bulk delete handlers (window-scoped) ──────────────────────────── */
  window._pClearMPSel = function () {
    _sel.mps.clear();
    document.querySelectorAll('.p-row-chk-mp,.p-chk-all-mp').forEach(c => c.checked = false);
    _updateBar('p-mp-bulk-bar','p-mp-bulk-count',_sel.mps);
  };
  window._pClearCPSel = function () {
    _sel.cps.clear();
    document.querySelectorAll('.p-row-chk-cp,.p-chk-all-cp').forEach(c => c.checked = false);
    _updateBar('p-cp-bulk-bar','p-cp-bulk-count',_sel.cps);
  };
  window._pBulkDeleteMPs = async function () {
    const ids = [..._sel.mps];
    if (!ids.length) return;
    if (!confirm('Delete ' + ids.length + ' Managing Point(s)?\n\nLinked CPs will be unlinked.')) return;
    const r = await fetch('/api/mps/bulk_delete',
      {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids})}).then(x=>x.json());
    if (typeof toast==='function') toast('Deleted ' + r.deleted + ' MP(s)','ok');
    _sel.mps.clear();
    await window.loadAll();
    if (typeof switchMaster==='function') switchMaster('mps');
  };
  window._pBulkDeleteCPs = async function () {
    const ids = [..._sel.cps];
    if (!ids.length) return;
    if (!confirm('Delete ' + ids.length + ' Checking Point(s)?')) return;
    const r = await fetch('/api/cps/bulk_delete',
      {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids})}).then(x=>x.json());
    if (typeof toast==='function') toast('Deleted ' + r.deleted + ' CP(s)','ok');
    _sel.cps.clear();
    await window.loadAll();
    if (typeof switchMaster==='function') switchMaster('cps');
  };

  /* ── 4  Sectors ────────────────────────────────────────────────────── */
  function _renderSectors() {
    const el = document.getElementById('master-content');
    if (!el) return;
    const secs = S.sectors || [];
    el.innerHTML =
      '<div class="section-head"><div><h2>Sectors / Departments</h2>' +
      '<p>' + secs.length + ' sectors — employee grouping and colour coding</p></div>' +
      '<button class="btn btn-primary btn-sm" onclick="window._pOpenSectorForm()">+ Add Sector</button></div>' +
      '<div class="grid-auto" style="margin-top:4px">' +
      (secs.length === 0 ? '<p class="text-muted text-sm">No sectors yet.</p>' :
        secs.map(function(s) {
          return '<div class="card" style="border-left:4px solid ' + _e(s.color) + '">' +
            '<div class="card-body" style="padding:14px 16px">' +
            '<div class="flex items-center gap-8 mb-8">' +
            '<span style="width:14px;height:14px;border-radius:50%;background:' + _e(s.color) + ';display:inline-block;flex-shrink:0"></span>' +
            '<span class="font-black" style="font-size:13px">' + _e(s.name) + '</span>' +
            '<span class="badge badge-blue" style="margin-left:auto">' + _e(s.code) + '</span></div>' +
            '<p class="text-xs text-muted" style="margin-bottom:12px;min-height:16px">' + (_e(s.description)||'—') + '</p>' +
            '<div class="flex gap-6">' +
            '<button class="btn btn-ghost btn-sm flex-1" onclick="window._pOpenSectorForm(\'' + s.id + '\')">✏ Edit</button>' +
            '<button class="btn btn-danger btn-sm" onclick="window._pDeleteSector(\'' + s.id + '\',\'' + _e(s.name) + '\')">🗑</button>' +
            '</div></div></div>';
        }).join('')) +
      '</div>';
  }

  window._pOpenSectorForm = function(sid) {
    var s = sid ? (S.sectors||[]).find(function(x){return x.id===sid;}) : null;
    _pOpenModal(s ? 'Edit Sector' : 'Add Sector',
      '<div class="form-group"><label class="form-label">Code *</label>' +
      '<input class="form-input" id="___sc" value="' + _e(s&&s.code||'') + '" placeholder="e.g. Vehicle"></div>' +
      '<div class="form-group"><label class="form-label">Name *</label>' +
      '<input class="form-input" id="___sn" value="' + _e(s&&s.name||'') + '" placeholder="e.g. Vehicle Operations"></div>' +
      '<div class="form-group"><label class="form-label">Colour</label>' +
      '<div style="display:flex;gap:8px;align-items:center">' +
      '<input type="color" id="___scol" value="' + _e(s&&s.color||'#475569') + '" ' +
      'style="width:44px;height:36px;border:1.5px solid var(--border);border-radius:8px;cursor:pointer;padding:2px" ' +
      'oninput="document.getElementById(\'___scolh\').value=this.value">' +
      '<input class="form-input" id="___scolh" value="' + _e(s&&s.color||'#475569') + '" ' +
      'oninput="document.getElementById(\'___scol\').value=this.value"></div></div>' +
      '<div class="form-group"><label class="form-label">Description</label>' +
      '<input class="form-input" id="___sd" value="' + _e(s&&s.description||'') + '" placeholder="Optional"></div>',
      [{ label: s ? 'Save Changes':'Create Sector', cls:'btn-primary',
         fn: 'window._pSaveSector("'+(sid||'')+'")'  }]);
  };

  window._pSaveSector = async function(sid) {
    var d = {
      code: document.getElementById('___sc').value.trim(),
      name: document.getElementById('___sn').value.trim(),
      color: document.getElementById('___scolh').value.trim() || document.getElementById('___scol').value,
      description: document.getElementById('___sd').value.trim()
    };
    if (!d.code||!d.name){ if(typeof toast==='function') toast('Code and Name required','err'); return; }
    await fetch(sid?'/api/sectors/'+sid:'/api/sectors',
      {method:sid?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
    _pCloseModal();
    S.sectors = await fetch('/api/sectors').then(r=>r.json());
    _renderSectors();
    if(typeof toast==='function') toast(sid?'Sector updated':'Sector created','ok');
  };

  window._pDeleteSector = async function(sid, name) {
    if (!confirm('Delete sector "'+name+'"?\n\nEmployees will have their department cleared.')) return;
    await fetch('/api/sectors/'+sid,{method:'DELETE'});
    S.sectors = await fetch('/api/sectors').then(r=>r.json());
    _renderSectors();
    if(typeof toast==='function') toast('Sector deleted','ok');
  };

  /* ── 5  Locations ──────────────────────────────────────────────────── */
  function _renderLocations() {
    var el = document.getElementById('master-content');
    if (!el) return;
    var locs = S.locations || [];
    var rows = locs.length===0
      ? '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:24px">No locations yet.</td></tr>'
      : locs.map(function(l){
          var sec = (S.sectors||[]).find(function(s){return s.id===l.sector_id;});
          return '<tr>' +
            '<td><span class="ref-badge">'+_e(l.code)+'</span></td>' +
            '<td class="font-bold">'+_e(l.name)+'</td>' +
            '<td class="text-muted text-xs">'+(_e(l.address)||'—')+'</td>' +
            '<td>'+(sec?'<span class="dept-badge" style="background:'+_e(sec.color)+'">'+_e(sec.name)+'</span>':'<span class="text-muted text-xs">—</span>')+'</td>' +
            '<td>'+(l.active?'<span class="badge badge-c">Active</span>':'<span class="badge badge-nc">Inactive</span>')+'</td>' +
            '<td><div style="display:flex;gap:6px">' +
            '<button class="btn-icon" onclick="window._pOpenLocationForm(\''+l.id+'\')" title="Edit">✏</button>' +
            '<button class="btn-icon" style="color:var(--red)" onclick="window._pDeleteLocation(\''+l.id+'\',\''+_e(l.name)+'\')" title="Delete">🗑</button>' +
            '</div></td></tr>';
        }).join('');

    el.innerHTML =
      '<div class="section-head"><div><h2>Locations</h2>' +
      '<p>'+locs.length+' locations — depots, border points, warehouses</p></div>' +
      '<button class="btn btn-primary btn-sm" onclick="window._pOpenLocationForm()">+ Add Location</button></div>' +
      '<div class="tbl-wrap"><table><thead><tr>' +
      '<th>Code</th><th>Name</th><th>Address</th><th>Sector</th><th>Status</th><th>Actions</th>' +
      '</tr></thead><tbody>'+rows+'</tbody></table></div>';
  }

  window._pOpenLocationForm = function(lid) {
    var l = lid ? (S.locations||[]).find(function(x){return x.id===lid;}) : null;
    var secOpts = (S.sectors||[]).map(function(s){
      return '<option value="'+s.id+'"'+(l&&l.sector_id===s.id?' selected':'')+'>'+_e(s.name)+'</option>';
    }).join('');
    _pOpenModal(l?'Edit Location':'Add Location',
      '<div class="form-grid-2">' +
      '<div class="form-group"><label class="form-label">Code *</label>' +
      '<input class="form-input" id="___lc" value="'+_e(l&&l.code||'')+'" placeholder="e.g. BRT-BP"></div>' +
      '<div class="form-group"><label class="form-label">Sector</label>' +
      '<select class="form-select" id="___ls"><option value="">— None —</option>'+secOpts+'</select></div></div>' +
      '<div class="form-group"><label class="form-label">Location Name *</label>' +
      '<input class="form-input" id="___ln" value="'+_e(l&&l.name||'')+'" placeholder="e.g. Birgunj Border Point"></div>' +
      '<div class="form-group"><label class="form-label">Address / District</label>' +
      '<input class="form-input" id="___la" value="'+_e(l&&l.address||'')+'" placeholder="e.g. Birgunj, Parsa"></div>' +
      '<div class="form-group"><label class="form-label">Status</label>' +
      '<select class="form-select" id="___lact">' +
      '<option value="1"'+(l&&l.active===0?'':' selected')+'>Active</option>' +
      '<option value="0"'+(l&&l.active===0?' selected':'')+'>Inactive</option></select></div>',
      [{label:l?'Save Changes':'Create Location',cls:'btn-primary',fn:'window._pSaveLocation("'+(lid||'')+'")'}]);
  };

  window._pSaveLocation = async function(lid) {
    var d = {
      code:      document.getElementById('___lc').value.trim(),
      name:      document.getElementById('___ln').value.trim(),
      address:   document.getElementById('___la').value.trim(),
      sector_id: document.getElementById('___ls').value,
      active:    document.getElementById('___lact').value==='1'
    };
    if (!d.code||!d.name){ if(typeof toast==='function') toast('Code and Name required','err'); return; }
    await fetch(lid?'/api/locations/'+lid:'/api/locations',
      {method:lid?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});
    _pCloseModal();
    S.locations = await fetch('/api/locations').then(r=>r.json());
    _renderLocations();
    if(typeof toast==='function') toast(lid?'Location updated':'Location created','ok');
  };

  window._pDeleteLocation = async function(lid, name) {
    if (!confirm('Delete location "'+name+'"?')) return;
    await fetch('/api/locations/'+lid,{method:'DELETE'});
    S.locations = await fetch('/api/locations').then(r=>r.json());
    _renderLocations();
    if(typeof toast==='function') toast('Location deleted','ok');
  };

  /* ── 6  Private modal (uses existing DOM, no override) ─────────────── */
  function _pOpenModal(title, bodyHtml, btns) {
    var overlay = document.getElementById('modal-overlay');
    var mT = document.getElementById('modal-title');
    var mB = document.getElementById('modal-body');
    var mF = document.getElementById('modal-foot');
    if (!overlay) return;
    mT.textContent = title;
    mB.innerHTML   = bodyHtml;
    mF.innerHTML =
      '<button class="btn btn-ghost" onclick="window._pCloseModal()">Cancel</button>' +
      btns.map(function(b){
        return '<button class="btn '+b.cls+'" onclick="'+b.fn+'">'+b.label+'</button>';
      }).join('');
    overlay.classList.remove('hidden');
  }
  window._pCloseModal = function() {
    var o = document.getElementById('modal-overlay');
    if (o) o.classList.add('hidden');
  };

  /* ── 7  Smart sample banner ─────────────────────────────────────────── */
  function _observeSampleBanner() {
    var dc = document.getElementById('data-content');
    if (!dc) return;
    new MutationObserver(_refreshSampleBanner).observe(dc,{childList:true,subtree:true});
  }

  function _refreshSampleBanner() {
    document.querySelectorAll('.sample-files').forEach(function(div) {
      if (div.dataset.pSamples) return;
      div.dataset.pSamples = '1';
      var items = [
        {key:'employees',label:'👥 Employees ('+(S.employees||[]).length+')',ext:'xlsx'},
        {key:'mps',      label:'🎯 Managing Points ('+(S.mps||[]).length+')',ext:'xlsx'},
        {key:'cps',      label:'✅ Checking Points ('+(S.cps||[]).length+')',ext:'xlsx'},
        {key:'sectors',  label:'🏷 Sectors ('+(S.sectors||[]).length+')',ext:'xlsx'},
        {key:'locations',label:'📍 Locations ('+(S.locations||[]).length+')',ext:'xlsx'},
        {key:'perf',     label:'📊 Performance Template',ext:'csv'},
      ];
      div.innerHTML = items.map(function(f){
        return '<a class="sample-link" href="/api/samples/'+f.key+'" download>' +
               f.label+'&nbsp;<span class="text-xxs" style="opacity:.6">.'+f.ext+'</span></a>';
      }).join('');
    });
  }
  window._refreshSampleBanner = _refreshSampleBanner;

  /* ── util ───────────────────────────────────────────────────────────── */
  function _e(s) {
    return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;')
                        .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }

})();
