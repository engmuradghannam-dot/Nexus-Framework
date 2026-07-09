import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import api from '@/lib/api';

export default function IndustryDashboard() {
  const [projects, setProjects] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [projectsRes, metricsRes] = await Promise.all([
        api.get('/industry/projects/'),
        api.get('/industry/metrics/')
      ]);
      setProjects(projectsRes.data.results || projectsRes.data);
      setMetrics(metricsRes.data.results || metricsRes.data);
    } catch (error) {
      console.error('Error fetching industry data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      active: 'bg-green-500',
      completed: 'bg-blue-500',
      on_hold: 'bg-yellow-500',
      cancelled: 'bg-red-500'
    };
    return colors[status] || 'bg-gray-500';
  };

  if (loading) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-3xl font-bold">Industry Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader><CardTitle>Total Projects</CardTitle></CardHeader>
          <CardContent><p className="text-4xl font-bold">{projects.length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Avg Efficiency</CardTitle></CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">
              {metrics.length > 0 
                ? (metrics.reduce((a, m) => a + (m.efficiency_score || 0), 0) / metrics.length).toFixed(1)
                : 0}%
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Compliance Rate</CardTitle></CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-green-600">
              {metrics.length > 0
                ? (metrics.reduce((a, m) => a + (m.compliance_rate || 0), 0) / metrics.length).toFixed(1)
                : 0}%
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Industry Projects</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Sector</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Budget</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {projects.map(project => (
                <TableRow key={project.id}>
                  <TableCell className="font-medium">{project.name}</TableCell>
                  <TableCell>{project.sector}</TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(project.status)}>{project.status}</Badge>
                  </TableCell>
                  <TableCell>${project.budget?.toLocaleString()}</TableCell>
                  <TableCell><Button variant="outline" size="sm">View</Button></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
