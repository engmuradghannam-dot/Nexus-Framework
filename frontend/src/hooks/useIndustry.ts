// hooks/useIndustry.ts
import { useState, useCallback, useEffect } from 'react';
import { IndustryFormData } from '../components/Industry/IndustryFormModal';
import { ProjectFormData } from '../components/PMO/ProjectFormModal';
import { industryApi, projectApi } from '../services/api';

export function useIndustry() {
  const [industries, setIndustries] = useState<IndustryFormData[]>([]);
  const [projects, setProjects] = useState<ProjectFormData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load data on mount
  useEffect(() => {
    fetchIndustries();
    fetchProjects();
  }, []);

  const fetchIndustries = useCallback(async () => {
    setLoading(true);
    try {
      const data = await industryApi.getAll();
      setIndustries(data);
    } catch (err) {
      setError('Failed to load industries');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    try {
      const data = await projectApi.getAll();
      setProjects(data);
    } catch (err) {
      setError('Failed to load projects');
    } finally {
      setLoading(false);
    }
  }, []);

  // Industry CRUD
  const createIndustry = useCallback(async (data: IndustryFormData) => {
    try {
      const newIndustry = await industryApi.create(data);
      setIndustries(prev => [...prev, newIndustry]);
    } catch (err) {
      setError('Failed to create industry');
    }
  }, []);

  const updateIndustry = useCallback(async (id: string, data: IndustryFormData) => {
    try {
      const updated = await industryApi.update(id, data);
      setIndustries(prev => prev.map(i => i.id === id ? updated : i));
    } catch (err) {
      setError('Failed to update industry');
    }
  }, []);

  const deleteIndustry = useCallback(async (id: string) => {
    try {
      await industryApi.delete(id);
      setIndustries(prev => prev.filter(i => i.id !== id));
    } catch (err) {
      setError('Failed to delete industry');
    }
  }, []);

  // Project CRUD
  const createProject = useCallback(async (data: ProjectFormData) => {
    try {
      const newProject = await projectApi.create(data);
      setProjects(prev => [...prev, newProject]);
    } catch (err) {
      setError('Failed to create project');
    }
  }, []);

  const updateProject = useCallback(async (id: string, data: ProjectFormData) => {
    try {
      const updated = await projectApi.update(id, data);
      setProjects(prev => prev.map(p => p.id === id ? updated : p));
    } catch (err) {
      setError('Failed to update project');
    }
  }, []);

  const deleteProject = useCallback(async (id: string) => {
    try {
      await projectApi.delete(id);
      setProjects(prev => prev.filter(p => p.id !== id));
    } catch (err) {
      setError('Failed to delete project');
    }
  }, []);

  return {
    industries,
    projects,
    loading,
    error,
    createIndustry,
    updateIndustry,
    deleteIndustry,
    createProject,
    updateProject,
    deleteProject,
    refreshIndustries: fetchIndustries,
    refreshProjects: fetchProjects
  };
}
