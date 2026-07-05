import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Token ${token}`
  }
  return config
})

export const fetchPurchaseOrders = () => api.get('/purchase-orders/').then(r => r.data)
export const fetchSalesOrders = () => api.get('/sales-orders/').then(r => r.data)
export const fetchEmployees = () => api.get('/employees/').then(r => r.data)
export const fetchCompanies = () => api.get('/companies/').then(r => r.data)
export const fetchSuppliers = () => api.get('/suppliers/').then(r => r.data)
export const fetchCustomers = () => api.get('/customers/').then(r => r.data)
export const fetchWorkOrders = () => api.get('/work-orders/').then(r => r.data)
export const fetchItems = () => api.get('/items/').then(r => r.data)
export const fetchAccounts = () => api.get('/accounts/').then(r => r.data)
export const fetchProjects = () => api.get('/projects/').then(r => r.data)
export const fetchAssets = () => api.get('/assets/').then(r => r.data)
export const fetchLeads = () => api.get('/leads/').then(r => r.data)

export default api
