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
import Login from '@/pages/Login';
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
              <Route path="industry" element={<IndustryDashboard />} />
              <Route path="ai" element={<AIDashboard />} />
              <Route path="regulatory" element={<RegulatoryDashboard />} />
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
