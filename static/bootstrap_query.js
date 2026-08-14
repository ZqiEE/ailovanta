(() => {
  const params = new URLSearchParams(location.search);
  const owner = params.get('owner');
  const project = params.get('project');
  if (owner && /^[A-Za-z0-9_-]{1,120}$/.test(owner)) {
    localStorage.setItem('ailovanta_owner', owner);
  }
  if (project && /^proj_[A-Za-z0-9]+$/.test(project)) {
    localStorage.setItem('ailovanta_project', project);
  }
})();
