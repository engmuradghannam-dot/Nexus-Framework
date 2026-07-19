import React, { useState, useEffect } from 'react';
import { Box, Grid, Paper, Typography, Chip } from '@mui/material';
import {
  Business, AccountTree, Inventory, Warning,
  Gavel, Psychology, TrendingUp
} from '@mui/icons-material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { getCompanies, getProjects, getInventory, getNeedsReorder, getRegulations } from '../api';

const COLORS = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe'];

export default function Dashboard() {
  const [stats, setStats] = useState({
    companies: 0, projects: 0, inventory: 0,
    reorder: 0, regulations: 0, loading: true
  });
  const [projectStatus, setProjectStatus] = useState([]);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const [companies, projects, inventory, reorder, regulations] = await Promise.all([
        getCompanies(), getProjects(), getInventory(),
        getNeedsReorder(), getRegulations()
      ]);

      const statusCounts = {};
      projects.data.forEach(p => {
        statusCounts[p.status] = (statusCounts[p.status] || 0) + 1;
      });

      setStats({
        companies: companies.data.length,
        projects: projects.data.length,
        inventory: inventory.data.length,
        reorder: reorder.data.length,
        regulations: regulations.data.length,
        loading: false
      });

      setProjectStatus(Object.entries(statusCounts).map(([name, value]) => ({ name, value })));
    } catch (e) {
      console.error(e);
      setStats(prev => ({ ...prev, loading: false }));
    }
  };

  const statCards = [
    { title: 'Companies', value: stats.companies, icon: <Business />, color: '#667eea' },
    { title: 'Projects', value: stats.projects, icon: <AccountTree />, color: '#764ba2' },
    { title: 'Inventory Items', value: stats.inventory, icon: <Inventory />, color: '#4facfe' },
    { title: 'Needs Reorder', value: stats.reorder, icon: <Warning />, color: '#f5576c', alert: stats.reorder > 0 },
    { title: 'Regulations', value: stats.regulations, icon: <Gavel />, color: '#f093fb' },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Nexus Framework Dashboard</Typography>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        {statCards.map((card) => (
          <Grid item xs={12} sm={6} md={4} lg={2.4} key={card.title}>
            <Paper sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2, borderLeft: `4px solid ${card.color}` }}>
              <Box sx={{ color: card.color }}>{card.icon}</Box>
              <Box>
                <Typography variant="h4" fontWeight="bold">{card.value}</Typography>
                <Typography variant="body2" color="text.secondary">{card.title}</Typography>
                {card.alert && <Chip label="Alert" color="error" size="small" sx={{ mt: 0.5 }} />}
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 300 }}>
            <Typography variant="h6" gutterBottom>Project Status Distribution</Typography>
            <ResponsiveContainer width="100%" height="85%">
              <PieChart>
                <Pie
                  data={projectStatus}
                  cx="50%" cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  dataKey="value"
                >
                  {projectStatus.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 300 }}>
            <Typography variant="h6" gutterBottom>System Overview</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Psychology color="primary" />
                <Box>
                  <Typography variant="subtitle1">AI Integration</Typography>
                  <Typography variant="body2" color="text.secondary">Groq LLM API connected</Typography>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <TrendingUp color="success" />
                <Box>
                  <Typography variant="subtitle1">Auto Reorder</Typography>
                  <Typography variant="body2" color="text.secondary">Inventory monitoring active</Typography>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Business color="info" />
                <Box>
                  <Typography variant="subtitle1">Multi-Branch</Typography>
                  <Typography variant="body2" color="text.secondary">Company → Branch → Warehouse</Typography>
                </Box>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
