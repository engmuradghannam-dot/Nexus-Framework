import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true,
});

// Core
export const getCompanies = () => api.get('/core/companies/');
export const getBranches = (companyId) => api.get(`/core/branches/by_company/?company_id=${companyId}`);
export const getWarehouses = (branchId) => api.get(`/core/warehouses/by_branch/?branch_id=${branchId}`);
export const getHRProfiles = () => api.get('/core/hr-profiles/');

// PMO
export const getProjects = () => api.get('/pmo/projects/');
export const getTasks = (projectId) => api.get(`/pmo/tasks/by_project/?project_id=${projectId}`);

// Industry
export const getInventory = () => api.get('/industry/inventory/');
export const getNeedsReorder = () => api.get('/industry/inventory/needs_reorder/');
export const createReorder = (id, supplierId) => api.post(`/industry/inventory/${id}/create_reorder/`, {supplier_id: supplierId});

// AI
export const getAIModels = () => api.get('/ai/models/');
export const createConversation = (data) => api.post('/ai/conversations/create_with_message/', data);
export const sendMessage = (id, content) => api.post(`/ai/conversations/${id}/send_message/`, {content});

// Regulatory
export const getRegulations = () => api.get('/regulatory/regulations/');
export const getComplianceChecks = () => api.get('/regulatory/compliance-checks/');


// HR
export const getEmployees = () => api.get('/hr/employees/');
export const getAttendance = () => api.get('/hr/attendance/');
export const getLeaveRequests = () => api.get('/hr/leave-requests/');
export const getPayrollRuns = () => api.get('/hr/payroll-runs/');

// E-commerce/POS
export const getCustomers = () => api.get('/ecommerce/customers/');
export const getOrders = () => api.get('/ecommerce/orders/');
export const getPOSSessions = () => api.get('/ecommerce/pos-sessions/');
export const getPOSTransactions = () => api.get('/ecommerce/pos-transactions/');

// Workflow
export const getWorkflows = () => api.get('/workflow/workflows/');
export const getApprovalRequests = () => api.get('/workflow/approval-requests/');
export const approveRequest = (id, data) => api.post(`/workflow/approval-requests/${id}/approve/`, data);
export const rejectRequest = (id, data) => api.post(`/workflow/approval-requests/${id}/reject/`, data);

// Permissions
export const getRoles = () => api.get('/permissions/roles/');
export const getUserRoles = () => api.get('/permissions/user-roles/');
export const getFieldPermissions = () => api.get('/permissions/field-permissions/');
export const getRecordPermissions = () => api.get('/permissions/record-permissions/');
export const getPermissionAudit = () => api.get('/permissions/audit/');

export default api;
