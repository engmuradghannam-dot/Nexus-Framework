import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import api from '@/lib/api';

export default function PMODashboard() {
  const [portfolios, setPortfolios] = useState([]);
  const [programs, setPrograms] = useState([]);
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [portRes, progRes, projRes] = await Promise.all([
        api.get('/pmo/portfolios/'),
        api.get('/pmo/programs/'),
        api.get('/pmo/projects/')
      ]);
      setPortfolios(portRes.data.results || portRes.data);
      setPrograms(progRes.data.results || progRes.data);
      setProjects(projRes.data.results || projRes.data);
    } catch (error) {
      console.error('Error fetching PMO data:', error);
    }
  };

  const getProgress = (project) => {
    if (!project.start_date || !project.end_date) return 0;
    const start = new Date(project.start_date);
    const end = new Date(project.end_date);
    const now = new Date();
    if (now > end) return 100;
    if (now < start) return 0;
    return Math.round(((now - start) / (end - start)) * 100);
  };

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold">PMO Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader><CardTitle>Portfolios</CardTitle></CardHeader>
          <CardContent><p className="text-4xl font-bold">{portfolios.length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Programs</CardTitle></CardHeader>
          <CardContent><p className="text-4xl font-bold">{programs.length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Projects</CardTitle></CardHeader>
          <CardContent><p className="text-4xl font-bold">{projects.length}</p></CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Active Projects</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {projects.filter(p => p.status === 'active').map(project => (
            <div key={project.id} className="space-y-2">
              <div className="flex justify-between">
                <span className="font-medium">{project.name}</span>
                <span className="text-sm text-gray-500">{getProgress(project)}%</span>
              </div>
              <Progress value={getProgress(project)} />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
