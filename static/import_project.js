async function importFolderLocal() {
  if (!projectId) {
    await createProject();
    if (!projectId) return;
  }

  let limits;
  try {
    limits = await api('/coding/status');
  } catch (_) {
    return toast('Could not read local project limits');
  }

  const maxFiles = Number(limits.max_files || 512);
  const maxFileBytes = Number(limits.max_file_bytes || 524288);
  const maxProjectBytes = Number(limits.max_project_bytes || 16777216);
  const input = document.createElement('input');
  input.type = 'file';
  input.multiple = true;
  input.setAttribute('webkitdirectory', '');

  input.onchange = async () => {
    const files = [];
    let total = 0;
    let skipped = 0;
    for (const file of [...input.files]) {
      const path = file.webkitRelativePath.split('/').slice(1).join('/') || file.name;
      if (!supported(path)) { skipped++; continue; }
      if (/(^|\/)(node_modules|dist|build|vendor|target|\.git|\.next|\.nuxt|coverage|__pycache__|\.venv|venv)(\/|$)/.test(path)) {
        skipped++;
        continue;
      }
      if (file.size > maxFileBytes) { skipped++; continue; }
      if (files.length >= maxFiles || total + file.size > maxProjectBytes) {
        skipped++;
        continue;
      }
      const text = await file.text();
      const bytes = new TextEncoder().encode(text).length;
      if (bytes > maxFileBytes || total + bytes > maxProjectBytes) { skipped++; continue; }
      total += bytes;
      files.push({ path, content: text });
    }

    if (!files.length) return toast('No supported source files found');
    try {
      await api(owned('/coding/projects/' + projectId + '/import'), {
        method: 'POST',
        body: JSON.stringify({ files, source_url: null })
      });
      currentFile = null;
      $('editor').value = '';
      await loadProjects();
      await loadFiles();
      toast(`Imported ${files.length} source files${skipped ? ` · skipped ${skipped}` : ''}`);
    } catch (error) {
      toast(error.message || 'Import failed');
    }
  };
  input.click();
}

// coding.js binds the original handler during initial script evaluation. Replace
// it after load so local imports follow the actual server-side configured limits.
$('importProject').onclick = importFolderLocal;
