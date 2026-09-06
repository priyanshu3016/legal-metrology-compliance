import axios from 'axios';

// Base API instance - swap BASE_URL for real backend
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor - attach auth token
api.interceptors.request.use((config) => {
  const user = localStorage.getItem('packcheck_user');
  if (user) {
    config.headers.Authorization = Bearer ;
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

// ─── Inspection Services ────────────────────────────────────────────────────

export const inspectionService = {
  create: (data) => api.post('/inspections', data),
  getAll: (params) => api.get('/inspections', { params }),
  getById: (id) => api.get(/inspections/),
  update: (id, data) => api.put(/inspections/, data),
  addRemarks: (id, remarks) => api.post(/inspections//remarks, { remarks }),
};

// ─── OCR / AI Services ──────────────────────────────────────────────────────

export const ocrService = {
  extractFromImages: (formData) =>
    api.post('/ocr/extract', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  getExtractionStatus: (jobId) => api.get(/ocr/status/),
};

// ─── Compliance Services ────────────────────────────────────────────────────

export const complianceService = {
  check: (extractedData) => api.post('/compliance/check', extractedData),
  getRules: (params) => api.get('/rules', { params }),
  getRuleById: (id) => api.get(/rules/),
};

// ─── Evidence Services ──────────────────────────────────────────────────────

export const evidenceService = {
  upload: (inspectionId, formData) =>
    api.post(/evidence/, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  getByInspection: (inspectionId) => api.get(/evidence/),
};

// ─── Reports Services ───────────────────────────────────────────────────────

export const reportService = {
  generate: (inspectionId) => api.post(/reports//generate),
  download: (inspectionId) => api.get(/reports//download, { responseType: 'blob' }),
};

// ─── Mock API Functions (used when backend unavailable) ────────────────────

import { mockInspections } from '../data/mockInspections';
import { mockRules } from '../data/mockRules';

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
