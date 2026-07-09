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
