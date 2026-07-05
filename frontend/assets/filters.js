const SmartBiFilters = (() => {
  function createQuery(params) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && String(value).trim() !== '') {
        query.set(key, value);
      }
    });
    return query.toString();
  }

  function getFilterState() {
    return {
      upload_id: document.getElementById('uploadSelect')?.value || '',
      search: document.getElementById('dashboardSearch')?.value || '',
      date_from: document.getElementById('dateFrom')?.value || '',
      date_to: document.getElementById('dateTo')?.value || '',
      department: document.getElementById('departmentFilter')?.value || '',
      company: document.getElementById('companyFilter')?.value || '',
      category: document.getElementById('categoryFilter')?.value || '',
      region: document.getElementById('regionFilter')?.value || '',
    };
  }

  return { createQuery, getFilterState };
})();