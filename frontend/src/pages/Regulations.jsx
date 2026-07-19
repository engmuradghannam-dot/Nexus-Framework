import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Chip, Button, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, MenuItem
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { Add, CheckCircle, Cancel, Pending } from '@mui/icons-material';
import { getRegulations, api } from '../api';

const statusColors = {
  draft: 'default',
  active: 'success',
  under_review: 'warning',
  expired: 'error',
};

export default function Regulations() {
  const [regulations, setRegulations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    title: '', code: '', description: '', status: 'draft'
  });

  useEffect(() => {
    loadRegulations();
  }, []);

  const loadRegulations = async () => {
    try {
      const res = await getRegulations();
      setRegulations(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      await api.post('/regulatory/regulations/', formData);
      setOpen(false);
      setFormData({ title: '', code: '', description: '', status: 'draft' });
      loadRegulations();
    } catch (e) {
      console.error(e);
    }
  };

  const columns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'code', headerName: 'Code', width: 120 },
    { field: 'title', headerName: 'Title', width: 250 },
    { field: 'company_name', headerName: 'Company', width: 150 },
    {
      field: 'status', headerName: 'Status', width: 120,
      renderCell: (params) => (
        <Chip label={params.value} color={statusColors[params.value] || 'default'} size="small" />
      )
    },
    { field: 'effective_date', headerName: 'Effective', width: 120 },
    { field: 'expiry_date', headerName: 'Expiry', width: 120 },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4">Regulations & Compliance</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => setOpen(true)}>
          Add Regulation
        </Button>
      </Box>

      <Paper sx={{ height: 500, width: '100%' }}>
        <DataGrid
          rows={regulations}
          columns={columns}
          loading={loading}
          pageSizeOptions={[5, 10, 20]}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
        />
      </Paper>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Regulation</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus margin="dense" label="Title" fullWidth
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          />
          <TextField
            margin="dense" label="Code" fullWidth
            value={formData.code}
            onChange={(e) => setFormData({ ...formData, code: e.target.value })}
          />
          <TextField
            margin="dense" label="Description" fullWidth multiline rows={2}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
          <TextField
            margin="dense" label="Status" fullWidth select
            value={formData.status}
            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
          >
            {Object.keys(statusColors).map(s => (
              <MenuItem key={s} value={s}>{s}</MenuItem>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
