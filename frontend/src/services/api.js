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
  aging: (type) => data(API.get("/invoicing/invoices/aging/", { params: { type } })),
  zatcaQr: (id) => data(API.get(`/invoicing/invoices/${id}/zatca_qr/`)),
  recordPayment: (id, amount) => data(API.post(`/invoicing/invoices/${id}/record_payment/`, { amount })),
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
  transfer: (payload) => data(API.post("/stock/movements/transfer/", payload)),
  valuation: () => data(API.get('/stock/movements/valuation/')),
  movements: () => list(API.get('/stock/movements/', { params: { page_size: 300 } })),
}

// ════════ Trade documents ════════
export const tradeApi = {
  list: () => list(API.get('/trade/documents/', { params: { page_size: 200 } })),
  create: (payload) => data(API.post('/trade/documents/', payload)),
  process: (id) => data(API.post(`/trade/documents/${id}/process/`)),
}

// ════════ Depreciation ════════
export const depreciationApi = {
  assets: () => list(API.get('/depreciation/assets/', { params: { page_size: 200 } })),
  schedule: (id) => data(API.get(`/depreciation/assets/${id}/schedule/`)),
}

// ════════ Banking & reconciliation ════════
export const bankingApi = {
  accounts: () => list(API.get('/banking/accounts/', { params: { page_size: 100 } })),
  transactions: (account) => list(API.get('/banking/transactions/', { params: { account, page_size: 300 } })),
  toggleReconcile: (id) => data(API.post(`/banking/transactions/${id}/toggle_reconcile/`)),
}

// ════════ Tenants (multi-tenancy) ════════
export const tenantsApi = {
  list: () => list(API.get('/tenancy/tenants/', { params: { page_size: 100 } })),
  current: () => data(API.get('/tenancy/tenants/current/')),
  create: (payload) => data(API.post('/tenancy/tenants/', payload)),
  update: (id, payload) => data(API.patch(`/tenancy/tenants/${id}/`, payload)),
}

// ════════ Currencies / FX ════════
export const currenciesApi = {
  list: () => data(API.get('/fx/currencies/')),
  convert: (amount, from, to) => data(API.get('/fx/currencies/convert/', { params: { amount, from, to } })),
  update: (id, payload) => data(API.patch(`/fx/currencies/${id}/`, payload)),
}

// ════════ Custom fields ════════
export const customFieldsApi = {
  list: (module) => data(API.get('/customfields/fields/', { params: module ? { module } : {} })),
  create: (payload) => data(API.post('/customfields/fields/', payload)),
  remove: (id) => API.delete(`/customfields/fields/${id}/`),
}

// ════════ Pricing rules ════════
export const pricingApi = {
  list: () => list(API.get('/pricing/rules/', { params: { page_size: 200 } })),
  create: (payload) => data(API.post('/pricing/rules/', payload)),
  remove: (id) => API.delete(`/pricing/rules/${id}/`),
  quote: (params) => data(API.get('/pricing/rules/quote/', { params })),
}

// ════════ Purchasing cycle ════════
export const purchasingApi = {
  list: () => list(API.get('/purchasing/documents/', { params: { page_size: 200 } })),
  create: (payload) => data(API.post('/purchasing/documents/', payload)),
  process: (id) => data(API.post(`/purchasing/documents/${id}/process/`)),
}

// ════════ Report builder ════════
export const reportsApi = {
  list: () => list(API.get('/reports/definitions/', { params: { page_size: 100 } })),
  create: (payload) => data(API.post('/reports/definitions/', payload)),
  remove: (id) => API.delete(`/reports/definitions/${id}/`),
  run: (id) => data(API.get(`/reports/definitions/${id}/run/`)),
  preview: (payload) => data(API.post('/reports/definitions/preview/', payload)),
}

// ════════ Notifications (email/SMS) ════════
export const notificationsApi = {
  templates: () => list(API.get('/notifications/templates/', { params: { page_size: 100 } })),
  createTemplate: (payload) => data(API.post('/notifications/templates/', payload)),
  removeTemplate: (id) => API.delete(`/notifications/templates/${id}/`),
  send: (id, payload) => data(API.post(`/notifications/templates/${id}/send/`, payload)),
  log: () => list(API.get('/notifications/log/', { params: { page_size: 200 } })),
}

// ════════ HR extras ════════
export const hrExtrasApi = {
  claims: () => list(API.get('/hr-extras/expense-claims/', { params: { page_size: 200 } })),
  createClaim: (p) => data(API.post('/hr-extras/expense-claims/', p)),
  claimStatus: (id, status) => data(API.post(`/hr-extras/expense-claims/${id}/set_status/`, { status })),
  loans: () => list(API.get('/hr-extras/loans/', { params: { page_size: 200 } })),
  createLoan: (p) => data(API.post('/hr-extras/loans/', p)),
  payInstallment: (id) => data(API.post(`/hr-extras/loans/${id}/pay_installment/`)),
  openings: () => list(API.get('/hr-extras/job-openings/', { params: { page_size: 100 } })),
  createOpening: (p) => data(API.post('/hr-extras/job-openings/', p)),
  applicants: (opening) => list(API.get('/hr-extras/applicants/', { params: { opening, page_size: 200 } })),
  createApplicant: (p) => data(API.post('/hr-extras/applicants/', p)),
  appraisals: () => list(API.get('/hr-extras/appraisals/', { params: { page_size: 200 } })),
  createAppraisal: (p) => data(API.post('/hr-extras/appraisals/', p)),
  eos: (params) => data(API.get('/hr-extras/end-of-service/', { params })),
}

// ════════ UOM & variants ════════
export const uomApi = {
  units: () => data(API.get('/uom/units/')),
  createUnit: (p) => data(API.post('/uom/units/', p)),
  convert: (amount, from, to) => data(API.get('/uom/units/convert/', { params: { amount, from, to } })),
  conversions: () => data(API.get('/uom/conversions/')),
  createConversion: (p) => data(API.post('/uom/conversions/', p)),
  variants: (template_code) => list(API.get('/uom/variants/', { params: { template_code, page_size: 500 } })),
  generate: (p) => data(API.post('/uom/variants/generate/', p)),
}

// ════════ Automation (scheduled jobs + webhooks) ════════
export const automationApi = {
  jobs: () => list(API.get('/automation/jobs/', { params: { page_size: 200 } })),
  createJob: (p) => data(API.post('/automation/jobs/', p)),
  runJob: (id) => data(API.post(`/automation/jobs/${id}/run/`)),
  webhooks: () => list(API.get('/automation/webhooks/', { params: { page_size: 200 } })),
  createWebhook: (p) => data(API.post('/automation/webhooks/', p)),
  triggerWebhook: (id, payload) => data(API.post(`/automation/webhooks/${id}/trigger/`, { payload })),
  deliveries: () => list(API.get('/automation/deliveries/', { params: { page_size: 200 } })),
}

// ════════ Inventory: items, item groups, stock entries ════════
export const itemsApi = {
  list: () => list(API.get('/inventory/items/', { params: { page_size: 500 } })),
  create: (p) => data(API.post('/inventory/items/', p)),
  update: (id, p) => data(API.patch(`/inventory/items/${id}/`, p)),
  remove: (id) => API.delete(`/inventory/items/${id}/`),
}

export const itemGroupsApi = {
  list: () => list(API.get('/inventory/item-groups/', { params: { page_size: 200 } })),
  create: (p) => data(API.post('/inventory/item-groups/', p)),
}

export const stockEntriesApi = {
  list: (filters) => list(API.get('/inventory/stock-entries/', { params: { page_size: 200, ...filters } })),
  create: (p) => data(API.post('/inventory/stock-entries/', p)),
}

// ════════ Core: company profiles, branches, warehouses ════════
export const companyProfilesApi = {
  list: () => list(API.get('/core/companies/', { params: { page_size: 100 } })),
}

export const branchesApi = {
  list: () => list(API.get('/core/branches/', { params: { page_size: 200 } })),
  create: (p) => data(API.post('/core/branches/', p)),
}

export const warehousesApi = {
  list: () => list(API.get('/core/warehouses/', { params: { page_size: 200 } })),
  create: (p) => data(API.post('/core/warehouses/', p)),
}

// ════════ Selling: customers + sales order cycle ════════
export const customersApi = {
  list: () => list(API.get('/selling/customers/', { params: { page_size: 200 } })),
  create: (p) => data(API.post('/selling/customers/', p)),
}

export const sellingApi = {
  orders: (filters) => list(API.get('/selling/sales-orders/', { params: { page_size: 200, ...filters } })),
  getOrder: (id) => data(API.get(`/selling/sales-orders/${id}/`)),
  createOrder: (p) => data(API.post('/selling/sales-orders/', p)),
  updateOrder: (id, p) => data(API.patch(`/selling/sales-orders/${id}/`, p)),
  deleteOrder: (id) => API.delete(`/selling/sales-orders/${id}/`),
  items: (soId) => list(API.get('/selling/sales-order-items/', { params: { sales_order: soId, page_size: 200 } })),
  addItem: (p) => data(API.post('/selling/sales-order-items/', p)),
  removeItem: (id) => API.delete(`/selling/sales-order-items/${id}/`),
  taxCharges: (soId) => list(API.get('/selling/sales-tax-charges/', { params: { sales_order: soId } })),
  addTaxCharge: (p) => data(API.post('/selling/sales-tax-charges/', p)),
  removeTaxCharge: (id) => API.delete(`/selling/sales-tax-charges/${id}/`),
  payments: (soId) => list(API.get('/selling/sales-payments/', { params: { sales_order: soId } })),
  addPayment: (p) => data(API.post('/selling/sales-payments/', p)),
}

// ════════ Buying: suppliers + purchase order cycle ════════
export const suppliersApi = {
  list: () => list(API.get('/buying/suppliers/', { params: { page_size: 200 } })),
  create: (p) => data(API.post('/buying/suppliers/', p)),
}

export const buyingApi = {
  orders: (filters) => list(API.get('/buying/purchase-orders/', { params: { page_size: 200, ...filters } })),
  getOrder: (id) => data(API.get(`/buying/purchase-orders/${id}/`)),
  createOrder: (p) => data(API.post('/buying/purchase-orders/', p)),
  updateOrder: (id, p) => data(API.patch(`/buying/purchase-orders/${id}/`, p)),
  deleteOrder: (id) => API.delete(`/buying/purchase-orders/${id}/`),
  items: (poId) => list(API.get('/buying/purchase-order-items/', { params: { purchase_order: poId, page_size: 200 } })),
  addItem: (p) => data(API.post('/buying/purchase-order-items/', p)),
  removeItem: (id) => API.delete(`/buying/purchase-order-items/${id}/`),
  taxCharges: (poId) => list(API.get('/buying/purchase-tax-charges/', { params: { purchase_order: poId } })),
  addTaxCharge: (p) => data(API.post('/buying/purchase-tax-charges/', p)),
  removeTaxCharge: (id) => API.delete(`/buying/purchase-tax-charges/${id}/`),
  payments: (poId) => list(API.get('/buying/purchase-payments/', { params: { purchase_order: poId } })),
  addPayment: (p) => data(API.post('/buying/purchase-payments/', p)),
}

// ════════ HR: employees, departments, leave, payroll ════════
export const hrApi = {
  employees: () => list(API.get('/hr/employees/', { params: { page_size: 200 } })),
  createEmployee: (p) => data(API.post('/hr/employees/', p)),
  departments: () => list(API.get('/hr/departments/', { params: { page_size: 100 } })),
  createDepartment: (p) => data(API.post('/hr/departments/', p)),
  leaveRequests: () => list(API.get('/hr/leave-requests/', { params: { page_size: 200 } })),
  createLeaveRequest: (p) => data(API.post('/hr/leave-requests/', p)),
  updateLeaveRequest: (id, p) => data(API.patch(`/hr/leave-requests/${id}/`, p)),
  payrolls: () => list(API.get('/hr/payrolls/', { params: { page_size: 200 } })),
  createPayroll: (p) => data(API.post('/hr/payrolls/', p)),
  updatePayroll: (id, p) => data(API.patch(`/hr/payrolls/${id}/`, p)),
}

// ════════ CRM: leads + opportunities ════════
export const crmApi = {
  leads: () => list(API.get('/crm/leads/', { params: { page_size: 200 } })),
  createLead: (p) => data(API.post('/crm/leads/', p)),
  updateLead: (id, p) => data(API.patch(`/crm/leads/${id}/`, p)),
  opportunities: () => list(API.get('/crm/opportunities/', { params: { page_size: 200 } })),
  createOpportunity: (p) => data(API.post('/crm/opportunities/', p)),
  updateOpportunity: (id, p) => data(API.patch(`/crm/opportunities/${id}/`, p)),
}
