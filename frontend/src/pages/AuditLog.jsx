import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Chip, Alert, Collapse, IconButton,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow
} from '@mui/material';
import { History, KeyboardArrowDown, KeyboardArrowUp } from '@mui/icons-material';
import { getChangeHeaders } from '../api';
import { useAuth } from '../AuthContext';

const changeTypeColors = { I: 'success', U: 'info', D: 'error' };
const changeTypeLabels = { I: 'Insert', U: 'Update', D: 'Delete' };

function ChangeRow({ header }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <>
      <TableRow>
        <TableCell>
          <IconButton size="small" onClick={() => setExpanded(!expanded)}>
            {expanded ? <KeyboardArrowUp /> : <KeyboardArrowDown />}
          </IconButton>
        </TableCell>
        <TableCell>{new Date(header.change_time).toLocaleString()}</TableCell>
        <TableCell>{header.content_type_label}</TableCell>
        <TableCell>{header.object_id}</TableCell>
        <TableCell>{header.object_repr}</TableCell>
        <TableCell>
          <Chip label={changeTypeLabels[header.change_type]} color={changeTypeColors[header.change_type]} size="small" />
        </TableCell>
        <TableCell>{header.username_snapshot}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell colSpan={7} sx={{ py: 0, border: 0 }}>
          <Collapse in={expanded} timeout="auto" unmountOnExit>
            <Box sx={{ my: 1 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Field</TableCell>
                    <TableCell>Old Value</TableCell>
                    <TableCell>New Value</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {header.items.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>{item.field_name}</TableCell>
                      <TableCell>{item.value_old}</TableCell>
                      <TableCell>{item.value_new}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

export default function AuditLog() {
  const { user } = useAuth();
  const [headers, setHeaders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user?.is_staff) return;
    getChangeHeaders()
      .then((res) => setHeaders(res.data))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, [user]);

  if (!user?.is_staff) {
    return <Alert severity="warning">You don't have access to the audit log.</Alert>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        <History sx={{ mr: 1, verticalAlign: 'middle' }} />
        Audit Log
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        CDHDR/CDPOS-style change trail - who changed what, and when, across every tracked model.
      </Typography>

      <Paper>
        <TableContainer sx={{ maxHeight: 600 }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell />
                <TableCell>When</TableCell>
                <TableCell>Model</TableCell>
                <TableCell>Object ID</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Change</TableCell>
                <TableCell>By</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {!loading && headers.map((h) => <ChangeRow key={h.id} header={h} />)}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
}
