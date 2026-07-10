// services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Generic fetch wrapper
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// ========== CHAT API ==========
export const chatApi = {
  sendMessage: (message: string, model?: string, settings?: Record<string, any>) =>
    fetchApi<{ response: string; messageId: string }>('/chat/send/', {
      method: 'POST',
      body: JSON.stringify({ message, model, settings }),
    }),

  getHistory: (sessionId?: string) =>
    fetchApi<Array<{ role: string; content: string; timestamp: string }>>(`/chat/history/${sessionId || ''}`),

  getModels: () =>
    fetchApi<Array<{ id: string; name: string; provider: string }>>('/chat/models/'),

  clearHistory: (sessionId?: string) =>
    fetchApi<void>(`/chat/clear/${sessionId || ''}`, { method: 'DELETE' }),
};

// ========== INDUSTRY API ==========
export const industryApi = {
  getAll: (filters?: Record<string, string>) => {
    const query = filters ? `?${new URLSearchParams(filters).toString()}` : '';
    return fetchApi<any[]>(`/industries/${query}`);
  },

  getById: (id: string) =>
    fetchApi<any>(`/industries/${id}/`),

  create: (data: any) =>
    fetchApi<any>('/industries/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: any) =>
    fetchApi<any>(`/industries/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    fetchApi<void>(`/industries/${id}/`, { method: 'DELETE' }),

  search: (query: string) =>
    fetchApi<any[]>(`/industries/search/?q=${encodeURIComponent(query)}`),

  export: (format: 'csv' | 'xlsx' = 'csv') =>
    fetch(`/api/industries/export/?format=${format}`),

  import: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetchApi<any>('/industries/import/', {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    });
  },
};

// ========== PROJECT API (PMO) ==========
export const projectApi = {
  getAll: (filters?: Record<string, string>) => {
    const query = filters ? `?${new URLSearchParams(filters).toString()}` : '';
    return fetchApi<any[]>(`/projects/${query}`);
  },

  getById: (id: string) =>
    fetchApi<any>(`/projects/${id}/`),

  create: (data: any) =>
    fetchApi<any>('/projects/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: any) =>
    fetchApi<any>(`/projects/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    fetchApi<void>(`/projects/${id}/`, { method: 'DELETE' }),

  updateStatus: (id: string, status: string) =>
    fetchApi<any>(`/projects/${id}/status/`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),

  updateProgress: (id: string, progress: number) =>
    fetchApi<any>(`/projects/${id}/progress/`, {
      method: 'PATCH',
      body: JSON.stringify({ progress }),
    }),

  addMilestone: (id: string, milestone: any) =>
    fetchApi<any>(`/projects/${id}/milestones/`, {
      method: 'POST',
      body: JSON.stringify(milestone),
    }),

  getTimeline: (id: string) =>
    fetchApi<any>(`/projects/${id}/timeline/`),

  getDashboard: () =>
    fetchApi<any>('/projects/dashboard/'),

  export: (format: 'csv' | 'xlsx' | 'pdf' = 'csv') =>
    fetch(`/api/projects/export/?format=${format}`),
};

// ========== AUTH API ==========
export const authApi = {
  login: (email: string, password: string) =>
    fetchApi<{ token: string; user: any }>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (data: any) =>
    fetchApi<{ token: string; user: any }>('/auth/register/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  googleLogin: (token: string) =>
    fetchApi<{ token: string; user: any }>('/auth/google/', {
      method: 'POST',
      body: JSON.stringify({ token }),
    }),

  getProfile: () =>
    fetchApi<any>('/auth/profile/'),

  updateProfile: (data: any) =>
    fetchApi<any>('/auth/profile/', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
};

export default { chatApi, industryApi, projectApi, authApi };
