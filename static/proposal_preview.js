renderProposal = function () {
  const box = $('agentBody');
  $('apply').disabled = !proposal;
  $('discard').disabled = !proposal;

  if (!proposal) {
    box.innerHTML = '<div class="empty">Ailovanta reads the current project and proposes file-level changes. Review them before applying.</div>';
    return;
  }

  let html = '<div class="card"><h3>' + esc(proposal.summary) + '</h3><p>' + esc(proposal.explanation || '') + '</p></div>';
  html += '<div class="card"><h3>Proposed files</h3>';

  proposal.changes.forEach((change, index) => {
    const label = (change.delete ? 'DELETE ' : '') + change.path;
    const preview = change.delete ? 'This file will be deleted.' : change.content;
    html += '<div class="change">' +
      '<input type="checkbox" class="changePick" data-i="' + index + '" checked>' +
      '<label><details><summary>' + esc(label) + '</summary>' +
      '<pre class="diff">' + esc(preview) + '</pre></details></label></div>';
  });

  html += '</div>';
  if (proposal.context_files && proposal.context_files.length) {
    html += '<div class="card"><h3>Context used</h3><p>' + esc(proposal.context_files.join('\n')) + '</p></div>';
  }
  box.innerHTML = html;
};
