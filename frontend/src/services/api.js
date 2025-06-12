import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API functions
export const apiService = {
  // Health check
  async healthCheck() {
    const response = await api.get('/health');
    return response.data;
  },

  // Scans
  async startScan(scanRequest = {}) {
    const response = await api.post('/scans', scanRequest);
    return response.data;
  },

  async getScanStatus(scanId) {
    const response = await api.get(`/scans/${scanId}/status`);
    return response.data;
  },

  async getScanResults(scanId) {
    const response = await api.get(`/scans/${scanId}/results`);
    return response.data;
  },

  async listScans() {
    const response = await api.get('/scans');
    return response.data;
  },

  async deleteScan(scanId) {
    const response = await api.delete(`/scans/${scanId}`);
    return response.data;
  },

  // Dashboard
  async getDashboardSummary() {
    const response = await api.get('/dashboard/summary');
    return response.data;
  },

  async getWasteByType() {
    const response = await api.get('/dashboard/waste-by-type');
    return response.data;
  },

  // Fixes
  async applyFixes(scanId, fixIndices, dryRun = true) {
    const response = await api.post(`/scans/${scanId}/fixes`, {
      finding_ids: fixIndices,
      dry_run: dryRun
    });
    return response.data;
  },
};

export default api; 