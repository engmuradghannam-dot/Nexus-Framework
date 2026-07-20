import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true,
    // Read Django's csrftoken cookie and echo it back as X-CSRFToken on
    // unsafe requests (POST/PUT/PATCH/DELETE) - required by Django's CSRF
    // protection when auth is session-cookie based, as it is here.
    xsrfCookieName: 'csrftoken',
    xsrfHeaderName: 'X-CSRFToken',
    // axios only does this automatically for same-origin requests by
    // default; the API is on a different origin (port) than the SPA.
    withXSRFToken: true,
});

// DRF's default pagination wraps every list response as
// {count, next, previous, results: [...]}. Pages here were written against
// plain arrays, so unwrap that envelope transparently in one place rather
// than touching every call site - and every DataGrid `rows={...}` prop that
// currently receives an object instead of an array.
api.interceptors.response.use((response) => {
    const { data } = response;
    if (
        data && typeof data === 'object' && !Array.isArray(data) &&
        Array.isArray(data.results) &&
        ['count', 'next', 'previous'].every((key) => key in data)
    ) {
        response.data = data.results;
    }
    return response;
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


// Accounting
export const getChartOfAccounts = () => api.get('/accounting/chart-of-accounts/');
export const getJournalEntries = () => api.get('/accounting/journal-entries/');
export const getInvoices = () => api.get('/accounting/invoices/');
export const getPayments = () => api.get('/accounting/payments/');
export const getFinancialReports = () => api.get('/accounting/financial-reports/');
export const getInvoiceStats = () => api.get('/accounting/invoices/dashboard_stats/');

export { api };
export default api;


// Manufacturing
export const getWorkCenters = () => api.get('/manufacturing/work-centers/');
export const getBOMs = () => api.get('/manufacturing/boms/');
export const getRoutings = () => api.get('/manufacturing/routings/');
export const getManufacturingOrders = () => api.get('/manufacturing/manufacturing-orders/');
export const createManufacturingOrder = (data) => api.post('/manufacturing/manufacturing-orders/', data);
export const releaseOrder = (id) => api.post(`/manufacturing/manufacturing-orders/${id}/release/`);
export const startOrder = (id) => api.post(`/manufacturing/manufacturing-orders/${id}/start/`);
export const completeOrder = (id) => api.post(`/manufacturing/manufacturing-orders/${id}/complete/`);
export const cancelOrder = (id) => api.post(`/manufacturing/manufacturing-orders/${id}/cancel/`);
export const produceOrder = (id, data) => api.post(`/manufacturing/manufacturing-orders/${id}/produce/`, data);
export const getMaterialRequisitions = () => api.get('/manufacturing/material-requisitions/');
export const approveRequisition = (id) => api.post(`/manufacturing/material-requisitions/${id}/approve/`);
export const issueRequisition = (id, data) => api.post(`/manufacturing/material-requisitions/${id}/issue/`, data);
export const getManufacturingStats = () => api.get('/manufacturing/manufacturing-orders/dashboard_stats/');
