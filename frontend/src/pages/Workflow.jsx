import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Tabs, Tab, Button, Chip,
  List, ListItem, ListItemText, Avatar, TextField, Grid
} from '@mui/material';
import {
  AccountTree, CheckCircle, Cancel, Pending, ThumbUp
} from '@mui/icons-material';
import { api } from '../api';

export default function Workflow() {
  const [tab, setTab] = useState(0);
  const [workflows, setWorkflows] = useState([]);
  const [myRequests, setMyRequests] = useState([]);
  const [pendingApproval, setPendingApproval] = useState([]);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState('');

  useEffect(() => { loadData(); }, [tab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (tab === 0) {
        const res = await api.get('/workflow/workflows/');
        setWorkflows(res.data);
      } else if (tab === 1) {
        const res = await api.get('/workflow/approval-requests/my_requests/');
        setMyRequests(res.data);
      } else if (tab === 2) {
        const res = await api.get('/workflow/approval-requests/pending_approval/');
        setPendingApproval(res.data);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const handleApprove = async (id) => {
    await api.post(`/workflow/approval-requests/${id}/approve/`, { comments: comment });
    setComment('');
    loadData();
  };

  const handleReject = async (id) => {
    await api.post(`/workflow/approval-requests/${id}/reject/`, { comments: comment });
    setComment('');
    loadData();
  };

  const statusColors = {
    pending: 'warning', approved: 'success', rejected: 'error',
    escalated: 'info', cancelled: 'default'
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        <AccountTree sx={{ mr: 1, verticalAlign: 'middle' }} />
        Workflow Engine
      </Typography>

      <Tabs value={tab} onChange={(e, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Workflows" icon={<AccountTree />} iconPosition="start" />
        <Tab label="My Requests" icon={<Pending />} iconPosition="start" />
        <Tab label="Pending Approval" icon={<ThumbUp />} iconPosition="start" />
      </Tabs>

      {tab === 0 && (
        <Grid container spacing={2}>
          {workflows.map((wf) => (
            <Grid item xs={12} md={6} key={wf.id}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6">{wf.name}</Typography>
                <Typography color="text.secondary" variant="body2">{wf.description}</Typography>
                <Chip label={`${wf.step_count} steps`} size="small" sx={{ mt: 1 }} />
                <Box sx={{ mt: 2 }}>
                  {wf.steps?.map((step, i) => (
                    <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Avatar sx={{ width: 24, height: 24, fontSize: 12 }}>{i + 1}</Avatar>
                      <Typography variant="body2">{step.name}</Typography>
                      <Chip label={step.action} size="small" variant="outlined" />
                    </Box>
                  ))}
                </Box>
              </Paper>
            </Grid>
          ))}
        </Grid>
      )}

      {tab === 1 && (
        <Paper>
          <List>
            {myRequests.map((req) => (
              <ListItem key={req.id} divider>
                <ListItemText
                  primary={req.title}
                  secondary={`${req.workflow_name} | ${req.current_step_name} | ${new Date(req.created_at).toLocaleDateString()}`}
                />
                <Chip label={req.status} color={statusColors[req.status] || 'default'} size="small" />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {tab === 2 && (
        <Paper>
          <List>
            {pendingApproval.map((req) => (
              <ListItem key={req.id} divider>
                <ListItemText
                  primary={req.title}
                  secondary={
                    <Box>
                      <Typography variant="body2">Requester: {req.requester_name}</Typography>
                      <Typography variant="body2">Workflow: {req.workflow_name}</Typography>
                      <Typography variant="body2">Step: {req.current_step_name}</Typography>
                    </Box>
                  }
                />
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <TextField size="small" placeholder="Add comment..." value={comment} onChange={(e) => setComment(e.target.value)} sx={{ minWidth: 200 }} />
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button size="small" variant="contained" color="success" startIcon={<CheckCircle />} onClick={() => handleApprove(req.id)}>Approve</Button>
                    <Button size="small" variant="outlined" color="error" startIcon={<Cancel />} onClick={() => handleReject(req.id)}>Reject</Button>
                  </Box>
                </Box>
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
}
