(() => {
  const button = document.getElementById('syncDisk');
  if (!button) return;

  async function updateState() {
    if (!projectId) {
      button.style.display = 'none';
      return;
    }
    try {
      const project = await api(owned('/coding/projects/' + projectId));
      if (project.source === 'local-path' && project.source_path) {
        button.style.display = '';
        button.title = 'Write reviewed Ailovanta changes back to ' + project.source_path;
      } else {
        button.style.display = 'none';
      }
    } catch (_) {
      button.style.display = 'none';
    }
  }

  async function syncDisk() {
    if (!projectId) return;
    if (dirty) await saveFile();
    let project;
    try {
      project = await api(owned('/coding/projects/' + projectId));
    } catch (error) {
      return toast(error.message || 'Could not read project');
    }
    if (project.source !== 'local-path') return toast('This project is not linked to a local folder');
    if (!confirm('Sync reviewed changes back to:\n\n' + project.source_path + '\n\nAilovanta will check for external edits first and back up overwritten files.')) return;

    button.disabled = true;
    button.textContent = 'Syncing...';
    try {
      const response = await fetch(owned('/coding/projects/' + projectId + '/sync'), {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
      });
      let body = {};
      try { body = await response.json(); } catch (_) {}
      if (!response.ok) {
        const detail = body.detail;
        if (response.status === 409 && detail && Array.isArray(detail.conflicts)) {
          throw new Error('Sync blocked because these files changed outside Ailovanta: ' + detail.conflicts.join(', '));
        }
        throw new Error(typeof detail === 'string' ? detail : 'Sync failed (' + response.status + ')');
      }
      await showDiff();
      if (currentFile) {
        try { await openFile(currentFile); } catch (_) {}
      }
      toast(body.synced?.length ? `Synced ${body.synced.length} files to disk` : 'Local repo already matches');
    } catch (error) {
      toast(error.message || 'Sync failed');
    } finally {
      button.disabled = false;
      button.textContent = 'Sync to disk';
      await updateState();
    }
  }

  const previousOpenProject = openProject;
  openProject = async function (id) {
    await previousOpenProject(id);
    await updateState();
  };

  button.onclick = syncDisk;
  setTimeout(updateState, 0);
})();
