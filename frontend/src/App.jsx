import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, CircularProgress } from '@mui/material';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Companies from './pages/Companies';
import Inventory from './pages/Inventory';
import Projects from './pages/Projects';
import AIChat from './pages/AIChat';
import Regulations from './pages/Regulations';
import HR from './pages/HR';
import POS from './pages/POS';
import Workflow from './pages/Workflow';
import Permissions from './pages/Permissions';
import Manufacturing from './pages/Manufacturing';
import Accounting from './pages/Accounting';
import CRM from './pages/CRM';
import Sales from './pages/Sales';
import Tenants from './pages/Tenants';
import AuditLog from './pages/AuditLog';
import { AuthProvider, useAuth } from './AuthContext';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#667eea' },
    secondary: { main: '#764ba2' },
  },
});

function AuthGate() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!user) {
    return <Login />;
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/companies" element={<Companies />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/ai" element={<AIChat />} />
        <Route path="/regulations" element={<Regulations />} />
        <Route path="/hr" element={<HR />} />
        <Route path="/pos" element={<POS />} />
        <Route path="/workflow" element={<Workflow />} />
        <Route path="/permissions" element={<Permissions />} />
        <Route path="/manufacturing" element={<Manufacturing />} />
        <Route path="/accounting" element={<Accounting />} />
        <Route path="/crm" element={<CRM />} />
        <Route path="/sales" element={<Sales />} />
        <Route path="/tenants" element={<Tenants />} />
        <Route path="/audit" element={<AuditLog />} />
      </Routes>
    </Layout>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <AuthProvider>
          <AuthGate />
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
