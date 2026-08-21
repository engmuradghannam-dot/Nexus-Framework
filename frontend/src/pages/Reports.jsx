import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Grid, Card, CardContent, Button,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, Tabs, Tab, CircularProgress, Alert, IconButton, Tooltip
} from '@mui/material';
import {
  PictureAsPdf, TableChart, Refresh, Download,
  Business, Inventory, Groups, AccountBalance,
  PointOfSale, Assessment
} from '@mui/icons-material';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, LineChart, Line, AreaChart, Area
} from 'recharts';
import { getCompanies, getInventory, getEmployees, getOrders, getJournalEntries } from '../api';

function TabPanel({ children, value, index }) {
  return value === index ? <Box sx={{ mt: 2 }}>{children}</Box> : null;
}

export default function Reports() {
  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState({
    companies: [], inventory: [], employees: [], orders: [], journalEntries: []
  });
  const [exportLoading, setExportLoading] = useState({});

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [companies, inventory, employees, orders, journalEntries] = await Promise.all([
        getCompanies().catch(() => ({ data: [] })),
        getInventory().catch(() => ({ data: [] })),
        getEmployees().catch(() => ({ data: [] })),
        getOrders().catch(() => ({ data: [] })),
        getJournalEntries().catch(() => ({ data: [] })),
      ]);
      setData({
        companies: companies.data,
        inventory: inventory.data,
        employees: employees.data,
        orders: orders.data,
        journalEntries: journalEntries.data,
      });
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = (filename, rows, headers) => {
    setExportLoading(prev => ({ ...prev, [filename]: true }));

    const csvContent = [
      headers.join(','),
      ...rows.map(row => headers.map(h => {
        const val = row[h] ?? row[h.toLowerCase().replace(/ /g, '_')] ?? '';
        return `"${String(val).replace(/"/g, '\"')}"`;
      }).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setTimeout(() => setExportLoading(prev => ({ ...prev, [filename]: false })), 1000);
  };

  const handleExportPDF = (title, contentId) => {
    setExportLoading(prev => ({ ...prev, [title]: true }));
    window.print();
    setTimeout(() => setExportLoading(prev => ({ ...prev, [title]: false })), 1000);
  };

  // Inventory chart data
  const inventoryByWarehouse = data.inventory.reduce((acc, item) => {
    acc[item.warehouse_name] = (acc[item.warehouse_name] || 0) + item.quantity;
    return acc;
  }, {});
  const inventoryChartData = Object.entries(inventoryByWarehouse).map(([name, value]) => ({ name, value }));

  // Employee chart data
  const employeesByDept = data.employees.reduce((acc, emp) => {
    const dept = emp.department_name || 'Unassigned';
    acc[dept] = (acc[dept] || 0) + 1;
    return acc;
  }, {});
  const employeeChartData = Object.entries(employeesByDept).map(([name, value]) => ({ name, value }));

  const reportCards = [
    { title: 'Companies Report', count: data.companies.length, icon: <Business />, color: '#667eea', data: data.companies, headers: ['ID', 'Name', 'Address', 'Phone', 'Email'] },
    { title: 'Inventory Report', count: data.inventory.length, icon: <Inventory />, color: '#4facfe', data: data.inventory, headers: ['ID', 'Product Name', 'SKU', 'Quantity', 'Warehouse'] },
    { title: 'HR Report', count: data.employees.length, icon: <Groups />, color: '#f093fb', data: data.employees, headers: ['ID', 'Username', 'Department', 'Branch', 'Salary'] },
    { title: 'Orders Report', count: data.orders.length, icon: <PointOfSale />, color: '#f5576c', data: data.orders, headers: ['ID', 'Customer', 'Total', 'Status', 'Date'] },
    { title: 'Accounting Report', count: data.journalEntries.length, icon: <AccountBalance />, color: '#764ba2', data: data.journalEntries, headers: ['ID', 'Account', 'Debit', 'Credit', 'Date'] },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          📊 Reports Engine
        </Typography>
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={loadAllData}
          disabled={loading}
        >
          {loading ? <CircularProgress size={20} /> : 'Refresh Data'}
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {reportCards.map((card) => (
          <Grid item xs={12} sm={6} md={4} lg={2.4} key={card.title}>
            <Card sx={{ borderLeft: `4px solid ${card.color}`, height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Box sx={{ color: card.color }}>{card.icon}</Box>
                  <Typography variant="body2" color="text.secondary">{card.title}</Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold">{card.count}</Typography>
                <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                  <Tooltip title="Export CSV">
                    <IconButton
                      size="small"
                      onClick={() => handleExportCSV(card.title.replace(/ /g, '_'), card.data, card.headers)}
                      disabled={exportLoading[card.title.replace(/ /g, '_')] || card.count === 0}
                    >
                      {exportLoading[card.title.replace(/ /g, '_')] ? <CircularProgress size={16} /> : <TableChart fontSize="small" />}
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Print PDF">
                    <IconButton
                      size="small"
                      onClick={() => handleExportPDF(card.title, card.title.replace(/ /g, '_'))}
                    >
                      <PictureAsPdf fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Tabs for detailed reports */}
      <Paper sx={{ p: 2 }}>
        <Tabs value={tab} onChange={(e, v) => setTab(v)} variant="scrollable">
          <Tab icon={<Inventory />} label="Inventory Analytics" />
          <Tab icon={<Groups />} label="HR Analytics" />
          <Tab icon={<PointOfSale />} label="Sales Analytics" />
          <Tab icon={<AccountBalance />} label="Accounting Analytics" />
        </Tabs>

        <TabPanel value={tab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>Stock by Warehouse</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={inventoryChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <RechartsTooltip />
                  <Bar dataKey="value" fill="#667eea" />
                </BarChart>
              </ResponsiveContainer>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>Low Stock Items</Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'primary.main' }}>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Product</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Qty</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Min Level</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.inventory.filter(i => i.needs_reorder).slice(0, 10).map(item => (
                      <TableRow key={item.id} hover>
                        <TableCell>{item.product_name}</TableCell>
                        <TableCell><Chip label={item.quantity} color="error" size="small" /></TableCell>
                        <TableCell>{item.min_reorder_level}</TableCell>
                        <TableCell><Chip label="REORDER" color="error" size="small" /></TableCell>
                      </TableRow>
                    ))}
                    {data.inventory.filter(i => i.needs_reorder).length === 0 && (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          <Alert severity="success">All stock levels are healthy!</Alert>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tab} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>Employees by Department</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={employeeChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <RechartsTooltip />
                  <Bar dataKey="value" fill="#f093fb" />
                </BarChart>
              </ResponsiveContainer>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>Employee List</Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'primary.main' }}>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Name</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Department</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Branch</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.employees.slice(0, 10).map(emp => (
                      <TableRow key={emp.id} hover>
                        <TableCell>{emp.username}</TableCell>
                        <TableCell>{emp.department_name || '-'}</TableCell>
                        <TableCell>{emp.branch_name || '-'}</TableCell>
                        <TableCell><Chip label="Active" color="success" size="small" /></TableCell>
                      </TableRow>
                    ))}
                    {data.employees.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={4} align="center">No employees found</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tab} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>Orders Overview</Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'primary.main' }}>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Order ID</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Customer</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Total</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Status</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Date</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.orders.slice(0, 20).map(order => (
                      <TableRow key={order.id} hover>
                        <TableCell>#{order.id}</TableCell>
                        <TableCell>{order.customer_name || order.customer || 'N/A'}</TableCell>
                        <TableCell sx={{ fontWeight: 'bold' }}>${order.total || 0}</TableCell>
                        <TableCell>
                          <Chip 
                            label={order.status || 'Pending'} 
                            color={order.status === 'completed' ? 'success' : order.status === 'cancelled' ? 'error' : 'warning'} 
                            size="small" 
                          />
                        </TableCell>
                        <TableCell>{order.created_at || order.date || '-'}</TableCell>
                      </TableRow>
                    ))}
                    {data.orders.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} align="center">No orders found</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tab} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>Journal Entries</Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'primary.main' }}>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Entry ID</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Account</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Debit</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Credit</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Date</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.journalEntries.slice(0, 20).map(entry => (
                      <TableRow key={entry.id} hover>
                        <TableCell>#{entry.id}</TableCell>
                        <TableCell>{entry.account_name || entry.account || 'N/A'}</TableCell>
                        <TableCell sx={{ color: 'success.main', fontWeight: 'bold' }}>${entry.debit || 0}</TableCell>
                        <TableCell sx={{ color: 'error.main', fontWeight: 'bold' }}>${entry.credit || 0}</TableCell>
                        <TableCell>{entry.date || entry.created_at || '-'}</TableCell>
                      </TableRow>
                    ))}
                    {data.journalEntries.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} align="center">No journal entries found</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>
    </Box>
  );
}
