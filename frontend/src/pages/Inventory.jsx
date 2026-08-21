import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Chip, Alert, Button, Grid, Card, CardContent,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  IconButton, Tooltip, Badge
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import {
  Warning, AddShoppingCart, Refresh, NotificationsActive,
  LocalShipping, TrendingDown, CheckCircle
} from '@mui/icons-material';
import { getInventory, getNeedsReorder, getReorderAlerts, triggerReorder, api } from '../api';

export default function Inventory() {
  const [inventory, setInventory] = useState([]);
  const [reorderItems, setReorderItems] = useState([]);
  const [reorderAlerts, setReorderAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reorderLoading, setReorderLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [invRes, reorderRes, alertsRes] = await Promise.all([
        getInventory(),
        getNeedsReorder(),
        getReorderAlerts().catch(() => ({ data: [] })) // Fallback if endpoint not ready
      ]);
      setInventory(invRes.data);
      setReorderItems(reorderRes.data);
      setReorderAlerts(alertsRes.data);
    } catch (e) {
      console.error('Error loading inventory:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleReorder = async (id) => {
    try {
      await api.post(`/industry/inventory/${id}/create_reorder/`, { supplier_id: 1 });
      loadData();
    } catch (e) {
      console.error(e);
    }
  };

  const handleTriggerReorder = async () => {
    try {
      setReorderLoading(true);
      await triggerReorder();
      loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setReorderLoading(false);
    }
  };

  const columns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'product_name', headerName: 'Product', width: 200 },
    { field: 'product_sku', headerName: 'SKU', width: 120 },
    { field: 'warehouse_name', headerName: 'Warehouse', width: 150 },
    { field: 'branch_name', headerName: 'Branch', width: 150 },
    {
      field: 'quantity', headerName: 'Quantity', width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={params.row.needs_reorder ? 'error' : 'success'}
          size="small"
          variant="filled"
        />
      )
    },
    { field: 'min_reorder_level', headerName: 'Min Level', width: 100 },
    {
      field: 'needs_reorder', headerName: 'Status', width: 120,
      renderCell: (params) => (
        params.value ? (
          <Chip icon={<Warning />} label="Reorder" color="error" size="small" />
        ) : (
          <Chip icon={<CheckCircle />} label="OK" color="success" size="small" />
        )
      )
    },
    {
      field: 'actions', headerName: 'Actions', width: 150,
      renderCell: (params) => (
        params.row.needs_reorder && (
          <Button
            size="small" variant="outlined" color="warning"
            startIcon={<AddShoppingCart />}
            onClick={() => handleReorder(params.row.id)}
          >
            Reorder
          </Button>
        )
      )
    },
  ];

  // Stats cards
  const totalItems = inventory.length;
  const lowStockCount = reorderItems.length;
  const okStockCount = totalItems - lowStockCount;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
          📦 Inventory Management
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<Refresh />}
            onClick={loadData}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            color="warning"
            startIcon={<LocalShipping />}
            onClick={handleTriggerReorder}
            disabled={reorderLoading || lowStockCount === 0}
          >
            Auto-Reorder All
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: '#e3f2fd', borderLeft: '4px solid #1976d2' }}>
            <CardContent>
              <Typography variant="h6" color="primary">Total Items</Typography>
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>{totalItems}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: '#fff3e0', borderLeft: '4px solid #ed6c02' }}>
            <CardContent>
              <Typography variant="h6" color="warning.dark">
                <Badge badgeContent={lowStockCount} color="error" sx={{ mr: 1 }}>
                  <NotificationsActive />
                </Badge>
                Low Stock Alerts
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'warning.dark' }}>
                {lowStockCount}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: '#e8f5e9', borderLeft: '4px solid #2e7d32' }}>
            <CardContent>
              <Typography variant="h6" color="success.dark">
                <CheckCircle sx={{ mr: 1 }} />
                Stock OK
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'success.dark' }}>
                {okStockCount}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Reorder Alerts Table */}
      {reorderItems.length > 0 && (
        <Paper sx={{ mb: 3, p: 2, bgcolor: '#fff8e1', border: '1px solid #ffb74d' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Warning color="error" sx={{ mr: 1 }} />
            <Typography variant="h6" color="error" sx={{ fontWeight: 'bold' }}>
              ⚠️ Reorder Alerts ({reorderItems.length} items need attention)
            </Typography>
          </Box>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: '#ffcc80' }}>
                  <TableCell sx={{ fontWeight: 'bold' }}>Product</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>SKU</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Warehouse</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Current Qty</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Min Level</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Deficit</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Action</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {reorderItems.map((item) => (
                  <TableRow key={item.id} hover>
                    <TableCell>{item.product_name}</TableCell>
                    <TableCell><code>{item.product_sku}</code></TableCell>
                    <TableCell>{item.warehouse_name}</TableCell>
                    <TableCell>
                      <Chip label={item.quantity} color="error" size="small" />
                    </TableCell>
                    <TableCell>{item.min_reorder_level}</TableCell>
                    <TableCell sx={{ color: 'error.main', fontWeight: 'bold' }}>
                      <TrendingDown sx={{ fontSize: 16, mr: 0.5 }} />
                      {item.min_reorder_level - item.quantity}
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small" variant="contained" color="warning"
                        startIcon={<AddShoppingCart />}
                        onClick={() => handleReorder(item.id)}
                      >
                        Reorder
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Main Inventory DataGrid */}
      <Paper sx={{ height: 550, width: '100%' }}>
        <DataGrid
          rows={inventory}
          columns={columns}
          loading={loading}
          pageSizeOptions={[10, 25, 50, 100]}
          initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
          density="compact"
          sx={{
            '& .MuiDataGrid-row:hover': { bgcolor: '#f5f5f5' },
          }}
        />
      </Paper>
    </Box>
  );
}
