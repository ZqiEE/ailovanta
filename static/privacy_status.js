(async function () {
  const el = document.getElementById('privacyText');
  if (!el) return;
  try {
    const response = await fetch('/coding/privacy');
    const privacy = await response.json();
    if (privacy.private_local) {
      el.textContent = 'private local · code + prompts stay on this computer';
      el.title = 'Ailovanta Local is bound to this computer. Project files and prompts are processed by the local runtime.';
    } else {
      el.textContent = 'runtime: ' + (privacy.mode || 'server-local');
      el.title = 'Use `make local` for the strict private-local path.';
    }
  } catch (_) {
    el.textContent = 'privacy: unavailable';
  }
})();
