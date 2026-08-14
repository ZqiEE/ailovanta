(async function () {
  const el = document.getElementById('modelText');
  if (!el) return;
  try {
    const response = await fetch('/coding/status');
    const status = await response.json();
    const runtime = status.model_runtime || {};
    const integrity = runtime.integrity || {};
    const digest = runtime.model_digest ? String(runtime.model_digest).slice(0, 14) : null;
    const parts = ['model: ' + (status.model || 'unknown')];
    if (digest) parts.push('digest ' + digest);
    if (integrity.status === 'verified') parts.push('locked ✓');
    else if (integrity.status === 'mismatch') parts.push('DIGEST MISMATCH');
    else if (integrity.status) parts.push(integrity.status);
    el.textContent = parts.join(' · ');
    if (integrity.status === 'mismatch') {
      el.title = 'The local model bytes changed since the saved lock. Restart Ailovanta Local to resolve this explicitly.';
    } else if (runtime.model_digest) {
      el.title = 'Local model digest: ' + runtime.model_digest;
    }
  } catch (_) {
    // coding.js already renders the basic model status; keep that fallback.
  }
})();
