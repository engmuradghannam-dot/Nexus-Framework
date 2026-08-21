import React, { useState, useEffect } from 'react';
import { Box, Grid, Paper, Typography, Chip, Card, CardContent } from '@mui/material';
import {
  Business, AccountTree, Inventory, Warning,
  Gavel, Psychology, TrendingUp, Groups, PointOfSale,
  AccountBalance, Engineering, AssignmentTurnedIn
} from '@mui/icons-material';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, AreaChart, Area
} from 'recharts';
import { getCompanies, getProjects, getInventory, getNeedsReorder, getRegulations, getEmployees, getOrders } from '../api';

const COLORS = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b'];

export default function Dashboard() {
  const [stats, setStats] = useState({
    companies: 0, projects: 0, inventory: 0,
    reorder: 0, regulations: 0, employees: 0, orders: 0,
    loading: true
  });
  const [projectStatus, setProjectStatus] = useState([]);
  const [inventoryTrend, setInventoryTrend] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const [companies, projects, inventory, reorder, regulations, employees, orders] = await Promise.all([
        getCompanies(), getProjects(), getInventory(),
        getNeedsReorder(), getRegulations(),
        getEmployees().catch(() => ({ data: [] })),
        getOrders().catch(() => ({ data: [] })),
      ]);

      const statusCounts = {};
      projects.data.forEach(p => {
        statusCounts[p.status] = (statusCounts[p.status] || 0) + 1;
      });

      // Inventory trend (mock monthly data based on current)
      const invData = inventory.data;
      const trend = [
        { month: 'Jan', stock: Math.floor(invData.length * 0.8) },
        { month: 'Feb', stock: Math.floor(invData.length * 0.85) },
        { month: 'Mar', stock: Math.floor(invData.length * 0.9) },
        { month: 'Apr', stock: Math.floor(invData.length * 0.95) },
        { month: 'May', stock: invData.length },
        { month: 'Jun', stock: Math.floor(invData.length * 1.05) },
      ];

      setStats({
        companies: companies.data.length,
        projects: projects.data.length,
        inventory: invData.length,
        reorder: reorder.data.length,
        regulations: regulations.data.length,
        employees: employees.data.length,
        orders: orders.data.length,
        loading: false
      });

      setProjectStatus(Object.entries(statusCounts).map(([name, value]) => ({ name, value })));
      setInventoryTrend(trend);
      setRecentActivity([
        { action: 'New order created', time: '2 min ago', user: 'System' },
        { action: 'Inventory reorder triggered', time: '15 min ago', user: 'Auto' },
        { action: 'Project updated', time: '1 hour ago', user: 'Admin' },
        { action: 'New employee registered', time: '3 hours ago', user: 'HR' },
      ]);
    } catch (e) {
      console.error(e);
      setStats(prev => ({ ...prev, loading: false }));
    }
  };

  const statCards = [
    { title: 'Companies', value: stats.companies, icon: <Business />, color: '#667eea' },
    { title: 'Projects', value: stats.projects, icon: <AccountTree />, color: '#764ba2' },
    { title: 'Inventory', value: stats.inventory, icon: <Inventory />, color: '#4facfe' },
    { title: 'Low Stock', value: stats.reorder, icon: <Warning />, color: '#f5576c', alert: stats.reorder > 0 },
    { title: 'Employees', value: stats.employees, icon: <Groups />, color: '#f093fb' },
    { title: 'Orders', value: stats.orders, icon: <PointOfSale />, color: '#43e97b' },
  ];

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 3 }}>
        📈 Nexus Framework Dashboard
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {statCards.map((card) => (
          <Grid item xs={12} sm={6} md={4} lg={2} key={card.title}>
            <Card sx={{ borderLeft: `4px solid ${card.color}`, height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Box sx={{ color: card.color }}>{card.icon}</Box>
                  <Typography variant="body2" color="text.secondary">{card.title}</Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold">{card.value}</Typography>
                {card.alert && <Chip label="Alert" color="error" size="small" sx={{ mt: 0.5 }} />}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Charts Row 1 */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: 320 }}>
            <Typography variant="h6" gutterBottom>Project Status</Typography>
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

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: 320 }}>
            <Typography variant="h6" gutterBottom>Inventory Trend</Typography>
            <ResponsiveContainer width="100%" height="85%">
              <AreaChart data={inventoryTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="stock" stroke="#667eea" fill="#667eea" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: 320 }}>
            <Typography variant="h6" gutterBottom>Recent Activity</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              {recentActivity.map((activity, i) => (
                <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 1, borderRadius: 1, bgcolor: 'background.default' }}>
                  <TrendingUp color="primary" fontSize="small" />
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="body2" fontWeight="medium">{activity.action}</Typography>
                    <Typography variant="caption" color="text.secondary">{activity.time} • {activity.user}</Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Charts Row 2 */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 300 }}>
            <Typography variant="h6" gutterBottom>System Modules</Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 2 }}>
              {[
                { name: 'AI Integration', icon: <Psychology />, status: 'Active', color: 'success' },
                { name: 'Auto Reorder', icon: <TrendingUp />, status: 'Active', color: 'success' },
                { name: 'Multi-Branch', icon: <Business />, status: 'Active', color: 'success' },
                { name: 'Workflow', icon: <AssignmentTurnedIn />, status: 'Active', color: 'success' },
                { name: 'Manufacturing', icon: <Engineering />, status: 'Active', color: 'success' },
                { name: 'Accounting', icon: <AccountBalance />, status: 'Active', color: 'success' },
              ].map((mod) => (
                <Paper key={mod.name} sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 2, minWidth: 200 }}>
                  <Box sx={{ color: 'primary.main' }}>{mod.icon}</Box>
                  <Box>
                    <Typography variant="subtitle2">{mod.name}</Typography>
                    <Chip label={mod.status} color={mod.color} size="small" />
                  </Box>
                </Paper>
              ))}
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 300 }}>
            <Typography variant="h6" gutterBottom>Quick Actions</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
              <Card variant="outlined" sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}>
                <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Inventory color="primary" />
                  <Box>
                    <Typography variant="subtitle1">Check Inventory</Typography>
                    <Typography variant="body2" color="text.secondary">{stats.reorder} items need reordering</Typography>
                  </Box>
                </CardContent>
              </Card>
              <Card variant="outlined" sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}>
                <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Gavel color="warning" />
                  <Box>
                    <Typography variant="subtitle1">Review Regulations</Typography>
                    <Typography variant="body2" color="text.secondary">{stats.regulations} active regulations</Typography>
                  </Box>
                </CardContent>
              </Card>
              <Card variant="outlined" sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}>
                <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Groups color="success" />
                  <Box>
                    <Typography variant="subtitle1">HR Overview</Typography>
                    <Typography variant="body2" color="text.secondary">{stats.employees} employees registered</Typography>
                  </Box>
                </CardContent>
              </Card>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
