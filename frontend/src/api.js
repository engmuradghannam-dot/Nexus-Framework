import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true,
});

// Request interceptor to add JWT token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            try {
                const refresh = localStorage.getItem('refresh_token');
                const response = await axios.post(`${API_BASE}/token/refresh/`, { refresh });
                const { access } = response.data;
                localStorage.setItem('access_token', access);
                api.defaults.headers.common['Authorization'] = `Bearer ${access}`;
                originalRequest.headers['Authorization'] = `Bearer ${access}`;
                return api(originalRequest);
            } catch (refreshError) {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }
        return Promise.reject(error);
    }
);

// ==================== AUTH ====================
export const login = (credentials) => api.post('/token/', credentials);
export const refreshToken = (refresh) => api.post('/token/refresh/', { refresh });
export const register = (data) => api.post('/core/auth/register/', data);
export const getMe = () => api.get('/core/auth/me/');
export const logout = () => api.post('/core/auth/logout/');

// ==================== CORE ====================
export const getCompanies = () => api.get('/core/companies/');
export const getBranches = (companyId) => api.get(`/core/branches/by_company/?company_id=${companyId}`);
export const getWarehouses = (branchId) => api.get(`/core/warehouses/by_branch/?branch_id=${branchId}`);
export const getHRProfiles = () => api.get('/core/hr-profiles/');

// ==================== PMO ====================
export const getProjects = () => api.get('/pmo/projects/');
export const getTasks = (projectId) => api.get(`/pmo/tasks/by_project/?project_id=${projectId}`);

// ==================== INDUSTRY / INVENTORY ====================
export const getInventory = () => api.get('/industry/inventory/');
export const getNeedsReorder = () => api.get('/industry/inventory/needs_reorder/');
export const createReorder = (id, supplierId) => api.post(`/industry/inventory/${id}/create_reorder/`, {supplier_id: supplierId});
export const getReorderAlerts = () => api.get('/industry/inventory/reorder_alerts/');
export const triggerReorder = () => api.post('/industry/inventory/trigger_reorder/');

// ==================== AI ====================
export const getAIModels = () => api.get('/ai/models/');
export const createConversation = (data) => api.post('/ai/conversations/create_with_message/', data);
export const sendMessage = (id, content) => api.post(`/ai/conversations/${id}/send_message/`, {content});

// ==================== REGULATORY ====================
export const getRegulations = () => api.get('/regulatory/regulations/');
export const getComplianceChecks = () => api.get('/regulatory/compliance-checks/');

// ==================== HR ====================
export const getEmployees = () => api.get('/hr/employees/');
export const getAttendance = () => api.get('/hr/attendance/');
export const getLeaveRequests = () => api.get('/hr/leave-requests/');
export const getPayrollRuns = () => api.get('/hr/payroll-runs/');

// ==================== E-COMMERCE/POS ====================
export const getCustomers = () => api.get('/ecommerce/customers/');
export const getOrders = () => api.get('/ecommerce/orders/');
export const getPOSSessions = () => api.get('/ecommerce/pos-sessions/');
export const getPOSTransactions = () => api.get('/ecommerce/pos-transactions/');

// ==================== WORKFLOW ====================
export const getWorkflows = () => api.get('/workflow/workflows/');
export const getApprovalRequests = () => api.get('/workflow/approval-requests/');
export const approveRequest = (id, data) => api.post(`/workflow/approval-requests/${id}/approve/`, data);
export const rejectRequest = (id, data) => api.post(`/workflow/approval-requests/${id}/reject/`, data);

// ==================== PERMISSIONS ====================
export const getRoles = () => api.get('/permissions/roles/');
export const getUserRoles = () => api.get('/permissions/user-roles/');
export const getFieldPermissions = () => api.get('/permissions/field-permissions/');
export const getRecordPermissions = () => api.get('/permissions/record-permissions/');
export const getPermissionAudit = () => api.get('/permissions/audit/');

// ==================== ACCOUNTING ====================
export const getChartOfAccounts = () => api.get('/accounting/chart-of-accounts/');
export const getJournalEntries = () => api.get('/accounting/journal-entries/');
export const getInvoices = () => api.get('/accounting/invoices/');
export const getBills = () => api.get('/accounting/bills/');

// ==================== MANUFACTURING ====================
export const getBOMs = () => api.get('/manufacturing/boms/');
export const getProductionOrders = () => api.get('/manufacturing/production-orders/');
export const getWorkCenters = () => api.get('/manufacturing/work-centers/');

export default api;
