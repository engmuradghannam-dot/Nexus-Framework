import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

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

export default api;
