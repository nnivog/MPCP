/**
 * MPCP Frontend Patches — index.html
 * Apply these changes in your <script> section
 *
 * Fixes:
 *   1. Modal backdrop click prevention
 *   2. Performance entry dual-mode (count vs %)
 *   3. FY auto-detection from date picker
 */


// ═══════════════════════════════════════════════════════════════
// 1. MODAL BACKDROP CLICK PREVENTION
//    Find your modal open/close logic and replace backdrop handler
// ═══════════════════════════════════════════════════════════════

/*
  FIND this pattern in your existing code (approximate):
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

  REPLACE with:
    modal.addEventListener('click', e => {
      // Only close if user clicks the dark overlay — NOT the white card
      if (e.target === modal) {
        e.stopPropagation();
        // Optional: shake animation to hint it won't close
        const card = modal.querySelector('.modal-card, [class*="modal-content"], [class*="bg-white"]');
        if (card) {
          card.style.transition = 'transform 0.1s';
          card.style.transform = 'scale(1.01)';
          setTimeout(() => card.style.transform = '', 150);
        }
        // REMOVE the closeModal() call — modal stays open
      }
    });

  ALSO add this to your modal HTML close button only:
    <button onclick="closeModal()">×</button>
*/

// Utility: Apply to ALL modals in one shot
function preventBackdropClose(modalEl) {
  modalEl.addEventListener('mousedown', function (e) {
    if (e.target === modalEl) {
      e.stopImmediatePropagation();
      // Visual feedback: brief scale pulse on the card
      const card = modalEl.querySelector('[class*="bg-white"], [class*="modal-card"], .rounded-xl');
      if (card) {
        card.classList.add('scale-[1.01]');
        setTimeout(() => card.classList.remove('scale-[1.01]'), 150);
      }
    }
  }, true);
}
// Usage: document.querySelectorAll('.modal-backdrop').forEach(preventBackdropClose);


// ═══════════════════════════════════════════════════════════════
// 2. PERFORMANCE ENTRY — DUAL INPUT MODE
//    Mode A: Enter total + compliant count → auto-calc %
//    Mode B: Enter total + % achieved     → auto-calc compliant count
// ═══════════════════════════════════════════════════════════════

const PerfEntryMode = {
  current: 'count',   // 'count' | 'percent'

  // Call this to build the entry form fields
  renderModeToggle(container) {
    container.innerHTML = `
      <div class="flex gap-2 mb-3">
        <button id="btn-mode-count"
          class="px-3 py-1 text-sm rounded font-semibold
                 ${this.current === 'count' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'}"
          onclick="PerfEntryMode.switch('count')">
          Count Mode (units done / on time)
        </button>
        <button id="btn-mode-pct"
          class="px-3 py-1 text-sm rounded font-semibold
                 ${this.current === 'percent' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'}"
          onclick="PerfEntryMode.switch('percent')">
          % Mode (total + % achieved)
        </button>
      </div>
      ${this.renderFields()}
    `;
  },

  renderFields() {
    if (this.current === 'count') {
      return `
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs font-semibold text-gray-500 uppercase">Total Units Done *</label>
            <input id="perf-total" type="number" min="1" placeholder="e.g. 250"
              class="w-full border rounded px-3 py-2 mt-1" oninput="PerfEntryMode.autoCalc()">
          </div>
          <div>
            <label class="text-xs font-semibold text-gray-500 uppercase">Units On Time (Compliant) *</label>
            <input id="perf-compliant" type="number" min="0" placeholder="e.g. 240"
              class="w-full border rounded px-3 py-2 mt-1" oninput="PerfEntryMode.autoCalc()">
          </div>
        </div>
        <div id="perf-calc-display" class="mt-2 text-sm text-gray-500"></div>
      `;
    } else {
      return `
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs font-semibold text-gray-500 uppercase">Total Units Done *</label>
            <input id="perf-total" type="number" min="1" placeholder="e.g. 250"
              class="w-full border rounded px-3 py-2 mt-1" oninput="PerfEntryMode.autoCalc()">
          </div>
          <div>
            <label class="text-xs font-semibold text-gray-500 uppercase">% Achieved *</label>
            <input id="perf-pct" type="number" min="0" max="100" step="0.01" placeholder="e.g. 96.5"
              class="w-full border rounded px-3 py-2 mt-1" oninput="PerfEntryMode.autoCalc()">
          </div>
        </div>
        <div id="perf-calc-display" class="mt-2 text-sm text-gray-500"></div>
      `;
    }
  },

  switch(mode) {
    this.current = mode;
    const container = document.getElementById('perf-mode-container');
    if (container) this.renderModeToggle(container);
  },

  autoCalc() {
    const total = parseInt(document.getElementById('perf-total')?.value || 0);
    const display = document.getElementById('perf-calc-display');
    if (!display || !total) return;

    let compliant, nc, pctC;

    if (this.current === 'count') {
      compliant = parseInt(document.getElementById('perf-compliant')?.value || 0);
      if (compliant > total) {
        display.innerHTML = `<span class="text-red-500">⚠ Compliant cannot exceed total</span>`;
        return;
      }
      nc   = total - compliant;
      pctC = total ? (compliant / total * 100).toFixed(1) : 0;
    } else {
      const pct = parseFloat(document.getElementById('perf-pct')?.value || 0);
      compliant = Math.round(total * pct / 100);
      nc   = total - compliant;
      pctC = pct.toFixed(1);
    }

    const statusColor = parseFloat(pctC) >= 95 ? 'text-green-600' : 'text-red-500';
    const statusLabel = parseFloat(pctC) >= 95 ? '✓ Compliant' : '✗ Non-Compliant';

    display.innerHTML = `
      <div class="flex gap-4 p-2 bg-gray-50 rounded text-xs">
        <span>Total: <strong>${total}</strong></span>
        <span>Compliant: <strong>${compliant}</strong></span>
        <span>NC: <strong>${nc}</strong></span>
        <span>Rate: <strong>${pctC}%</strong></span>
        <span class="${statusColor} font-bold">${statusLabel}</span>
      </div>
    `;

    // Store computed values for form submission
    window._perfPayload = { total, compliant, nc: nc, pct_c: parseFloat(pctC),
                            mode: this.current };
  },

  // Call this when submitting the form
  getPayload() {
    return window._perfPayload || null;
  }
};


// ═══════════════════════════════════════════════════════════════
// 3. FY AUTO-DETECTION FROM DATE PICKER
//    Wire this to your date input in the Quick Entry form
// ═══════════════════════════════════════════════════════════════

async function autoDetectFY(dateValue) {
  if (!dateValue) return;
  try {
    const res  = await fetch(`/api/fy_from_date?date=${dateValue}`);
    const data = await res.json();
    if (data.error) return;

    // Update FY display / hidden field
    const fyDisplay = document.getElementById('perf-fy-display');
    const fyInput   = document.getElementById('perf-fy-hidden');
    const monthDisp = document.getElementById('perf-month-display');

    if (fyDisplay)  fyDisplay.textContent = `FY: ${data.fy} | ${data.bs_month} | ${data.quarter}`;
    if (fyInput)    fyInput.value = data.fy;
    if (monthDisp)  monthDisp.textContent = data.bs_month;

    // Store for submission
    window._perfFY    = data.fy;
    window._perfMonth = data.bs_month;

    return data;
  } catch (e) {
    console.warn('FY detection failed:', e);
  }
}

/*
  USAGE in your Quick Entry date input:
    <input type="date" id="quick-entry-date"
      onchange="autoDetectFY(this.value)"
      value="${new Date().toISOString().split('T')[0]}">
    <div id="perf-fy-display" class="text-xs text-blue-600 mt-1"></div>
    <input type="hidden" id="perf-fy-hidden">
*/


// ═══════════════════════════════════════════════════════════════
// 4. UPDATED QUICK ENTRY SUBMIT — sends to /api/perf/quick
// ═══════════════════════════════════════════════════════════════

async function submitQuickEntry({ empCode, cpRef, date, actualVal, notes, overwrite = false }) {
  const perf = PerfEntryMode.getPayload();
  if (!perf) {
    showToast('Please fill in total and compliant/% fields', 'error');
    return;
  }

  const fy      = window._perfFY    || document.getElementById('perf-fy-hidden')?.value;
  const bsMonth = window._perfMonth || '';

  if (!fy) {
    showToast('FY could not be detected — check date', 'error');
    return;
  }

  const body = {
    date, emp_code: empCode, cp_ref: cpRef,
    total: perf.total, compliant: perf.compliant,
    mode: perf.mode, pct_achieved: perf.pct_c,
    actual_val: actualVal || 0, notes: notes || '',
    fy, bs_month: bsMonth, overwrite
  };

  const res  = await fetch('/api/perf/quick', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const data = await res.json();

  if (res.status === 409) {
    // Duplicate warning — ask user to confirm overwrite
    if (confirm(`⚠ ${data.message}\n\nDo you want to overwrite?`)) {
      return submitQuickEntry({ empCode, cpRef, date, actualVal, notes, overwrite: true });
    }
    return;
  }
  if (!res.ok) {
    showToast(data.error || 'Save failed', 'error');
    return;
  }

  showToast(`Saved ✓ — ${data.bs_month} ${data.fy} | ${data.pct_compliant}% compliant`, 'success');
  return data;
}


// ═══════════════════════════════════════════════════════════════
// 5. INITIALIZE ON PAGE LOAD
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
  // Auto-detect FY on load with today's date
  const today = new Date().toISOString().split('T')[0];
  autoDetectFY(today);

  // Prevent backdrop close on all modals
  document.querySelectorAll('[id$="-modal"], .modal-overlay').forEach(preventBackdropClose);
});
