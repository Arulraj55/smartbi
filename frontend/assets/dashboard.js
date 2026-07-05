const SmartBiDashboard = (() => {
  const state = {
    currentUploadId: '',
    currentData: null,
    currentRows: [],
    currentChartType: 'bar',
  };

  async function initialize() {
    bindDashboardControls();
    await refreshDashboard();
  }

  function bindDashboardControls() {
    document.getElementById('logoutButton')?.addEventListener('click', async () => {
      await SmartBiApi.logout();
      window.location.href = '/';
    });

    document.getElementById('uploadShortcutButton')?.addEventListener('click', () => {
      window.location.href = '/upload';
    });

    document.getElementById('refreshDashboardButton')?.addEventListener('click', () => refreshDashboard());

    document.getElementById('uploadSelect')?.addEventListener('change', (event) => {
      state.currentUploadId = event.target.value;
      refreshDashboard();
    });

    const debouncedRefresh = SmartBiUtils.debounce(() => refreshDashboard());
    ['dateFrom', 'dateTo', 'departmentFilter', 'companyFilter', 'categoryFilter', 'regionFilter', 'dashboardSearch']
      .map((id) => document.getElementById(id))
      .filter(Boolean)
      .forEach((element) => element.addEventListener('input', debouncedRefresh));
  }

  async function refreshDashboard() {
    showLoadingState(true);
    try {
      const query = SmartBiFilters.createQuery({ upload_id: state.currentUploadId });
      const response = await SmartBiApi.get(`/api/analytics/dashboard${query ? `?${query}` : ''}`);
      if (!response.ok) {
        showEmptyState(response.data?.message || 'No analytics data available.');
        return;
      }

      state.currentData = response.data;
      state.currentRows = extractRowsFromAnalytics(response.data);
      renderDashboard(response.data);
      showNotification('Dashboard refreshed successfully.', 'success');
    } catch (error) {
      showErrorState('Unable to load the dashboard.');
    } finally {
      showLoadingState(false);
    }
  }

  function extractRowsFromAnalytics(data) {
    return data?.dashboard?.recent_uploads || [];
  }

  function renderDashboard(data) {
    renderHeader(data);
    renderWidgets(data);
    renderKpiCards(data);
    renderCharts(data);
    renderUploadHistory(data);
    renderTables(data);
  }

  function renderHeader(data) {
    const titleNode = document.getElementById('dashboardTitle');
    const profileNode = document.getElementById('profileName');
    const refreshNode = document.getElementById('lastRefreshTime');
    const domainNode = document.getElementById('domainDetectionResult');

    if (titleNode) {
      titleNode.textContent = `SmartBI Dashboard - ${data?.upload?.file_name || 'Latest Upload'}`;
    }
    if (profileNode) {
      profileNode.textContent = 'Admin';
    }
    if (refreshNode) {
      refreshNode.textContent = SmartBiUtils.formatDate(data?.dashboard?.last_refresh_time);
    }
    if (domainNode) {
      domainNode.textContent = `${data?.analytics?.domain?.name || 'Generic'} (${data?.analytics?.domain?.confidence || 0}% confidence)`;
    }
  }

  function renderWidgets(data) {
    setText('recordCountWidget', SmartBiUtils.formatNumber(data?.dashboard?.record_count || 0));
    setText('datasetInfoWidget', `${data?.dashboard?.dataset_information?.row_count || 0} rows / ${data?.dashboard?.dataset_information?.column_count || 0} cols`);
    setText('latestReportWidget', data?.dashboard?.latest_report?.file_name || 'No reports yet');
    setText('recentUploadWidget', data?.dashboard?.recent_uploads?.[0]?.file_name || 'No recent uploads');
  }

  function renderKpiCards(data) {
    const kpiContainer = document.getElementById('kpiCards');
    if (!kpiContainer) {
      return;
    }

    const kpis = data?.analytics?.kpis || {};
    const domainName = data?.analytics?.domain?.name || 'Generic';
    const cards = buildKpiCards(domainName, kpis);
    kpiContainer.innerHTML = cards.map((card) => `
      <article class="kpi-card">
        <strong>${SmartBiUtils.escapeHtml(card.value)}</strong>
        <span>${SmartBiUtils.escapeHtml(card.label)}</span>
      </article>
    `).join('');
  }

  function buildKpiCards(domainName, kpis) {
    if (domainName === 'Placement Management') {
      return [
        { label: 'Total Students', value: kpis.total_students ?? 0 },
        { label: 'Placement %', value: `${kpis.placement_percentage ?? 0}%` },
        { label: 'Highest Package', value: kpis.highest_package ?? 0 },
        { label: 'Companies', value: Object.keys(kpis.company_wise_placements || {}).length },
      ];
    }
    if (domainName === 'HR Management') {
      return [
        { label: 'Employees', value: kpis.total_employees ?? 0 },
        { label: 'Attendance', value: `${kpis.attendance_percentage ?? 0}%` },
        { label: 'Departments', value: kpis.department_count ?? 0 },
        { label: 'Average Salary', value: kpis.average_salary ?? 0 },
      ];
    }
    if (domainName === 'Retail Sales') {
      return [
        { label: 'Revenue', value: kpis.total_revenue ?? 0 },
        { label: 'Orders', value: kpis.total_orders ?? 0 },
        { label: 'Customers', value: Object.keys(kpis.top_customers || {}).length },
        { label: 'Products', value: Object.keys(kpis.top_products || {}).length },
      ];
    }
    if (domainName === 'Inventory') {
      return [
        { label: 'Products', value: kpis.total_products ?? 0 },
        { label: 'Low Stock', value: kpis.low_stock_items ?? 0 },
        { label: 'Stock Value', value: kpis.stock_value ?? 0 },
        { label: 'Out of Stock', value: kpis.out_of_stock ?? 0 },
      ];
    }
    if (domainName === 'Student Attendance') {
      return [
        { label: 'Attendance %', value: `${kpis.attendance_percentage ?? 0}%` },
        { label: 'Absent %', value: `${kpis.absent_percentage ?? 0}%` },
        { label: 'Students', value: Object.values(kpis.class_wise_attendance || {}).reduce((sum, current) => sum + Number(current || 0), 0) },
        { label: 'Classes', value: Object.keys(kpis.class_wise_attendance || {}).length },
      ];
    }
    return [
      { label: 'Rows', value: kpis.row_count ?? 0 },
      { label: 'Columns', value: kpis.column_count ?? 0 },
      { label: 'Duplicates', value: kpis.duplicate_rows ?? 0 },
      { label: 'Missing Values', value: kpis.missing_values?.total ?? 0 },
    ];
  }

  function renderCharts(data) {
    const charts = data?.analytics?.charts || {};
    SmartBiCharts.render('primaryChart', buildChartConfig(charts.primary, state.currentChartType));
    SmartBiCharts.render('secondaryChart', buildChartConfig(charts.secondary, 'line'));
    SmartBiCharts.render('tertiaryChart', buildChartConfig(charts.tertiary, 'pie'));
    SmartBiCharts.render('quaternaryChart', buildChartConfig(charts.quaternary, 'doughnut'));
  }

  function buildChartConfig(chartData, type) {
    return {
      type,
      labels: chartData?.labels || [],
      datasets: [{
        label: chartData?.label || 'Chart',
        data: chartData?.values || [],
        backgroundColor: ['rgba(53, 194, 255, 0.75)', 'rgba(104, 240, 185, 0.75)', 'rgba(255, 180, 107, 0.75)', 'rgba(255, 120, 120, 0.75)'],
      }],
    };
  }

  function renderUploadHistory(data) {
    const container = document.getElementById('recentUploadsList');
    if (!container) {
      return;
    }
    const uploads = data?.dashboard?.recent_uploads || [];
    if (!uploads.length) {
      container.innerHTML = '<div class="empty-state">No uploads available yet.</div>';
      return;
    }
    container.innerHTML = uploads.map((upload) => `
      <button class="history-item" data-upload-id="${upload.id}">
        <strong>${SmartBiUtils.escapeHtml(upload.file_name)}</strong>
        <span>${SmartBiUtils.escapeHtml(upload.domain_name)} - ${upload.row_count} rows</span>
      </button>
    `).join('');

    container.querySelectorAll('[data-upload-id]').forEach((button) => {
      button.addEventListener('click', async () => {
        state.currentUploadId = button.dataset.uploadId;
        await refreshDashboard();
      });
    });
  }

  function renderTables(data) {
    const tableContainer = document.getElementById('analyticsTable');
    if (!tableContainer) {
      return;
    }

    const rows = data?.dashboard?.recent_uploads || [];
    const filteredRows = applyFilters(rows);
    const sortedRows = SmartBiTables.sortRows(filteredRows, 'created_at', 'desc');
    const pagedRows = SmartBiTables.paginateRows(sortedRows, 1);

    if (!pagedRows.length) {
      tableContainer.innerHTML = '<div class="empty-state">No table rows match the current filters.</div>';
      return;
    }

    tableContainer.innerHTML = `
      <div class="table-actions">
        <button type="button" id="exportCsvButton">Export CSV</button>
        <button type="button" id="exportExcelButton">Export Excel</button>
      </div>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>File</th>
              <th>Domain</th>
              <th>Rows</th>
              <th>Confidence</th>
              <th>Created At</th>
            </tr>
          </thead>
          <tbody>
            ${pagedRows.map((row) => `
              <tr>
                <td>${SmartBiUtils.escapeHtml(row.file_name)}</td>
                <td>${SmartBiUtils.escapeHtml(row.domain_name)}</td>
                <td>${SmartBiUtils.formatNumber(row.row_count)}</td>
                <td>${row.confidence}%</td>
                <td>${SmartBiUtils.formatDate(row.created_at)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('exportCsvButton')?.addEventListener('click', () => SmartBiTables.exportCsv(sortedRows));
    document.getElementById('exportExcelButton')?.addEventListener('click', () => SmartBiTables.exportExcel(sortedRows));
  }

  function applyFilters(rows) {
    const stateFilters = SmartBiFilters.getFilterState();
    let filteredRows = SmartBiTables.filterRows(rows, stateFilters.search);
    if (stateFilters.department) {
      filteredRows = filteredRows.filter((row) => String(row.department_name || row.department || '').toLowerCase().includes(stateFilters.department.toLowerCase()));
    }
    if (stateFilters.company) {
      filteredRows = filteredRows.filter((row) => String(row.company_name || row.company || '').toLowerCase().includes(stateFilters.company.toLowerCase()));
    }
    if (stateFilters.category) {
      filteredRows = filteredRows.filter((row) => String(row.category || '').toLowerCase().includes(stateFilters.category.toLowerCase()));
    }
    if (stateFilters.region) {
      filteredRows = filteredRows.filter((row) => String(row.region || '').toLowerCase().includes(stateFilters.region.toLowerCase()));
    }
    return filteredRows;
  }

  function showLoadingState(isLoading) {
    document.getElementById('dashboardLoadingSpinner')?.classList.toggle('is-visible', isLoading);
    document.getElementById('dashboardSkeleton')?.classList.toggle('is-visible', isLoading);
  }

  function showErrorState(message) {
    const node = document.getElementById('dashboardMessage');
    if (node) {
      node.textContent = message;
      node.className = 'message error';
    }
  }

  function showEmptyState(message) {
    const node = document.getElementById('dashboardMessage');
    if (node) {
      node.textContent = message;
      node.className = 'message empty-state';
    }
  }

  function showNotification(message, type = 'success') {
    const node = document.getElementById('dashboardMessage');
    if (node) {
      node.textContent = message;
      node.className = type === 'success' ? 'message status-pill' : 'message error';
    }
  }

  function setText(id, value) {
    const node = document.getElementById(id);
    if (node) {
      node.textContent = value;
    }
  }

  return { initialize, refreshDashboard };
})();