import axios from 'axios';
import { mockInspections } from '../data/mockInspections';
import { mockRules } from '../data/mockRules';

// Base API instance - swap BASE_URL for real backend
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor - attach auth token
api.interceptors.request.use((config) => {
  const userStr = localStorage.getItem('packcheck_user');
  if (userStr) {
    try {
      const user = JSON.parse(userStr);
      if (user?.token) {
        config.headers.Authorization = `Bearer ${user.token}`;
      }
    } catch (_) {
      // Ignore parse error
    }
  }
  return config;
});

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('packcheck_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ─── Full Inspection Service (Single-Shot AI + Compliance Pipeline) ─────────

export const inspectService = {
  run: (formData) =>
    api.post('/v1/inspect', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000, // 2 min timeout for OCR processing
    }),
};

// ─── Inspection Services ────────────────────────────────────────────────────

export const inspectionService = {
  create: (data) => api.post('/v1/inspections', data),
  getAll: (params) => api.get('/v1/inspections', { params }),
  getById: (id) => api.get(`/v1/inspections/${id}`),
  update: (id, data) => api.put(`/v1/inspections/${id}`, data),
  addRemarks: (id, remarks) => api.post(`/v1/inspections/${id}/remarks`, { remarks }),
};

// ─── OCR / AI Services ──────────────────────────────────────────────────────

export const ocrService = {
  extractFromImages: (formData) =>
    api.post('/ocr/extract', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  getExtractionStatus: (jobId) => api.get(`/ocr/status/${jobId}`),
};

// ─── Compliance Services ────────────────────────────────────────────────────

export const complianceService = {
  check: (extractedData) => api.post('/compliance/check', extractedData),
  getRules: (params) => api.get('/rules', { params }),
  getRuleById: (id) => api.get(`/rules/${id}`),
};

// ─── Evidence Services ──────────────────────────────────────────────────────

export const evidenceService = {
  upload: (inspectionId, formData) =>
    api.post(`/evidence/${inspectionId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  getByInspection: (inspectionId) => api.get(`/evidence/${inspectionId}`),
};

// ─── Reports Services ───────────────────────────────────────────────────────

export const reportService = {
  generate: (inspectionId) => api.post(`/reports/${inspectionId}/generate`),
  download: (inspectionId) => api.get(`/reports/${inspectionId}/download`, { responseType: 'blob' }),
};

// ─── Mock API Functions (used when backend unavailable) ────────────────────

const delay = (ms) => new Promise((res) => setTimeout(res, ms));

export const mockApi = {
  getInspections: async (filters = {}) => {
    await delay(600);
    let results = [...mockInspections];
    if (filters.status) results = results.filter((i) => i.status === filters.status);
    if (filters.search) {
      const q = filters.search.toLowerCase();
      results = results.filter(
        (i) =>
          i.product.toLowerCase().includes(q) ||
          i.manufacturer.toLowerCase().includes(q) ||
          i.id.toLowerCase().includes(q)
      );
    }
    return results;
  },

  getInspectionById: async (id) => {
    await delay(400);
    return mockInspections.find((i) => i.id === id) || null;
  },

  runOcrAndCompliance: async (images) => {
    await delay(3000);
    // Returns mock AI response - replace with real API call
    return mockInspections[0];
  },

  getRules: async (filters = {}) => {
    await delay(500);
    let results = [...mockRules];
    if (filters.category) results = results.filter((r) => r.category === filters.category);
    if (filters.search) {
      const q = filters.search.toLowerCase();
      results = results.filter(
        (r) => r.name.toLowerCase().includes(q) || r.description.toLowerCase().includes(q)
      );
    }
    return results;
  },
};

export default api;
