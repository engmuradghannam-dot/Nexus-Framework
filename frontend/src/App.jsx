import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/toaster';
import Layout from '@/components/Layout';
import Dashboard from '@/pages/Dashboard';
import PMODashboard from '@/pages/PMODashboard';
import IndustryDashboard from '@/pages/IndustryDashboard';
import AIDashboard from '@/pages/AIDashboard';
import RegulatoryDashboard from '@/pages/RegulatoryDashboard';
import PMO from '@/pages/PMO';
import Industry from '@/pages/Industry';
import AI from '@/pages/AI';
import Regulatory from '@/pages/Regulatory';
import Login from '@/pages/Login';
import Users from '@/pages/Users';
import Settings from '@/pages/Settings';
import Branches from '@/pages/Branches';
import Warehouses from '@/pages/Warehouses';
import { AuthProvider } from '@/contexts/AuthContext';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="pmo" element={<PMODashboard />} />
              <Route path="pmo/detail" element={<PMO />} />
              <Route path="industry" element={<IndustryDashboard />} />
              <Route path="industry/detail" element={<Industry />} />
              <Route path="ai" element={<AIDashboard />} />
              <Route path="ai/detail" element={<AI />} />
              <Route path="regulatory" element={<RegulatoryDashboard />} />
              <Route path="regulatory/detail" element={<Regulatory />} />
              <Route path="users" element={<Users />} />
              <Route path="settings" element={<Settings />} />
              <Route path="branches" element={<Branches />} />
              <Route path="warehouses" element={<Warehouses />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
        <Toaster />
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
