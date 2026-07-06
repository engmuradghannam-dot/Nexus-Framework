import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useTenant } from './hooks/useTenant';
import Layout from './components/Layout';
import LoadingScreen from './components/LoadingScreen';

// Lazy load pages for code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const TenantOnboarding = lazy(() => import('./pages/TenantOnboarding'));
const BillingPage = lazy(() => import('./pages/BillingPage'));
const PluginManager = lazy(() => import('./pages/PluginManager'));
const Settings = lazy(() => import('./pages/Settings'));
const Login = lazy(() => import('./pages/Login'));
const NotFound = lazy(() => import('./pages/NotFound'));

function App() {
  const { tenant, loading } = useTenant();

  if (loading) return <LoadingScreen />;

  return (
    <Suspense fallback={<LoadingScreen />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/onboarding" element={<TenantOnboarding />} />
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/billing" element={<BillingPage />} />
          <Route path="/plugins" element={<PluginManager />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}

export default App;
