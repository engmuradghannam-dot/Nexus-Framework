import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Button, Chip, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, Alert
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { Add, Apartment } from '@mui/icons-material';
import { getTenants, createTenant, activateTenant, deactivateTenant } from '../api';
import { useAuth } from '../AuthContext';

export default function Tenants() {
  const { user } = useAuth();
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: '', schema_name: '' });
  const [error, setError] = useState('');
  const [warning, setWarning] = useState('');

  useEffect(() => { loadTenants(); }, []);

  const loadTenants = async () => {
    setLoading(true);
    try {
      const res = await getTenants();
      setTenants(res.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const submit = async () => {
    setError('');
    setWarning('');
    try {
      const res = await createTenant(form);
      if (res.data.warning) setWarning(res.data.warning);
      setOpen(false);
      setForm({ name: '', schema_name: '' });
      loadTenants();
    } catch (e) {
      setError(e.response?.data?.error || 'Failed to create tenant');
    }
  };

  const toggleActive = async (row) => {
    try {
      if (row.is_active) await deactivateTenant(row.id);
      else await activateTenant(row.id);
      loadTenants();
    } catch (e) { console.error(e); }
  };

  const columns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'name', headerName: 'Name', width: 200 },
    { field: 'schema_name', headerName: 'Schema', width: 160 },
    { field: 'plan', headerName: 'Plan', width: 110 },
    {
      field: 'is_active', headerName: 'Status', width: 140,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Active' : 'Inactive'}
          color={params.value ? 'success' : 'default'}
          size="small"
          onClick={() => toggleActive(params.row)}
          sx={{ cursor: 'pointer' }}
        />
      ),
    },
    { field: 'created_on', headerName: 'Created', width: 130 },
  ];

  if (!user?.is_staff) {
    return <Alert severity="warning">You don't have access to tenant management.</Alert>;
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4">
          <Apartment sx={{ mr: 1, verticalAlign: 'middle' }} />
          Tenants
        </Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => setOpen(true)}>
          New Tenant
        </Button>
      </Box>

      {warning && <Alert severity="warning" sx={{ mb: 2 }}>{warning}</Alert>}

      <Paper sx={{ height: 500, width: '100%' }}>
        <DataGrid
          rows={tenants} columns={columns} loading={loading}
          pageSizeOptions={[5, 10, 20]}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
        />
      </Paper>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>New Tenant</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <TextField
            autoFocus margin="dense" label="Tenant Name" fullWidth
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <TextField
            margin="dense" label="Schema Name" fullWidth
            helperText="Lowercase letters and numbers only - identifies the tenant's own database"
            value={form.schema_name}
            onChange={(e) => setForm({ ...form, schema_name: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={submit} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
