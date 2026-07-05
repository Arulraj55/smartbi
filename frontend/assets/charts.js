const SmartBiCharts = (() => {
  const chartInstances = new Map();

  function destroyChart(canvasId) {
    const existingChart = chartInstances.get(canvasId);
    if (existingChart) {
      existingChart.destroy();
      chartInstances.delete(canvasId);
    }
  }

  function resolveType(type) {
    switch (type) {
      case 'line':
      case 'pie':
      case 'doughnut':
        return type;
      case 'horizontalBar':
        return 'bar';
      default:
        return 'bar';
    }
  }

  function buildOptions(type) {
    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#e6eef8' } } },
    };
    if (type === 'horizontalBar') {
      options.indexAxis = 'y';
    }
    return options;
  }

  function render(canvasId, config) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === 'undefined') {
      return null;
    }

    destroyChart(canvasId);
    const type = resolveType(config.type || 'bar');
    const chart = new Chart(canvas, {
      type,
      data: {
        labels: config.labels || [],
        datasets: (config.datasets || []).map((dataset) => ({
          label: dataset.label || 'Dataset',
          data: dataset.data || [],
          backgroundColor: dataset.backgroundColor || ['rgba(53, 194, 255, 0.75)'],
          borderColor: dataset.borderColor || 'rgba(53, 194, 255, 1)',
          borderWidth: dataset.borderWidth || 1,
          tension: dataset.tension || 0.3,
          borderRadius: dataset.borderRadius ?? 10,
          fill: dataset.fill ?? false,
        })),
      },
      options: buildOptions(type),
    });

    chartInstances.set(canvasId, chart);
    return chart;
  }

  return { render, destroyChart };
})();