import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Tabs, Tab, Button, Grid, Chip,
  Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  LinearProgress, Alert
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import {
  Factory, PrecisionManufacturing, Route, Assignment,
  Inventory, CheckCircle, Cancel, PlayArrow, Pause
} from '@mui/icons-material';
import { api } from '../api';

export default function Manufacturing() {
  const [tab, setTab] = useState(0);
  const [workCenters, setWorkCenters] = useState([]);
  const [boms, setBoms] = useState([]);
  const [routings, setRoutings] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogType, setDialogType] = useState('');

  useEffect(() => { loadData(); }, [tab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (tab === 0) {
        const res = await api.get('/manufacturing/work-centers/');
        setWorkCenters(res.data);
      } else if (tab === 1) {
        const res = await api.get('/manufacturing/boms/');
        setBoms(res.data);
      } else if (tab === 2) {
        const res = await api.get('/manufacturing/routings/');
        setRoutings(res.data);
      } else if (tab === 3) {
        const res = await api.get('/manufacturing/manufacturing-orders/');
        setOrders(res.data);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const statusColors = {
    draft: 'default',
    planned: 'info',
    released: 'primary',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'error',
    on_hold: 'secondary',
  };

  const orderColumns = [
    { field: 'order_number', headerName: 'Order #', width: 120 },
    { field: 'product_name', headerName: 'Product', width: 200 },
    { field: 'quantity', headerName: 'Qty', width: 80, type: 'number' },
    { field: 'quantity_produced', headerName: 'Produced', width: 90, type: 'number' },
    {
      field: 'completion_percentage',
      headerName: 'Progress',
      width: 120,
      renderCell: (params) => (
        <Box sx={{ width: '100%' }}>
          <LinearProgress variant="determinate" value={params.value || 0} />
          <Typography variant="caption">{params.value}%</Typography>
        </Box>
      )
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip label={params.value} color={statusColors[params.value] || 'default'} size="small" />
      )
    },
    {
      field: 'priority',
      headerName: 'Priority',
      width: 100,
      renderCell: (params) => (
        <Chip label={params.value} color={params.value === 'urgent' ? 'error' : 'default'} size="small" variant="outlined" />
      )
    },
    { field: 'is_overdue', headerName: 'Overdue', width: 80, type: 'boolean' },
  ];

  const workCenterColumns = [
    { field: 'code', headerName: 'Code', width: 100 },
    { field: 'name', headerName: 'Name', width: 200 },
    { field: 'capacity_per_hour', headerName: 'Capacity/hr', width: 120, type: 'number' },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip label={params.value} color={params.value === 'active' ? 'success' : 'warning'} size="small" />
      )
    },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        <Factory sx={{ mr: 1, verticalAlign: 'middle' }} />
        Manufacturing
      </Typography>

      <Tabs value={tab} onChange={(e, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Work Centers" icon={<Factory />} iconPosition="start" />
        <Tab label="BOMs" icon={<Inventory />} iconPosition="start" />
        <Tab label="Routings" icon={<Route />} iconPosition="start" />
        <Tab label="Orders" icon={<Assignment />} iconPosition="start" />
      </Tabs>

      {tab === 0 && (
        <Paper sx={{ height: 500 }}>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="h6">Work Centers</Typography>
            <Button variant="contained" startIcon={<Factory />}>Add Work Center</Button>
          </Box>
          <DataGrid rows={workCenters} columns={workCenterColumns} loading={loading} pageSizeOptions={[10, 25, 50]} />
        </Paper>
      )}

      {tab === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Bill of Materials</Typography>
          <Grid container spacing={2}>
            {boms.map((bom) => (
              <Grid item xs={12} md={6} key={bom.id}>
                <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
                  <Typography variant="subtitle1">{bom.product_name} v{bom.version}</Typography>
                  <Typography color="text.secondary">Items: {bom.item_count} | Cost: ${bom.total_cost}</Typography>
                  <Box sx={{ mt: 1 }}>
                    {bom.is_default && <Chip label="Default" size="small" color="primary" sx={{ mr: 1 }} />}
                    {bom.is_active && <Chip label="Active" size="small" color="success" />}
                  </Box>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {tab === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Production Routings</Typography>
          <Grid container spacing={2}>
            {routings.map((routing) => (
              <Grid item xs={12} md={6} key={routing.id}>
                <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
                  <Typography variant="subtitle1">{routing.product_name} v{routing.version}</Typography>
                  <Typography color="text.secondary">Operations: {routing.operation_count} | Cost: ${routing.total_cost}</Typography>
                  <Box sx={{ mt: 1 }}>
                    {routing.is_default && <Chip label="Default" size="small" color="primary" sx={{ mr: 1 }} />}
                  </Box>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {tab === 3 && (
        <Paper sx={{ height: 500 }}>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="h6">Manufacturing Orders</Typography>
            <Button variant="contained" startIcon={<Assignment />}>Create Order</Button>
          </Box>
          <DataGrid rows={orders} columns={orderColumns} loading={loading} pageSizeOptions={[10, 25, 50]} />
        </Paper>
      )}
    </Box>
  );
}
