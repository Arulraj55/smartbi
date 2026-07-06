const BASE_URL = window.SMARTBI_BACKEND_URL || 'https://smartbi-backend.onrender.com';

const SmartBiApi = (() => {
  async function request(path, options = {}) {
    const response = await fetch(`${BASE_URL}${path}`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
      ...options,
    });

    const contentType = response.headers.get('content-type') || '';
    const data = contentType.includes('application/json') ? await response.json() : null;
    return { ok: response.ok, status: response.status, data };
  }

  return {
    login(username, password) {
      return request('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      });
    },
    logout() {
      return request('/api/auth/logout', { method: 'POST' });
    },
    uploadFiles(formData) {
      return fetch(`${BASE_URL}/api/uploads/`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      }).then(async (response) => ({ ok: response.ok, status: response.status, data: await response.json() }));
    },
    get(path) {
      return request(path, { method: 'GET' });
    },
    getJson(path) {
      return request(path, { method: 'GET' }).then((result) => result.data);
    },
  };
})();