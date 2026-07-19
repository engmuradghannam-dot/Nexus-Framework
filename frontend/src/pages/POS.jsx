import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Grid, Paper, TextField, Button, List,
  ListItem, ListItemText, IconButton, Divider, Chip, Dialog,
  DialogTitle, DialogContent, DialogActions, Alert
} from '@mui/material';
import { Add, Remove, Delete, PointOfSale, ShoppingCart, Payment } from '@mui/icons-material';
import { api } from '../api';

export default function POS() {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [search, setSearch] = useState('');
  const [session, setSession] = useState(null);
  const [showPayment, setShowPayment] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('cash');

  useEffect(() => {
    loadProducts();
    checkSession();
  }, []);

  const loadProducts = async () => {
    try {
      const res = await api.get('/industry/products/');
      setProducts(res.data);
    } catch (e) { console.error(e); }
  };

  const checkSession = async () => {
    try {
      const res = await api.get('/ecommerce/pos-sessions/open_sessions/');
      if (res.data.length > 0) setSession(res.data[0]);
    } catch (e) { console.error(e); }
  };

  const addToCart = (product) => {
    const existing = cart.find(item => item.product_id === product.id);
    if (existing) {
      setCart(cart.map(item => 
        item.product_id === product.id 
          ? { ...item, quantity: item.quantity + 1, subtotal: (item.quantity + 1) * item.unit_price }
          : item
      ));
    } else {
      setCart([...cart, {
        product_id: product.id,
        name: product.name,
        sku: product.sku,
        quantity: 1,
        unit_price: parseFloat(product.unit_price) || 0,
        subtotal: parseFloat(product.unit_price) || 0
      }]);
    }
  };

  const updateQty = (productId, delta) => {
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const newQty = Math.max(1, item.quantity + delta);
        return { ...item, quantity: newQty, subtotal: newQty * item.unit_price };
      }
      return item;
    }));
  };

  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.product_id !== productId));
  };

  const subtotal = cart.reduce((sum, item) => sum + (item.subtotal || 0), 0);
  const tax = subtotal * 0.15;
  const total = subtotal + tax;

  const filteredProducts = products.filter(p => 
    p.name?.toLowerCase().includes(search.toLowerCase()) ||
    p.sku?.toLowerCase().includes(search.toLowerCase())
  );

  const handleCheckout = async () => {
    if (!session) {
      alert('Please open a POS session first');
      return;
    }
    try {
      await api.post('/ecommerce/pos-transactions/', {
        session: session.id,
        type: 'sale',
        payment_method: paymentMethod,
        subtotal,
        tax,
        total,
        items: cart.map(item => ({
          product: item.product_id,
          quantity: item.quantity,
          unit_price: item.unit_price
        }))
      });
      setCart([]);
      setShowPayment(false);
      alert('Transaction completed!');
    } catch (e) { console.error(e); }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        <PointOfSale sx={{ mr: 1, verticalAlign: 'middle' }} />
        Point of Sale
      </Typography>

      {!session && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          No open POS session. Please open a session first.
        </Alert>
      )}

      <Grid container spacing={2}>
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 2, height: 'calc(100vh - 200px)' }}>
            <TextField fullWidth placeholder="Search products..." value={search} onChange={(e) => setSearch(e.target.value)} sx={{ mb: 2 }} />
            <Grid container spacing={1}>
              {filteredProducts.map(product => (
                <Grid item xs={6} sm={4} key={product.id}>
                  <Paper sx={{ p: 1.5, cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }} onClick={() => addToCart(product)}>
                    <Typography variant="subtitle2" noWrap>{product.name}</Typography>
                    <Typography variant="caption" color="text.secondary">{product.sku}</Typography>
                    <Typography variant="h6" color="primary">${product.unit_price}</Typography>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2, height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>
              <ShoppingCart sx={{ mr: 1, verticalAlign: 'middle' }} />
              Cart ({cart.length})
            </Typography>
            <List sx={{ flex: 1, overflow: 'auto' }}>
              {cart.map((item) => (
                <ListItem key={item.product_id} sx={{ px: 0 }}>
                  <ListItemText primary={item.name} secondary={`$${item.unit_price} x ${item.quantity}`} />
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <IconButton size="small" onClick={() => updateQty(item.product_id, -1)}><Remove /></IconButton>
                    <Typography>{item.quantity}</Typography>
                    <IconButton size="small" onClick={() => updateQty(item.product_id, 1)}><Add /></IconButton>
                    <Typography variant="subtitle1" sx={{ ml: 2 }}>${(item.subtotal || 0).toFixed(2)}</Typography>
                    <IconButton size="small" color="error" onClick={() => removeFromCart(item.product_id)}><Delete /></IconButton>
                  </Box>
                </ListItem>
              ))}
            </List>
            <Divider sx={{ my: 2 }} />
            <Box sx={{ mt: 'auto' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography>Subtotal:</Typography><Typography>${subtotal.toFixed(2)}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography>Tax (15%):</Typography><Typography>${tax.toFixed(2)}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">Total:</Typography><Typography variant="h6" color="primary">${total.toFixed(2)}</Typography>
              </Box>
              <Button variant="contained" fullWidth size="large" startIcon={<Payment />} onClick={() => setShowPayment(true)} disabled={cart.length === 0}>
                Checkout
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      <Dialog open={showPayment} onClose={() => setShowPayment(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Payment</DialogTitle>
        <DialogContent>
          <Typography variant="h4" align="center" sx={{ my: 3 }}>${total.toFixed(2)}</Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            {['cash', 'card', 'digital'].map((method) => (
              <Button key={method} variant={paymentMethod === method ? 'contained' : 'outlined'} onClick={() => setPaymentMethod(method)} sx={{ textTransform: 'capitalize' }}>
                {method}
              </Button>
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPayment(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCheckout}>Complete Payment</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
