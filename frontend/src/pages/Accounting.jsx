import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Tabs, Tab, Button, Chip, Grid,
  Card, CardContent, TextField, Dialog, DialogTitle,
  DialogContent, DialogActions, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow
} from '@mui/material';
import {
  AccountBalance, Receipt, Payment, Assessment,
  TrendingUp, TrendingDown, Warning
} from '@mui/icons-material';
import { api } from '../api';

export default function Accounting() {
  const [tab, setTab] = useState(0);
  const [accounts, setAccounts] = useState([]);
  const [journalEntries, setJournalEntries] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [payments, setPayments] = useState([]);
  const [reports, setReports] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [tab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (tab === 0) {
        const [accRes, statRes] = await Promise.all([
          api.get('/accounting/chart-of-accounts/'),
          api.get('/accounting/invoices/dashboard_stats/')
        ]);
        setAccounts(accRes.data);
        setStats(statRes.data);
      } else if (tab === 1) {
        const res = await api.get('/accounting/journal-entries/');
        setJournalEntries(res.data);
      } else if (tab === 2) {
        const res = await api.get('/accounting/invoices/');
        setInvoices(res.data);
      } else if (tab === 3) {
        const res = await api.get('/accounting/payments/');
        setPayments(res.data);
      } else if (tab === 4) {
        const res = await api.get('/accounting/financial-reports/');
        setReports(res.data);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const statusColors = {
    draft: 'default',
    posted: 'success',
    reversed: 'error',
    sent: 'info',
    paid: 'success',
    overdue: 'error',
    cancelled: 'default',
    pending: 'warning',
    completed: 'success',
    failed: 'error'
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        <AccountBalance sx={{ mr: 1, verticalAlign: 'middle' }} />
        Accounting
      </Typography>

      <Tabs value={tab} onChange={(e, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Chart of Accounts" icon={<AccountBalance />} iconPosition="start" />
        <Tab label="Journal Entries" icon={<Receipt />} iconPosition="start" />
        <Tab label="Invoices" icon={<Receipt />} iconPosition="start" />
        <Tab label="Payments" icon={<Payment />} iconPosition="start" />
        <Tab label="Reports" icon={<Assessment />} iconPosition="start" />
      </Tabs>

      {tab === 0 && (
        <Box>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>Total Sales</Typography>
                  <Typography variant="h4" color="success.main">${stats.total_sales?.toFixed(2) || '0.00'}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>Total Purchases</Typography>
                  <Typography variant="h4" color="error.main">${stats.total_purchases?.toFixed(2) || '0.00'}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>Overdue</Typography>
                  <Typography variant="h4" color="warning.main">${stats.overdue_amount?.toFixed(2) || '0.00'}</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>Paid Amount</Typography>
                  <Typography variant="h4" color="info.main">${stats.paid_amount?.toFixed(2) || '0.00'}</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Paper>
            <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="h6">Chart of Accounts</Typography>
              <Button variant="contained" startIcon={<AccountBalance />}>Add Account</Button>
            </Box>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Code</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Category</TableCell>
                    <TableCell align="right">Balance</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {accounts.map((acc) => (
                    <TableRow key={acc.id}>
                      <TableCell>{acc.code}</TableCell>
                      <TableCell>{acc.name}</TableCell>
                      <TableCell>{acc.account_type_name}</TableCell>
                      <TableCell>
                        <Chip label={acc.account_type_category} size="small" />
                      </TableCell>
                      <TableCell align="right">${acc.current_balance?.toFixed(2)}</TableCell>
                      <TableCell>
                        <Chip label={acc.is_active ? 'Active' : 'Inactive'} color={acc.is_active ? 'success' : 'default'} size="small" />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Box>
      )}

      {tab === 1 && (
        <Paper>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="h6">Journal Entries</Typography>
            <Button variant="contained" startIcon={<Receipt />}>New Entry</Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Entry #</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell align="right">Debit</TableCell>
                  <TableCell align="right">Credit</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {journalEntries.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell>{entry.entry_number}</TableCell>
                    <TableCell>{entry.date}</TableCell>
                    <TableCell>{entry.description}</TableCell>
                    <TableCell align="right">${entry.total_debit?.toFixed(2)}</TableCell>
                    <TableCell align="right">${entry.total_credit?.toFixed(2)}</TableCell>
                    <TableCell>
                      <Chip label={entry.status} color={statusColors[entry.status] || 'default'} size="small" />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {tab === 2 && (
        <Paper>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="h6">Invoices</Typography>
            <Button variant="contained" startIcon={<Receipt />}>New Invoice</Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Invoice #</TableCell>
                  <TableCell>Customer</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Due Date</TableCell>
                  <TableCell align="right">Total</TableCell>
                  <TableCell align="right">Balance</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {invoices.map((inv) => (
                  <TableRow key={inv.id}>
                    <TableCell>{inv.invoice_number}</TableCell>
                    <TableCell>{inv.customer_name}</TableCell>
                    <TableCell>{inv.date}</TableCell>
                    <TableCell>{inv.due_date}</TableCell>
                    <TableCell align="right">${inv.total?.toFixed(2)}</TableCell>
                    <TableCell align="right">${inv.balance_due?.toFixed(2)}</TableCell>
                    <TableCell>
                      <Chip label={inv.status} color={statusColors[inv.status] || 'default'} size="small" />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {tab === 3 && (
        <Paper>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="h6">Payments</Typography>
            <Button variant="contained" startIcon={<Payment />}>Record Payment</Button>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Payment #</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Method</TableCell>
                  <TableCell align="right">Amount</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {payments.map((pay) => (
                  <TableRow key={pay.id}>
                    <TableCell>{pay.payment_number}</TableCell>
                    <TableCell>{pay.date}</TableCell>
                    <TableCell>{pay.method}</TableCell>
                    <TableCell align="right">${pay.amount?.toFixed(2)}</TableCell>
                    <TableCell>
                      <Chip label={pay.status} color={statusColors[pay.status] || 'default'} size="small" />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {tab === 4 && (
        <Box>
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="h6">Financial Reports</Typography>
            <Button variant="contained" startIcon={<Assessment />}>Generate Report</Button>
          </Box>
          <Grid container spacing={2}>
            {reports.map((report) => (
              <Grid item xs={12} md={6} key={report.id}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6">{report.name}</Typography>
                  <Typography color="text.secondary">{report.report_type.replace('_', ' ').toUpperCase()}</Typography>
                  <Typography variant="body2">Period: {report.period_start} to {report.period_end}</Typography>
                  <Typography variant="caption">Generated: {new Date(report.generated_at).toLocaleString()}</Typography>
                  {report.data && (
                    <Box sx={{ mt: 2, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                      <pre style={{ margin: 0, fontSize: 12 }}>
                        {JSON.stringify(report.data, null, 2)}
                      </pre>
                    </Box>
                  )}
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
    </Box>
  );
}
