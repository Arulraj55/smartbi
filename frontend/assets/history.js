const SmartBiHistory = (() => {
  async function loadUploads() {
    try {
      const response = await SmartBiApi.get('/api/history/uploads');
      return response.data?.items || [];
    } catch (error) {
      return [];
    }
  }

  async function loadRecentUploads(limit = 5) {
    const uploads = await loadUploads();
    return uploads.slice(0, limit);
  }

  function renderUploadOptions(container, uploads) {
    if (!container) {
      return;
    }
    container.innerHTML = uploads.map((upload) => `
      <option value="${upload.id}">${SmartBiUtils.escapeHtml(upload.file_name)} - ${SmartBiUtils.escapeHtml(upload.domain_name)}</option>
    `).join('');
  }

  return { loadUploads, loadRecentUploads, renderUploadOptions };
})();