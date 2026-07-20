import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Tabs, Tab, Button, Chip, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, MenuItem
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { Add, ShoppingCart } from '@mui/icons-material';
import {
  getSalesOrders, createSalesOrder, getQuotations, getSalesInvoices,
  getDeliveries, getBackorders, getCrmCustomers, getAllWarehouses,
} from '../api';

const statusColors = {
  draft: 'default', confirmed: 'info', picking: 'warning', packed: 'warning',
  shipped: 'info', delivered: 'success', invoiced: 'success', paid: 'success',
  cancelled: 'error', pending: 'warning',
};

export default function Sales() {
  const [tab, setTab] = useState(0);
  const [orders, setOrders] = useState([]);
  const [quotations, setQuotations] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [deliveries, setDeliveries] = useState([]);
  const [backorders, setBackorders] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [orderOpen, setOrderOpen] = useState(false);
  const [orderForm, setOrderForm] = useState({ customer: '', warehouse: '', shipping_address: '', required_date: '' });

  useEffect(() => { loadData(); }, [tab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (tab === 0) {
        const [orderRes, custRes, whRes] = await Promise.all([getSalesOrders(), getCrmCustomers(), getAllWarehouses()]);
        setOrders(orderRes.data);
        setCustomers(custRes.data);
        setWarehouses(whRes.data);
      } else if (tab === 1) setQuotations((await getQuotations()).data);
      else if (tab === 2) setInvoices((await getSalesInvoices()).data);
      else if (tab === 3) setDeliveries((await getDeliveries()).data);
      else if (tab === 4) setBackorders((await getBackorders()).data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const submitOrder = async () => {
    try {
      await createSalesOrder(orderForm);
      setOrderOpen(false);
      setOrderForm({ customer: '', warehouse: '', shipping_address: '', required_date: '' });
      loadData();
    } catch (e) { console.error(e); }
  };

  const statusChip = (params) => <Chip label={params.value} color={statusColors[params.value] || 'default'} size="small" />;

  const orderColumns = [
    { field: 'so_id', headerName: 'Order #', width: 140 },
    { field: 'customer_name', headerName: 'Customer', width: 180 },
    { field: 'order_date', headerName: 'Order Date', width: 120 },
    { field: 'total_amount', headerName: 'Total', width: 120, type: 'number' },
    { field: 'status', headerName: 'Status', width: 120, renderCell: statusChip },
  ];

  const quotationColumns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'customer_name', headerName: 'Customer', width: 180 },
    { field: 'total_amount', headerName: 'Total', width: 120, type: 'number' },
    { field: 'status', headerName: 'Status', width: 120, renderCell: statusChip },
  ];

  const invoiceColumns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'order', headerName: 'Order', width: 100 },
    { field: 'total_amount', headerName: 'Total', width: 120, type: 'number' },
    { field: 'status', headerName: 'Status', width: 120, renderCell: statusChip },
  ];

  const deliveryColumns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'order', headerName: 'Order', width: 100 },
    { field: 'delivery_date', headerName: 'Delivery Date', width: 140 },
    { field: 'status', headerName: 'Status', width: 120, renderCell: statusChip },
  ];

  const backorderColumns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'order_item', headerName: 'Order Item', width: 120 },
    { field: 'quantity_pending', headerName: 'Qty Pending', width: 130, type: 'number' },
  ];

  const tabConfig = [
    { rows: orders, columns: orderColumns },
    { rows: quotations, columns: quotationColumns },
    { rows: invoices, columns: invoiceColumns },
    { rows: deliveries, columns: deliveryColumns },
    { rows: backorders, columns: backorderColumns },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        <ShoppingCart sx={{ mr: 1, verticalAlign: 'middle' }} />
        Sales
      </Typography>

      <Tabs value={tab} onChange={(e, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label="Orders" />
        <Tab label="Quotations" />
        <Tab label="Invoices" />
        <Tab label="Deliveries" />
        <Tab label="Backorders" />
      </Tabs>

      {tab === 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
          <Button variant="contained" startIcon={<Add />} onClick={() => setOrderOpen(true)}>
            New Order
          </Button>
        </Box>
      )}

      <Paper sx={{ height: 500, width: '100%' }}>
        <DataGrid
          rows={tabConfig[tab].rows} columns={tabConfig[tab].columns} loading={loading}
          pageSizeOptions={[5, 10, 20]}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
        />
      </Paper>

      <Dialog open={orderOpen} onClose={() => setOrderOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>New Sales Order</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus margin="dense" label="Customer" fullWidth select
            value={orderForm.customer}
            onChange={(e) => setOrderForm({ ...orderForm, customer: e.target.value })}
          >
            {customers.map((c) => (
              <MenuItem key={c.id} value={c.id}>{c.customer_name}</MenuItem>
            ))}
          </TextField>
          <TextField
            margin="dense" label="Warehouse" fullWidth select
            value={orderForm.warehouse}
            onChange={(e) => setOrderForm({ ...orderForm, warehouse: e.target.value })}
          >
            {warehouses.map((w) => (
              <MenuItem key={w.id} value={w.id}>{w.name}</MenuItem>
            ))}
          </TextField>
          <TextField
            margin="dense" label="Shipping Address" fullWidth multiline rows={2}
            value={orderForm.shipping_address}
            onChange={(e) => setOrderForm({ ...orderForm, shipping_address: e.target.value })}
          />
          <TextField
            margin="dense" label="Required Date" type="date" fullWidth
            InputLabelProps={{ shrink: true }}
            value={orderForm.required_date}
            onChange={(e) => setOrderForm({ ...orderForm, required_date: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOrderOpen(false)}>Cancel</Button>
          <Button onClick={submitOrder} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
