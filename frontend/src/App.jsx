import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
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
import Reports from './pages/Reports';

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? children : <Navigate to="/login" replace />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/*" element={
        <PrivateRoute>
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
              <Route path="/reports" element={<Reports />} />
            </Routes>
          </Layout>
        </PrivateRoute>
      } />
    </Routes>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
