// Main application logic - uses SmartBiApi from api.js
const api = window.SmartBiApi;

function showLoginForm() {
  document.getElementById('loginForm').style.display = 'block';
  document.getElementById('signupForm').style.display = 'none';
  document.getElementById('loginTab').classList.add('active');
  document.getElementById('signupTab').classList.remove('active');
}

function showSignupForm() {
  document.getElementById('loginForm').style.display = 'none';
  document.getElementById('signupForm').style.display = 'block';
  document.getElementById('loginTab').classList.remove('active');
  document.getElementById('signupTab').classList.add('active');
}

window.showLoginForm = showLoginForm;
window.showSignupForm = showSignupForm;

function formatNumber(value) {
  return new Intl.NumberFormat('en-IN').format(value);
}

function renderChart(canvasId, labels, values, label) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof Chart === 'undefined' || typeof SmartBiCharts === 'undefined') {
    return;
  }

  SmartBiCharts.render(canvasId, {
    type: 'bar',
    labels: labels,
    datasets: [{
      label: label,
      data: values,
      backgroundColor: ['rgba(53, 194, 255, 0.75)', 'rgba(104, 240, 185, 0.75)', 'rgba(255, 180, 107, 0.75)', 'rgba(255, 120, 120, 0.75)'],
    }]
  });
}

function bindLoginForm() {
  const loginForm = document.getElementById('loginForm');
  if (!loginForm) {
    return;
  }

  const messageNode = document.getElementById('loginMessage');
  const bannerNode = document.getElementById('uploadStatusBanner');
  
  loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(loginForm);
    const username = formData.get('username');
    const password = formData.get('password');
    
    if (messageNode) {
      messageNode.textContent = '';
      messageNode.style.display = 'none';
    }
    
    try {
      const result = await api.login(username, password);
      
      if (messageNode) {
        messageNode.textContent = result.ok ? 'Login successful! Redirecting...' : (result.data?.message || 'Login failed');
        messageNode.className = result.ok ? 'auth-message success' : 'auth-message error';
        messageNode.style.display = 'block';
      }
      
      if (bannerNode) {
        bannerNode.textContent = result.ok ? 'Session active.' : 'Waiting for sign-in.';
        bannerNode.className = result.ok ? 'status-banner success' : 'status-banner';
      }
      
      if (result.ok) {
        setTimeout(() => window.location.href = '/pages/upload.html', 1500);
      }
    } catch (error) {
      if (messageNode) {
        messageNode.textContent = 'Cannot connect to server. Is backend running?';
        messageNode.className = 'auth-message error';
        messageNode.style.display = 'block';
      }
    }
  });
}

function bindSignupForm() {
  const signupForm = document.getElementById('signupForm');
  if (!signupForm) {
    return;
  }

  const messageNode = document.getElementById('signupMessage');
  
  signupForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(signupForm);
    const fullName = formData.get('fullName') || '';
    const username = formData.get('username');
    const email = formData.get('email');
    const password = formData.get('password');
    
    if (messageNode) {
      messageNode.textContent = '';
      messageNode.style.display = 'none';
    }
    
    if (password.length < 6) {
      if (messageNode) {
        messageNode.textContent = 'Password must be at least 6 characters.';
        messageNode.className = 'auth-message error';
        messageNode.style.display = 'block';
      }
      return;
    }
    
    try {
      const response = await fetch('https://smartbi-backend.onrender.com/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ username, email, password, full_name: fullName })
      });
      
      const data = await response.json();
      
      if (messageNode) {
        messageNode.textContent = data.message || (response.ok ? 'Account created successfully!' : 'Signup failed');
        messageNode.className = response.ok ? 'auth-message success' : 'auth-message error';
        messageNode.style.display = 'block';
      }
      
      if (response.ok) {
        setTimeout(() => {
          showLoginForm();
          if (messageNode) {
            messageNode.style.display = 'none';
          }
        }, 2000);
      }
    } catch (error) {
      if (messageNode) {
        messageNode.textContent = 'Cannot connect to server. Is backend running?';
        messageNode.className = 'auth-message error';
        messageNode.style.display = 'block';
      }
    }
  });
}

function bindUploadForm() {
  const uploadForm = document.getElementById('uploadForm');
  if (!uploadForm) {
    return;
  }

  const resultsNode = document.getElementById('uploadResults');
  const statusNode = document.getElementById('uploadStatus');
  
  uploadForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    if (statusNode) {
      statusNode.innerHTML = '<p class=\"status-pill\">Processing uploads...</p>';
    }
    
    const formData = new FormData(uploadForm);
    
    try {
      const result = await api.uploadFiles(formData);
      
      if (resultsNode) {
        resultsNode.innerHTML = '';
      }
      if (statusNode) {
        statusNode.innerHTML = '';
      }

      if (!result.ok) {
        if (statusNode) {
          statusNode.innerHTML = `<p class=\"error\">${result.data?.message || 'Upload failed'}</p>`;
        }
        return;
      }

      const items = result.data?.items || [];
      
      items.forEach((item) => {
        if (resultsNode) {
          const article = document.createElement('article');
          article.className = 'result page-card';
          article.innerHTML = `
            <h3>${item.file_name || 'Untitled file'}</h3>
            <p><span class="status-pill">${item.status}</span></p>
            <p>Domain: ${item.domain_name || 'Unknown'} | Confidence: ${item.confidence ?? 0}%</p>
            <p>Rows: ${item.row_count ?? 0}</p>
            ${item.reason ? `<p class="error">${item.reason}</p>` : ''}
            ${(item.errors || []).length > 0 ? `<p class="error">${item.errors.join('<br>')}</p>` : ''}
            ${(item.warnings || []).length > 0 ? `<p class="message">${item.warnings.join('<br>')}</p>` : ''}
          `;
          resultsNode.appendChild(article);
        }

        if (statusNode) {
          if (item.status === 'processed') {
            statusNode.insertAdjacentHTML('beforeend', `<p class="status-pill">${item.file_name} uploaded successfully.</p>`);
          } else if (item.status === 'validation_failed') {
            statusNode.insertAdjacentHTML('beforeend', `<p class="error">${item.file_name} has validation issues.</p>`);
          } else if (item.status === 'rejected') {
            statusNode.insertAdjacentHTML('beforeend', `<p class="error">${item.file_name} was rejected.</p>`);
          } else {
            statusNode.insertAdjacentHTML('beforeend', `<p class="error">${item.file_name || 'File'} failed to process.</p>`);
          }
        }
      });
    } catch (error) {
      if (statusNode) {
        statusNode.innerHTML = '<p class="error">Upload request failed.</p>';
      }
    }
  });
}

async function loadDashboard() {
  const summaryNode = document.getElementById('dashboardSummary');
  const domainBadge = document.getElementById('analyticsDomainBadge');
  
  if (!summaryNode) {
    return;
  }

  try {
    const response = await api.get('/api/analytics/summary');
    
    if (!response.ok) {
      summaryNode.innerHTML = '<p class="error">Unable to load dashboard data. Log in first, then upload a workbook.</p>';
      return;
    }

    const summary = response.data || {};
    const selectedSummary = summary.kpis || {};
    const domainName = summary.domain?.name || 'Generic';
    const confidence = summary.domain?.confidence ?? 0;

    if (domainBadge) {
      domainBadge.textContent = `${domainName} | ${confidence}% confidence`;
      domainBadge.className = 'status-banner success';
    }

    summaryNode.innerHTML = `
      <div class="metric"><h3>${formatNumber(summary.row_count || 0)}</h3><p>Rows Processed</p></div>
      <div class="metric"><h3>${domainName}</h3><p>Detected Domain</p></div>
      <div class="metric"><h3>${confidence}%</h3><p>Detection Confidence</p></div>
      <div class="metric"><h3>${formatNumber(selectedSummary.total_revenue || selectedSummary.total_students || selectedSummary.total_employees || selectedSummary.row_count || 0)}</h3><p>Primary KPI</p></div>
    `;

    const primaryChart = summary.charts?.primary || {};
    const secondaryChart = summary.charts?.secondary || {};
    
    renderChart('domainChart', primaryChart.labels || [], primaryChart.values || [], primaryChart.label || 'Primary Chart');
    renderChart('monthlyChart', secondaryChart.labels || [], secondaryChart.values || [], secondaryChart.label || 'Secondary Chart');
  } catch (error) {
    summaryNode.innerHTML = '<p class="error">Unable to load dashboard data. Log in first, then upload a workbook.</p>';
  }
}

async function loadHistory() {
  const historyNode = document.getElementById('historyList');
  if (!historyNode) {
    return;
  }

  try {
    const response = await api.get('/api/history/uploads');
    
    if (!response.ok || !response.data) {
      historyNode.innerHTML = '<p class="error">Unable to load history. Sign in first.</p>';
      return;
    }
    
    const history = response.data;
    historyNode.innerHTML = '';
    
    if (!history.items || history.items.length === 0) {
      historyNode.innerHTML = '<p class="message">No upload history available yet.</p>';
      return;
    }
    
    history.items.forEach((item) => {
      const element = document.createElement('article');
      element.className = 'history-item';
      element.innerHTML = `
        <h3>${item.file_name}</h3>
        <p>${item.domain_name} | ${item.row_count} rows | ${item.confidence}%</p>
        <p>${new Date(item.created_at).toLocaleString()}</p>
      `;
      historyNode.appendChild(element);
    });
  } catch (error) {
    historyNode.innerHTML = '<p class="error">Unable to load history. Sign in first.</p>';
  }
}

async function loadReports() {
  const reportNode = document.getElementById('reportList');
  if (!reportNode) {
    return;
  }

  try {
    const response = await api.get('/api/reports');
    
    if (!response.ok || !response.data) {
      reportNode.innerHTML = '<p class="error">Unable to load reports. Sign in first.</p>';
      return;
    }
    
    const metadata = response.data;
    reportNode.innerHTML = `
      <article class="report-box page-card"><h3>Available Formats</h3><p>${(metadata.available_formats || []).join(', ')}</p></article>
      <article class="report-box page-card"><h3>Download Endpoint</h3><p>${metadata.download_endpoint || '/api/reports/download'}</p></article>
      <article class="report-box page-card"><h3>Required Parameters</h3><p>${((metadata.parameters || {}).required || []).join(', ')}</p></article>
    `;
  } catch (error) {
    reportNode.innerHTML = '<p class="error">Unable to load reports. Sign in first.</p>';
  }
}

function bindReportDownloadForm() {
  const form = document.getElementById('reportDownloadForm');
  if (!form) {
    return;
  }

  const statusNode = document.getElementById('reportStatus');
  
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    const formData = new FormData(form);
    const params = new URLSearchParams();
    
    ['upload_id', 'format', 'compare', 'upload_b'].forEach((key) => {
      const value = formData.get(key);
      if (value !== null && String(value).trim()) {
        params.set(key, value);
      }
    });

    if (statusNode) {
      statusNode.textContent = 'Generating report...';
      statusNode.className = 'message status-pill';
    }

    try {
      const response = await fetch(`https://smartbi-backend.onrender.com/api/reports/download?${params.toString()}`, {
        credentials: 'same-origin',
      });
      
      if (!response.ok) {
        const errorPayload = await response.json();
        if (statusNode) {
          statusNode.textContent = errorPayload.message || 'Report generation failed.';
          statusNode.className = 'message error';
        }
        return;
      }

      const blob = await response.blob();
      const disposition = response.headers.get('content-disposition') || '';
      const match = disposition.match(/filename="?([^"]+)"?/);
      const filename = match ? match[1] : `smartbi-report.${formData.get('format')}`;
      
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      
      if (statusNode) {
        statusNode.textContent = 'Report downloaded successfully.';
        statusNode.className = 'message status-pill';
      }
    } catch (error) {
      if (statusNode) {
        statusNode.textContent = 'Report download failed.';
        statusNode.className = 'message error';
      }
    }
  });
}

// Initialize on page load
bindLoginForm();
bindSignupForm();
bindUploadForm();
bindReportDownloadForm();
loadDashboard();
loadHistory();
loadReports();
