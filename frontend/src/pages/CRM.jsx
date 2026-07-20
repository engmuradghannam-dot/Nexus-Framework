import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Tabs, Tab, Button, Chip, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, MenuItem
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { Add, People } from '@mui/icons-material';
import { getCrmCustomers, createCrmCustomer, getContacts, getOpportunities, createOpportunity, getAllBranches } from '../api';

const stageColors = {
  qualification: 'default',
  needs_analysis: 'info',
  proposal: 'warning',
  negotiation: 'warning',
  closed_won: 'success',
  closed_lost: 'error',
};

export default function CRM() {
  const [tab, setTab] = useState(0);
  const [customers, setCustomers] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [branches, setBranches] = useState([]);
  const [customerOpen, setCustomerOpen] = useState(false);
  const [opportunityOpen, setOpportunityOpen] = useState(false);
  const [customerForm, setCustomerForm] = useState({ customer_name: '', email: '', phone: '', customer_type: 'company', branch: '' });
  const [opportunityForm, setOpportunityForm] = useState({ customer: '', name: '', value: 0, probability: 10 });

  useEffect(() => { loadData(); }, [tab]);
  useEffect(() => { getAllBranches().then((res) => setBranches(res.data)).catch((e) => console.error(e)); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      if (tab === 0) setCustomers((await getCrmCustomers()).data);
      else if (tab === 1) setContacts((await getContacts()).data);
      else if (tab === 2) {
        const [oppRes, custRes] = await Promise.all([getOpportunities(), getCrmCustomers()]);
        setOpportunities(oppRes.data);
        setCustomers(custRes.data);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const submitCustomer = async () => {
    try {
      await createCrmCustomer(customerForm);
      setCustomerOpen(false);
      setCustomerForm({ customer_name: '', email: '', phone: '', customer_type: 'company', branch: '' });
      loadData();
    } catch (e) { console.error(e); }
  };

  const submitOpportunity = async () => {
    try {
      await createOpportunity(opportunityForm);
      setOpportunityOpen(false);
      setOpportunityForm({ customer: '', name: '', value: 0, probability: 10 });
      loadData();
    } catch (e) { console.error(e); }
  };

  const customerColumns = [
    { field: 'customer_id', headerName: 'ID', width: 130 },
    { field: 'customer_name', headerName: 'Name', width: 200 },
    { field: 'customer_type', headerName: 'Type', width: 110 },
    { field: 'email', headerName: 'Email', width: 200 },
    { field: 'phone', headerName: 'Phone', width: 140 },
    {
      field: 'status', headerName: 'Status', width: 120,
      renderCell: (params) => <Chip label={params.value} size="small" />
    },
    { field: 'credit_limit', headerName: 'Credit Limit', width: 120, type: 'number' },
  ];

  const contactColumns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'name', headerName: 'Name', width: 200 },
    { field: 'email', headerName: 'Email', width: 200 },
    { field: 'phone', headerName: 'Phone', width: 140 },
    { field: 'title', headerName: 'Title', width: 160 },
  ];

  const opportunityColumns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'name', headerName: 'Opportunity', width: 200 },
    { field: 'customer_name', headerName: 'Customer', width: 180 },
    {
      field: 'stage', headerName: 'Stage', width: 150,
      renderCell: (params) => <Chip label={params.value} color={stageColors[params.value] || 'default'} size="small" />
    },
    { field: 'value', headerName: 'Value', width: 120, type: 'number' },
    { field: 'probability', headerName: 'Probability %', width: 130, type: 'number' },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        <People sx={{ mr: 1, verticalAlign: 'middle' }} />
        CRM
      </Typography>

      <Tabs value={tab} onChange={(e, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Customers" />
        <Tab label="Contacts" />
        <Tab label="Opportunities" />
      </Tabs>

      {tab === 0 && (
        <>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button variant="contained" startIcon={<Add />} onClick={() => setCustomerOpen(true)}>
              Add Customer
            </Button>
          </Box>
          <Paper sx={{ height: 500, width: '100%' }}>
            <DataGrid
              rows={customers} columns={customerColumns} loading={loading}
              pageSizeOptions={[5, 10, 20]}
              initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
            />
          </Paper>
        </>
      )}

      {tab === 1 && (
        <Paper sx={{ height: 500, width: '100%' }}>
          <DataGrid
            rows={contacts} columns={contactColumns} loading={loading}
            pageSizeOptions={[5, 10, 20]}
            initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
          />
        </Paper>
      )}

      {tab === 2 && (
        <>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button variant="contained" startIcon={<Add />} onClick={() => setOpportunityOpen(true)}>
              Add Opportunity
            </Button>
          </Box>
          <Paper sx={{ height: 500, width: '100%' }}>
            <DataGrid
              rows={opportunities} columns={opportunityColumns} loading={loading}
              pageSizeOptions={[5, 10, 20]}
              initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
            />
          </Paper>
        </>
      )}

      <Dialog open={customerOpen} onClose={() => setCustomerOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Customer</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus margin="dense" label="Customer Name" fullWidth
            value={customerForm.customer_name}
            onChange={(e) => setCustomerForm({ ...customerForm, customer_name: e.target.value })}
          />
          <TextField
            margin="dense" label="Email" fullWidth
            value={customerForm.email}
            onChange={(e) => setCustomerForm({ ...customerForm, email: e.target.value })}
          />
          <TextField
            margin="dense" label="Phone" fullWidth
            value={customerForm.phone}
            onChange={(e) => setCustomerForm({ ...customerForm, phone: e.target.value })}
          />
          <TextField
            margin="dense" label="Type" fullWidth select
            value={customerForm.customer_type}
            onChange={(e) => setCustomerForm({ ...customerForm, customer_type: e.target.value })}
          >
            <MenuItem value="individual">Individual</MenuItem>
            <MenuItem value="company">Company</MenuItem>
            <MenuItem value="government">Government</MenuItem>
          </TextField>
          <TextField
            margin="dense" label="Branch" fullWidth select
            value={customerForm.branch}
            onChange={(e) => setCustomerForm({ ...customerForm, branch: e.target.value })}
          >
            {branches.map((b) => (
              <MenuItem key={b.id} value={b.id}>{b.name}</MenuItem>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCustomerOpen(false)}>Cancel</Button>
          <Button onClick={submitCustomer} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={opportunityOpen} onClose={() => setOpportunityOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Opportunity</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense" label="Customer" fullWidth select
            value={opportunityForm.customer}
            onChange={(e) => setOpportunityForm({ ...opportunityForm, customer: e.target.value })}
          >
            {customers.map((c) => (
              <MenuItem key={c.id} value={c.id}>{c.customer_name}</MenuItem>
            ))}
          </TextField>
          <TextField
            autoFocus margin="dense" label="Opportunity Name" fullWidth
            value={opportunityForm.name}
            onChange={(e) => setOpportunityForm({ ...opportunityForm, name: e.target.value })}
          />
          <TextField
            margin="dense" label="Value" fullWidth type="number"
            value={opportunityForm.value}
            onChange={(e) => setOpportunityForm({ ...opportunityForm, value: e.target.value })}
          />
          <TextField
            margin="dense" label="Probability %" fullWidth type="number"
            value={opportunityForm.probability}
            onChange={(e) => setOpportunityForm({ ...opportunityForm, probability: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpportunityOpen(false)}>Cancel</Button>
          <Button onClick={submitOpportunity} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
