import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Chip, LinearProgress, Button, Dialog,
  DialogTitle, DialogContent, DialogActions, TextField, MenuItem
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { Add, TrendingUp } from '@mui/icons-material';
import { getProjects, api } from '../api';

const statusColors = {
  planning: 'default',
  active: 'primary',
  on_hold: 'warning',
  completed: 'success',
  cancelled: 'error',
};

export default function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '', description: '', status: 'planning', budget: ''
  });

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const res = await getProjects();
      setProjects(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      await api.post('/pmo/projects/', formData);
      setOpen(false);
      setFormData({ name: '', description: '', status: 'planning', budget: '' });
      loadProjects();
    } catch (e) {
      console.error(e);
    }
  };

  const columns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'name', headerName: 'Project Name', width: 200 },
    { field: 'company_name', headerName: 'Company', width: 150 },
    {
      field: 'status', headerName: 'Status', width: 120,
      renderCell: (params) => (
        <Chip label={params.value} color={statusColors[params.value] || 'default'} size="small" />
      )
    },
    {
      field: 'task_count', headerName: 'Tasks', width: 100,
      renderCell: (params) => `${params.row.completed_tasks || 0}/${params.value || 0}`
    },
    {
      field: 'progress', headerName: 'Progress', width: 150,
      renderCell: (params) => {
        const total = params.row.task_count || 0;
        const completed = params.row.completed_tasks || 0;
        const pct = total > 0 ? (completed / total) * 100 : 0;
        return <LinearProgress variant="determinate" value={pct} sx={{ width: '100%' }} />;
      }
    },
    { field: 'budget', headerName: 'Budget', width: 120, type: 'number' },
    { field: 'start_date', headerName: 'Start', width: 120 },
    { field: 'end_date', headerName: 'End', width: 120 },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h4">Projects</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => setOpen(true)}>
          New Project
        </Button>
      </Box>

      <Paper sx={{ height: 500, width: '100%' }}>
        <DataGrid
          rows={projects}
          columns={columns}
          loading={loading}
          pageSizeOptions={[5, 10, 20]}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
        />
      </Paper>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus margin="dense" label="Project Name" fullWidth
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
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
          <TextField
            margin="dense" label="Budget" fullWidth type="number"
            value={formData.budget}
            onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
