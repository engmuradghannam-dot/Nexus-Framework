import axios from 'axios'

// Helper to get CSRF token from cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,  // CRITICAL: Send cookies with every request
})

API.interceptors.request.use((config) => {
  // Add CSRF token for state-changing requests
  if (config.method !== 'get' && config.method !== 'GET') {
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
  }

  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Token ${token}`
  return config
})

API.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default API

// ── Core ─────────────────────────────────────────
export const getUsers = (params) => API.get('/core/users/', { params })
export const getBranches = (params) => API.get('/core/branches/', { params })
export const getWarehouses = (params) => API.get('/core/warehouses/', { params })

// ── PMO ──────────────────────────────────────────
export const getProjects = (params) => API.get('/pmo/projects/', { params })
export const getProjectDashboard = () => API.get('/pmo/projects/dashboard/')
export const getTasks = (params) => API.get('/pmo/tasks/', { params })
export const getMilestones = (params) => API.get('/pmo/milestones/', { params })

// ── Industry ───────────────────────────────────────
export const getSectors = () => API.get('/industry/sectors/')
export const getCompanies = (params) => API.get('/industry/companies/', { params })
export const getCompanyLeaderboard = () => API.get('/industry/companies/leaderboard/')
export const getMetrics = (params) => API.get('/industry/metrics/', { params })

// ── AI ───────────────────────────────────────────
export const getAIModels = (params) => API.get('/ai/models/', { params })
export const getAIDashboard = () => API.get('/ai/models/dashboard/')
export const getPredictions = (params) => API.get('/ai/predictions/', { params })
export const getInsights = (params) => API.get('/ai/insights/', { params })
export const markInsightsRead = () => API.post('/ai/insights/mark_all_read/')

// ── Regulatory ───────────────────────────────────
export const getRegulations = (params) => API.get('/regulatory/regulations/', { params })
export const getRegulatoryDashboard = () => API.get('/regulatory/regulations/dashboard/')
export const getComplianceChecks = (params) => API.get('/regulatory/compliance-checks/', { params })
export const getRisks = (params) => API.get('/regulatory/risks/', { params })
export const getRiskHeatmap = () => API.get('/regulatory/risks/heatmap/')

// ── Taxes ──────────────────────────────────────
export const getTaxProfiles = (params) => API.get('/taxes/profiles/', { params })
export const getTaxProfile = (id) => API.get(`/taxes/profiles/${id}/`)
export const createTaxProfile = (data) => API.post('/taxes/profiles/', data)
export const updateTaxProfile = (id, data) => API.patch(`/taxes/profiles/${id}/`, data)
export const deleteTaxProfile = (id) => API.delete(`/taxes/profiles/${id}/`)
export const getTaxRates = (params) => API.get('/taxes/rates/', { params })
export const getTaxRules = (params) => API.get('/taxes/rules/', { params })
export const calculateTax = (data) => API.post('/taxes/calculations/calculate/', data)
export const getTaxCalculations = (params) => API.get('/taxes/calculations/', { params })

// ── i18n ─────────────────────────────────────────
export const getLanguages = (params) => API.get('/i18n/languages/', { params })
export const getLanguage = (id) => API.get(`/i18n/languages/${id}/`)
export const createLanguage = (data) => API.post('/i18n/languages/', data)
export const updateLanguage = (id, data) => API.patch(`/i18n/languages/${id}/`, data)
export const deleteLanguage = (id) => API.delete(`/i18n/languages/${id}/`)
export const getDefaultLanguage = () => API.get('/i18n/languages/default/')
export const getActiveLanguages = () => API.get('/i18n/languages/active/')
export const getTranslations = (params) => API.get('/i18n/translations/', { params })
export const createTranslation = (data) => API.post('/i18n/translations/', data)
export const updateTranslation = (id, data) => API.patch(`/i18n/translations/${id}/`, data)
export const deleteTranslation = (id) => API.delete(`/i18n/translations/${id}/`)
export const searchTranslations = (q) => API.get(`/i18n/translations/search/?q=${q}`)
export const bulkUploadTranslations = (data) => API.post('/i18n/translations/bulk/', data)
export const getTranslationImportJobs = (params) => API.get('/i18n/import-jobs/', { params })

// ════════════════════════════════════════════════
// Object-style APIs (return response data directly)
// Consolidated from the former api.ts.
// ════════════════════════════════════════════════
const data = (p) => p.then((r) => r.data)
// Unwrap DRF paginated responses ({results:[...]}) to a plain array.
const list = (p) => p.then((r) => (r.data && r.data.results) || r.data || [])

export const authApi = {
  login: (email, password) => data(API.post('/core/auth/login/', { email, password })),
  register: (payload) => data(API.post('/core/auth/register/', payload)),
  googleLogin: (token) => data(API.post('/core/auth/google/', { token })),
  getProfile: () => data(API.get('/core/users/me/')),
  updateProfile: (payload) => data(API.put('/core/users/me/', payload)),
}

export const controlsApi = {
  summary: () => data(API.get('/controls/form-controls/summary/')),
  byForm: () => data(API.get('/controls/form-controls/by_form/')),
  formControls: (formName) =>
    data(API.get('/controls/form-controls/', { params: { form_name: formName, page_size: 500 } })),
  industryControls: () => data(API.get('/controls/industry-controls/')),
  categories: () => data(API.get('/controls/industries/categories/')),
  industries: () => data(API.get('/controls/industries/')),
  sectors: () => data(API.get('/controls/sector-controls/sectors/')),
  sectorControls: (sector) =>
    list(API.get('/controls/sector-controls/', { params: { sector, page_size: 100 } })),
  saveCompanySetup: (payload) => data(API.post('/controls/company-setup/', payload)),
  listCompanySetups: () => list(API.get('/controls/company-setup/')),
}

export const industryApi = {
  getAll: (filters) => list(API.get('/industry/companies/', { params: filters })),
  getById: (id) => data(API.get(`/industry/companies/${id}/`)),
  create: (payload) => data(API.post('/industry/companies/', payload)),
  update: (id, payload) => data(API.put(`/industry/companies/${id}/`, payload)),
  delete: (id) => data(API.delete(`/industry/companies/${id}/`)),
}

export const projectApi = {
  getAll: (filters) => list(API.get('/pmo/projects/', { params: filters })),
  getById: (id) => data(API.get(`/pmo/projects/${id}/`)),
  create: (payload) => data(API.post('/pmo/projects/', payload)),
  update: (id, payload) => data(API.put(`/pmo/projects/${id}/`, payload)),
  delete: (id) => data(API.delete(`/pmo/projects/${id}/`)),
}

export const chatApi = {
  sendMessage: (message, model, settings) =>
    data(API.post('/chat/send/', { message, model, settings })),
  getHistory: (sessionId) => data(API.get(`/chat/history/${sessionId || ''}`)),
  getModels: () => data(API.get('/chat/models/')),
  clearHistory: (sessionId) => data(API.delete(`/chat/clear/${sessionId || ''}`)),
}

// ════════ Generic module records (real CRUD) ════════
export const recordsApi = {
  list: (module) => list(API.get('/records/', { params: { module, page_size: 500 } })),
  lowStock: () => data(API.get('/records/low_stock/')),
  create: (module, payload) => data(API.post('/records/', { module, data: payload })),
  update: (id, module, payload) => data(API.put(`/records/${id}/`, { module, data: payload })),
  remove: (id) => API.delete(`/records/${id}/`),
}

// ════════ Accounting ════════
export const accountingApi = {
  accounts: () => list(API.get('/accounts/accounts/', { params: { page_size: 200 } })),
  trialBalance: () => data(API.get('/accounts/accounts/trial_balance/')),
  financialStatements: () => data(API.get('/accounts/accounts/financial_statements/')),
  journalEntries: () => list(API.get('/accounts/journal-entries/', { params: { page_size: 200 } })),
  generalLedger: (id) => data(API.get(`/accounts/accounts/${id}/general_ledger/`)),
}

// ════════ Audit trail ════════
export const auditApi = {
  logs: (params = {}) => list(API.get('/audit/logs/', { params: { page_size: 200, ...params } })),
}

// ════════ Invoicing ════════
export const invoicingApi = {
  list: () => list(API.get('/invoicing/invoices/', { params: { page_size: 200 } })),
  create: (payload) => data(API.post('/invoicing/invoices/', payload)),
  post: (id) => data(API.post(`/invoicing/invoices/${id}/post_to_ledger/`)),
}

// ════════ RBAC (roles & permissions) ════════
export const rbacApi = {
  roles: () => list(API.get('/rbac/roles/')),
  catalog: () => data(API.get('/rbac/roles/catalog/')),
  updateRole: (id, permissions) => data(API.patch(`/rbac/roles/${id}/`, { permissions })),
  myPermissions: () => data(API.get('/rbac/roles/my_permissions/')),
}

// ════════ Tax templates (ZATCA) ════════
export const taxApi = {
  templates: () => data(API.get('/taxes/templates/')),
}

// ════════ Attendance & Timesheets ════════
export const attendanceApi = {
  attendance: () => list(API.get('/hr/attendance/', { params: { page_size: 200 } })),
  timesheets: () => list(API.get('/hr/timesheets/', { params: { page_size: 200 } })),
  createAttendance: (payload) => data(API.post('/hr/attendance/', payload)),
  createTimesheet: (payload) => data(API.post('/hr/timesheets/', payload)),
}

// ════════ Two-factor auth ════════
export const twofaApi = {
  status: () => data(API.get('/security/2fa/status/')),
  setup: () => data(API.post('/security/2fa/setup/')),
  verify: (code) => data(API.post('/security/2fa/verify/', { code })),
  disable: () => data(API.post('/security/2fa/disable/')),
}

// ════════ Stock valuation ════════
export const stockApi = {
  valuation: () => data(API.get('/stock/movements/valuation/')),
  movements: () => list(API.get('/stock/movements/', { params: { page_size: 300 } })),
}

// ════════ Trade documents ════════
export const tradeApi = {
  list: () => list(API.get('/trade/documents/', { params: { page_size: 200 } })),
  create: (payload) => data(API.post('/trade/documents/', payload)),
  process: (id) => data(API.post(`/trade/documents/${id}/process/`)),
}
