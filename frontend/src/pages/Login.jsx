import React, { useState } from 'react';
import { Box, Paper, TextField, Button, Typography, Alert } from '@mui/material';
import { useAuth } from '../AuthContext';

export default function Login() {
    const { login } = useAuth();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSubmitting(true);
        try {
            await login(username, password);
        } catch (err) {
            setError(err.response?.data?.error || 'Login failed');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <Box sx={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            minHeight: '100vh', bgcolor: 'background.default',
        }}>
            <Paper component="form" onSubmit={handleSubmit} sx={{ p: 4, width: 360 }}>
                <Typography variant="h5" gutterBottom>Nexus Framework</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Sign in to continue
                </Typography>
                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
                <TextField
                    label="Username" fullWidth margin="normal" autoFocus
                    value={username} onChange={(e) => setUsername(e.target.value)}
                />
                <TextField
                    label="Password" type="password" fullWidth margin="normal"
                    value={password} onChange={(e) => setPassword(e.target.value)}
                />
                <Button type="submit" variant="contained" fullWidth sx={{ mt: 3 }} disabled={submitting}>
                    {submitting ? 'Signing in...' : 'Sign In'}
                </Button>
            </Paper>
        </Box>
    );
}
