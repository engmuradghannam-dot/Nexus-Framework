import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Box, Paper, TextField, Button, Typography, Alert, CircularProgress,
  Avatar, CssBaseline
} from '@mui/material';
import { PersonAddOutlined } from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const [data, setData] = useState({
    username: '', email: '', password: '', password2: '', first_name: '', last_name: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (data.password !== data.password2) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await register(data);
      navigate('/login');
    } catch (err) {
      const errors = err.response?.data;
      if (errors) {
        const messages = Object.values(errors).flat().join(', ');
        setError(messages);
      } else {
        setError('Registration failed');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <CssBaseline />
      <Paper elevation={6} sx={{ p: 4, width: '100%', maxWidth: 450, borderRadius: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <Avatar sx={{ m: 1, bgcolor: 'secondary.main' }}>
            <PersonAddOutlined />
          </Avatar>
          <Typography component="h1" variant="h5" sx={{ mb: 2, fontWeight: 'bold' }}>
            Create Account
          </Typography>
        </Box>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            margin="normal" required fullWidth label="Username"
            value={data.username} onChange={(e) => setData({ ...data, username: e.target.value })}
          />
          <TextField
            margin="normal" required fullWidth label="Email" type="email"
            value={data.email} onChange={(e) => setData({ ...data, email: e.target.value })}
          />
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              margin="normal" fullWidth label="First Name"
              value={data.first_name} onChange={(e) => setData({ ...data, first_name: e.target.value })}
            />
            <TextField
              margin="normal" fullWidth label="Last Name"
              value={data.last_name} onChange={(e) => setData({ ...data, last_name: e.target.value })}
            />
          </Box>
          <TextField
            margin="normal" required fullWidth label="Password" type="password"
            value={data.password} onChange={(e) => setData({ ...data, password: e.target.value })}
          />
          <TextField
            margin="normal" required fullWidth label="Confirm Password" type="password"
            value={data.password2} onChange={(e) => setData({ ...data, password2: e.target.value })}
          />
          <Button
            type="submit" fullWidth variant="contained"
            sx={{ mt: 3, mb: 2, py: 1.2, borderRadius: 2 }}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Sign Up'}
          </Button>
          <Box sx={{ textAlign: 'center' }}>
            <Link to="/login" style={{ textDecoration: 'none' }}>
              <Typography variant="body2" color="primary">
                Already have an account? Sign In
              </Typography>
            </Link>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
}
