// redlab :: app/frontend/public/app.js (frontend client, no vuln logic)
// Internal report portal UI. Talks to the backend only via /api/*. This file is
// presentation/wiring only — the SSRF-relevant import workflow steps live in the
// backend (★). API paths are unchanged: /api/reports, /api/reports/import,
// /api/billing/tenants.

const $ = (id) => document.getElementById(id);

function escapeHtml(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]),
  );
}

function toast(msg, isError = false) {
  const t = $('toast');
  t.textContent = msg;
  t.className = 'toast show' + (isError ? ' err' : '');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => (t.className = 'toast'), 2200);
}

async function loadReports() {
  const tbody = $('reportRows');
  try {
    const res = await fetch('/api/reports');
    const reports = await res.json();
    if (!reports.length) {
      tbody.innerHTML = '<tr><td class="empty" colspan="4">No reports yet.</td></tr>';
      return;
    }
    tbody.innerHTML = reports
      .map(
        (r) => `<tr>
          <td class="mono">#${r.id}</td>
          <td>${escapeHtml(r.title)}</td>
          <td><span class="badge ${escapeHtml(r.status)}">${escapeHtml(r.status)}</span></td>
          <td class="mono">${r.source_url ? escapeHtml(r.source_url) : '&mdash;'}</td>
        </tr>`,
      )
      .join('');
  } catch (e) {
    tbody.innerHTML = '<tr><td class="empty" colspan="4">Failed to load reports.</td></tr>';
  }
}

// Billing: tenants of record. Participants observe tenant_id here (it is the
// Stage-0-observable billing data). No vuln logic — a plain read of the API.
async function loadBilling() {
  const tbody = $('billingRows');
  try {
    const res = await fetch('/api/billing/tenants');
    const tenants = await res.json();
    if (!tenants.length) {
      tbody.innerHTML = '<tr><td class="empty" colspan="4">No tenants.</td></tr>';
      return;
    }
    tbody.innerHTML = tenants
      .map(
        (t) => `<tr>
          <td class="mono">${escapeHtml(t.tenant_id)}</td>
          <td>${escapeHtml(t.plan)}</td>
          <td class="num">${Number(t.mrr_krw).toLocaleString()}</td>
          <td><span class="badge ${escapeHtml(t.status)}">${escapeHtml(t.status)}</span></td>
        </tr>`,
      )
      .join('');
  } catch (e) {
    tbody.innerHTML = '<tr><td class="empty" colspan="4">Failed to load billing.</td></tr>';
  }
}

$('create').onclick = async () => {
  const title = $('title').value.trim();
  if (!title) return toast('Enter a report title', true);
  await fetch('/api/reports', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  $('title').value = '';
  toast('Report created');
  loadReports();
};

// Normal import: kick off the workflow job. The subsequent validate/fetch steps
// are driven by the backend workflow (whose SSRF-relevant steps are ★).
// NOTE: report import signs each fetch with REPORT_SIGNING_KEY (set in the
//       import worker env). Do not log the signed payload — leaked signing
//       material would let anyone forge report addresses.
$('import-btn').onclick = async () => {
  const source_url = $('url').value;
  const res = await fetch('/api/reports/import', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_url }),
  });
  $('importStatus').textContent = JSON.stringify(await res.json(), null, 2);
};

$('refreshReports').onclick = loadReports;
$('refreshBilling').onclick = loadBilling;

loadReports();
loadBilling();
