import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Chip, Alert, Button
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { Warning, AddShoppingCart } from '@mui/icons-material';
import { getInventory, getNeedsReorder, api } from '../api';

export default function Inventory() {
  const [inventory, setInventory] = useState([]);
  const [reorderItems, setReorderItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [invRes, reorderRes] = await Promise.all([
        getInventory(),
        getNeedsReorder()
      ]);
      setInventory(invRes.data);
      setReorderItems(reorderRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleReorder = async (id) => {
    try {
      await api.post(`/industry/inventory/${id}/create_reorder/`, { supplier_id: 1 });
      loadData();
    } catch (e) {
      console.error(e);
    }
  };

  const columns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'product_name', headerName: 'Product', width: 200 },
    { field: 'product_sku', headerName: 'SKU', width: 120 },
    { field: 'warehouse_name', headerName: 'Warehouse', width: 150 },
    { field: 'branch_name', headerName: 'Branch', width: 150 },
    {
      field: 'quantity', headerName: 'Quantity', width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={params.row.needs_reorder ? 'error' : 'success'}
          size="small"
        />
      )
    },
    { field: 'min_reorder_level', headerName: 'Min Level', width: 100 },
    {
      field: 'needs_reorder', headerName: 'Status', width: 120,
      renderCell: (params) => (
        params.value ? (
          <Chip icon={<Warning />} label="Reorder" color="error" size="small" />
        ) : (
          <Chip label="OK" color="success" size="small" />
        )
      )
    },
    {
      field: 'actions', headerName: 'Actions', width: 150,
      renderCell: (params) => (
        params.row.needs_reorder && (
          <Button
            size="small" variant="outlined" color="warning"
            startIcon={<AddShoppingCart />}
            onClick={() => handleReorder(params.row.id)}
          >
            Reorder
          </Button>
        )
      )
    },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Inventory Management</Typography>

      {reorderItems.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {reorderItems.length} items need reordering!
        </Alert>
      )}

      <Paper sx={{ height: 500, width: '100%' }}>
        <DataGrid
          rows={inventory}
          columns={columns}
          loading={loading}
          pageSizeOptions={[10, 20, 50]}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
        />
      </Paper>
    </Box>
  );
}
