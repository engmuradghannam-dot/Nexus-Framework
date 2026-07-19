import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Tabs, Tab, Button, Chip, Grid
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { Add, CheckCircle, Event, AttachMoney } from '@mui/icons-material';
import { api } from '../api';

export default function HR() {
  const [tab, setTab] = useState(0);
  const [employees, setEmployees] = useState([]);
  const [leaves, setLeaves] = useState([]);
  const [payroll, setPayroll] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [tab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (tab === 0) {
        const res = await api.get('/hr/employees/');
        setEmployees(res.data);
      } else if (tab === 2) {
        const res = await api.get('/hr/leave-requests/');
        setLeaves(res.data);
      } else if (tab === 3) {
        const res = await api.get('/hr/payroll-runs/');
        setPayroll(res.data);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const employeeColumns = [
    { field: 'employee_id', headerName: 'ID', width: 100 },
    { field: 'full_name', headerName: 'Name', width: 200 },
    { field: 'job_title', headerName: 'Job Title', width: 200 },
    { field: 'department_name', headerName: 'Department', width: 150 },
    { field: 'branch_name', headerName: 'Branch', width: 150 },
    {
      field: 'status', headerName: 'Status', width: 120,
      renderCell: (params) => (
        <Chip label={params.value} color={params.value === 'active' ? 'success' : 'default'} size="small" />
      )
    },
    { field: 'salary', headerName: 'Salary', width: 150, type: 'number' },
  ];

  const leaveColumns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'employee_name', headerName: 'Employee', width: 200 },
    { field: 'leave_type_name', headerName: 'Type', width: 150 },
    { field: 'start_date', headerName: 'From', width: 120 },
    { field: 'end_date', headerName: 'To', width: 120 },
    { field: 'days', headerName: 'Days', width: 80 },
    {
      field: 'status', headerName: 'Status', width: 120,
      renderCell: (params) => (
        <Chip label={params.value} color={params.value === 'approved' ? 'success' : params.value === 'rejected' ? 'error' : 'warning'} size="small" />
      )
    },
    {
      field: 'actions', headerName: 'Actions', width: 150,
      renderCell: (params) => params.row.status === 'pending' ? (
        <Box>
          <Button size="small" color="success" onClick={() => handleApproveLeave(params.row.id)}>Approve</Button>
          <Button size="small" color="error" onClick={() => handleRejectLeave(params.row.id)}>Reject</Button>
        </Box>
      ) : null
    },
  ];

  const handleApproveLeave = async (id) => {
    await api.post(`/hr/leave-requests/${id}/approve/`);
    loadData();
  };

  const handleRejectLeave = async (id) => {
    await api.post(`/hr/leave-requests/${id}/reject/`);
    loadData();
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>HR & Payroll</Typography>
      <Tabs value={tab} onChange={(e, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Employees" icon={<Event />} iconPosition="start" />
        <Tab label="Attendance" icon={<CheckCircle />} iconPosition="start" />
        <Tab label="Leave Requests" icon={<Event />} iconPosition="start" />
        <Tab label="Payroll" icon={<AttachMoney />} iconPosition="start" />
      </Tabs>

      {tab === 0 && (
        <Paper sx={{ height: 500 }}>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="h6">Employees</Typography>
            <Button variant="contained" startIcon={<Add />}>Add Employee</Button>
          </Box>
          <DataGrid rows={employees} columns={employeeColumns} loading={loading} pageSizeOptions={[10, 25, 50]} />
        </Paper>
      )}

      {tab === 2 && (
        <Paper sx={{ height: 500 }}>
          <DataGrid rows={leaves} columns={leaveColumns} loading={loading} pageSizeOptions={[10, 25, 50]} />
        </Paper>
      )}

      {tab === 3 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Payroll Runs</Typography>
          <Grid container spacing={2}>
            {payroll.map((p) => (
              <Grid item xs={12} md={4} key={p.id}>
                <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
                  <Typography variant="subtitle1">{p.name}</Typography>
                  <Typography color="text.secondary">{p.period_start} to {p.period_end}</Typography>
                  <Chip label={p.status} color={p.status === 'paid' ? 'success' : 'default'} size="small" sx={{ mt: 1 }} />
                  <Typography variant="h6" sx={{ mt: 1 }}>${p.total_net}</Typography>
                  <Typography variant="caption">{p.payslip_count} payslips</Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}
    </Box>
  );
}
