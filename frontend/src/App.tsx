// App.tsx
import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

// Layout
import Layout from './components/Layout';

// Pages loaded eagerly (first paint: login + the post-login landing page)
import LoginPage from './pages/Auth/LoginPage';
import RegisterPage from './pages/Auth/RegisterPage';
import DashboardPage from './pages/Dashboard/DashboardPage';

// All other pages are code-split: each becomes its own chunk, fetched only
// when the user navigates to that route, instead of one ~750KB bundle.
const ChatPage = lazy(() => import('./pages/Chat/ChatPage'));
const IndustryPage = lazy(() => import('./pages/Industry/IndustryPage'));
const PMOPage = lazy(() => import('./pages/PMO/PMOPage'));
const AIPage = lazy(() => import('./pages/AI/AIPage'));
const RegulatoryPage = lazy(() => import('./pages/Regulatory/RegulatoryPage'));
const BranchesPage = lazy(() => import('./pages/Branches/BranchesPage'));
const WarehousesPage = lazy(() => import('./pages/Warehouses/WarehousesPage'));
const UsersPage = lazy(() => import('./pages/Users/UsersPage'));
const SettingsPage = lazy(() => import('./pages/Settings/SettingsPage'));
const CRMPage = lazy(() => import('./pages/CRM/CRMPage'));
const SellingPage = lazy(() => import('./pages/Selling/SellingPage'));
const BuyingPage = lazy(() => import('./pages/Buying/BuyingPage'));
const ManufacturingPage = lazy(() => import('./pages/Manufacturing/ManufacturingPage'));
const AssetsPage = lazy(() => import('./pages/Assets/AssetsPage'));
const HRPage = lazy(() => import('./pages/HR/HRPage'));
const InventoryPage = lazy(() => import('./pages/Inventory/InventoryPage'));
const ControlsPage = lazy(() => import('./pages/Controls/ControlsPage'));
const CompanySetupPage = lazy(() => import('./pages/CompanySetup/CompanySetupPage'));
const AccountingPage = lazy(() => import('./pages/Accounting/AccountingPage'));
const InvoicingPage = lazy(() => import('./pages/Invoicing/InvoicingPage'));
const CreditNotesPage = lazy(() => import('./pages/CreditNotes/CreditNotesPage'));
const PeriodsPage = lazy(() => import('./pages/Periods/PeriodsPage'));
const AgingPage = lazy(() => import('./pages/Aging/AgingPage'));
const DepreciationPage = lazy(() => import('./pages/Depreciation/DepreciationPage'));
const BankingPage = lazy(() => import('./pages/Banking/BankingPage'));
const TenantsPage = lazy(() => import('./pages/Tenants/TenantsPage'));
const CurrenciesPage = lazy(() => import('./pages/Currencies/CurrenciesPage'));
const CustomFieldsPage = lazy(() => import('./pages/CustomFields/CustomFieldsPage'));
const PricingPage = lazy(() => import('./pages/Pricing/PricingPage'));
const BarcodePage = lazy(() => import('./pages/Barcode/BarcodePage'));
const PurchasingPage = lazy(() => import('./pages/Purchasing/PurchasingPage'));
const ReportsPage = lazy(() => import('./pages/Reports/ReportsPage'));
const NotificationsPage = lazy(() => import('./pages/Notifications/NotificationsPage'));
const HRExtrasPage = lazy(() => import('./pages/HRExtras/HRExtrasPage'));
const UOMPage = lazy(() => import('./pages/UOM/UOMPage'));
const AutomationPage = lazy(() => import('./pages/Automation/AutomationPage'));
const ReorderPage = lazy(() => import('./pages/Reorder/ReorderPage'));
const ValuationPage = lazy(() => import('./pages/Valuation/ValuationPage'));
const StockMovementsPage = lazy(() => import('./pages/StockMovements/StockMovementsPage'));
const DocumentsPage = lazy(() => import('./pages/Documents/DocumentsPage'));
const RolesPage = lazy(() => import('./pages/Roles/RolesPage'));
const AttendancePage = lazy(() => import('./pages/Attendance/AttendancePage'));
const SecurityPage = lazy(() => import('./pages/Security/SecurityPage'));
const AuditPage = lazy(() => import('./pages/Audit/AuditPage'));
const TaxesPage = lazy(() => import('./pages/Taxes/TaxesPage'));
const I18nPage = lazy(() => import('./pages/I18n/I18nPage'));

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

function RouteLoading() {
  return (
    <div className="flex items-center justify-center h-64 text-[#605e5c] text-sm">
      جارِ التحميل...
    </div>
  );
}

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
          <Suspense fallback={<RouteLoading />}>
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

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
                  <Route path="/company-setup" element={<CompanySetupPage />} />
                  <Route path="/branches" element={<BranchesPage />} />
                  <Route path="/warehouses" element={<WarehousesPage />} />
                  <Route path="/users" element={<UsersPage />} />
                  <Route path="/tenants" element={<TenantsPage />} />
                  <Route path="/custom-fields" element={<CustomFieldsPage />} />
                  <Route path="/roles" element={<RolesPage />} />
                  <Route path="/security" element={<SecurityPage />} />
                  <Route path="/audit" element={<AuditPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="/crm" element={<CRMPage />} />
                  <Route path="/selling" element={<SellingPage />} />
                  <Route path="/pricing" element={<PricingPage />} />
                  <Route path="/buying" element={<BuyingPage />} />
                  <Route path="/purchasing" element={<PurchasingPage />} />
                  <Route path="/reports" element={<ReportsPage />} />
                  <Route path="/notifications" element={<NotificationsPage />} />
                  <Route path="/manufacturing" element={<ManufacturingPage />} />
                  <Route path="/assets" element={<AssetsPage />} />
                  <Route path="/depreciation" element={<DepreciationPage />} />
                  <Route path="/hr" element={<HRPage />} />
                  <Route path="/hr-extras" element={<HRExtrasPage />} />
                  <Route path="/uom" element={<UOMPage />} />
                  <Route path="/automation" element={<AutomationPage />} />
                  <Route path="/attendance" element={<AttendancePage />} />
                  <Route path="/inventory" element={<InventoryPage />} />
                  <Route path="/barcode" element={<BarcodePage />} />
                  <Route path="/reorder" element={<ReorderPage />} />
                  <Route path="/valuation" element={<ValuationPage />} />
                  <Route path="/stock-movements" element={<StockMovementsPage />} />
                  <Route path="/accounting" element={<AccountingPage />} />
                  <Route path="/invoicing" element={<InvoicingPage />} />
                  <Route path="/credit-notes" element={<CreditNotesPage />} />
                  <Route path="/periods" element={<PeriodsPage />} />
                  <Route path="/aging" element={<AgingPage />} />
                  <Route path="/banking" element={<BankingPage />} />
                  <Route path="/trade" element={<DocumentsPage />} />
                  <Route path="/taxes" element={<TaxesPage />} />
                  <Route path="/currencies" element={<CurrenciesPage />} />
                  <Route path="/i18n" element={<I18nPage />} />
                </Route>
              </Route>

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </QueryClientProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
