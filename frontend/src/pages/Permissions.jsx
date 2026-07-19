import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Tabs, Tab, Button, Chip,
  List, ListItem, ListItemText, Switch, Grid
} from '@mui/material';
import {
  Security, People, Visibility, History
} from '@mui/icons-material';
import { api } from '../api';

export default function Permissions() {
  const [tab, setTab] = useState(0);
  const [roles, setRoles] = useState([]);
  const [userRoles, setUserRoles] = useState([]);
  const [fieldPerms, setFieldPerms] = useState([]);
  const [recordPerms, setRecordPerms] = useState([]);
  const [audit, setAudit] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [tab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (tab === 0) {
        const res = await api.get('/permissions/roles/');
        setRoles(res.data);
      } else if (tab === 1) {
        const res = await api.get('/permissions/user-roles/');
        setUserRoles(res.data);
      } else if (tab === 2) {
        const [fp, rp] = await Promise.all([
          api.get('/permissions/field-permissions/'),
          api.get('/permissions/record-permissions/')
        ]);
        setFieldPerms(fp.data);
        setRecordPerms(rp.data);
      } else if (tab === 3) {
        const res = await api.get('/permissions/audit/');
        setAudit(res.data);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const accessColors = {
    hidden: 'error', read_only: 'warning', read_write: 'success',
    none: 'error', view: 'info', edit: 'primary', delete: 'secondary'
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        <Security sx={{ mr: 1, verticalAlign: 'middle' }} />
        Advanced Permissions
      </Typography>

      <Tabs value={tab} onChange={(e, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Roles" icon={<People />} iconPosition="start" />
        <Tab label="User Roles" icon={<People />} iconPosition="start" />
        <Tab label="Field/Record" icon={<Visibility />} iconPosition="start" />
        <Tab label="Audit Log" icon={<History />} iconPosition="start" />
      </Tabs>

      {tab === 0 && (
        <Paper>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="h6">Roles</Typography>
            <Button variant="contained" startIcon={<Security />}>Add Role</Button>
          </Box>
          <List>
            {roles.map((role) => (
              <ListItem key={role.id} divider>
                <ListItemText
                  primary={role.name}
                  secondary={`${role.description} | ${role.user_count} users | ${role.permission_names?.length || 0} permissions`}
                />
                {role.is_system && <Chip label="System" size="small" color="primary" />}
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {tab === 1 && (
        <Paper>
          <List>
            {userRoles.map((ur) => (
              <ListItem key={ur.id} divider>
                <ListItemText primary={`${ur.user_name} -> ${ur.role_name}`} secondary={`Branch: ${ur.branch_name || 'All'} | ${ur.is_active ? 'Active' : 'Inactive'}`} />
                <Switch checked={ur.is_active} />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {tab === 2 && (
        <Box>
          <Typography variant="h6" gutterBottom>Field Permissions</Typography>
          <Paper sx={{ mb: 2 }}>
            <List>
              {fieldPerms.map((fp) => (
                <ListItem key={fp.id} divider>
                  <ListItemText primary={`${fp.role_name} -> ${fp.model_name}.${fp.field_name}`} />
                  <Chip label={fp.access_level} color={accessColors[fp.access_level] || 'default'} size="small" />
                </ListItem>
              ))}
            </List>
          </Paper>
          <Typography variant="h6" gutterBottom>Record Permissions</Typography>
          <Paper>
            <List>
              {recordPerms.map((rp) => (
                <ListItem key={rp.id} divider>
                  <ListItemText primary={`${rp.role_name} -> ${rp.model_name}`} />
                  <Chip label={rp.access_level} color={accessColors[rp.access_level] || 'default'} size="small" />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Box>
      )}

      {tab === 3 && (
        <Paper>
          <List>
            {audit.map((log) => (
              <ListItem key={log.id} divider>
                <ListItemText primary={`${log.user_name} ${log.action} ${log.resource_type}`} secondary={`${new Date(log.timestamp).toLocaleString()} | ${log.ip_address || 'N/A'}`} />
                <Chip label={log.action} size="small" />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
}
