// App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

// Layout
import Layout from './components/Layout';

// Pages
import ChatPage from './pages/Chat/ChatPage';
import IndustryPage from './pages/Industry/IndustryPage';
import PMOPage from './pages/PMO/PMOPage';
import DashboardPage from './pages/Dashboard/DashboardPage';
import LoginPage from './pages/Auth/LoginPage';
import AIPage from './pages/AI/AIPage';
import RegulatoryPage from './pages/Regulatory/RegulatoryPage';
import BranchesPage from './pages/Branches/BranchesPage';
import WarehousesPage from './pages/Warehouses/WarehousesPage';
import UsersPage from './pages/Users/UsersPage';
import SettingsPage from './pages/Settings/SettingsPage';
import CRMPage from './pages/CRM/CRMPage';
import SellingPage from './pages/Selling/SellingPage';
import BuyingPage from './pages/Buying/BuyingPage';
import ManufacturingPage from './pages/Manufacturing/ManufacturingPage';
import AssetsPage from './pages/Assets/AssetsPage';
import HRPage from './pages/HR/HRPage';
import InventoryPage from './pages/Inventory/InventoryPage';
import ControlsPage from './pages/Controls/ControlsPage';
import TaxesPage from './pages/Taxes/TaxesPage';
import I18nPage from './pages/I18n/I18nPage';

// Auth Guard
import { AuthGuard } from './components/Auth/AuthGuard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 2,
    },
  },
});

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '681700684231-ir8piq7o8aca3hgfuqle41pt124bhk77.apps.googleusercontent.com';

function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Toaster 
            position="top-left"
            toastOptions={{
              duration: 4000,
              style: {
                direction: 'rtl',
                fontFamily: 'system-ui',
              },
            }}
          />
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected Routes */}
            <Route element={<AuthGuard />}>
              <Route element={<Layout />}>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/chat" element={<ChatPage />} />
                <Route path="/ai" element={<AIPage />} />
                <Route path="/industry" element={<IndustryPage />} />
                <Route path="/pmo" element={<PMOPage />} />
                <Route path="/regulatory" element={<RegulatoryPage />} />
                <Route path="/controls" element={<ControlsPage />} />
                <Route path="/branches" element={<BranchesPage />} />
                <Route path="/warehouses" element={<WarehousesPage />} />
                <Route path="/users" element={<UsersPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/crm" element={<CRMPage />} />
                <Route path="/selling" element={<SellingPage />} />
                <Route path="/buying" element={<BuyingPage />} />
                <Route path="/manufacturing" element={<ManufacturingPage />} />
                <Route path="/assets" element={<AssetsPage />} />
                <Route path="/hr" element={<HRPage />} />
                <Route path="/inventory" element={<InventoryPage />} />
                <Route path="/taxes" element={<TaxesPage />} />
                <Route path="/i18n" element={<I18nPage />} />
              </Route>
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
