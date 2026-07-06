import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './context/AuthContext'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'

import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import PurchaseOrders from './pages/PurchaseOrders'
import SalesOrders from './pages/SalesOrders'
import Employees from './pages/Employees'
import Companies from './pages/Companies'
import Suppliers from './pages/Suppliers'
import Customers from './pages/Customers'
import WorkOrders from './pages/WorkOrders'
import Items from './pages/Items'
import Teams from './pages/Teams'
import Tasks from './pages/Tasks'
import LeaveRequests from './pages/LeaveRequests'
import Payrolls from './pages/Payrolls'
import Projects from './pages/Projects'
import Assets from './pages/Assets'
import JournalEntries from './pages/JournalEntries'
import CRM from './pages/CRM'
import Reports from './pages/Reports'
import Settings from './pages/Settings'
import StockReconciliation from './pages/StockReconciliation'
import Budgets from './pages/Budgets'
import WarehousesBranches from './pages/WarehousesBranches'

// NEW: Project Management pages
import KanbanBoard from './pages/KanbanBoard'
import GanttChart from './pages/GanttChart'
import TimeTracking from './pages/TimeTracking'
import AIAssistant from './pages/AIAssistant'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<Layout />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="purchase-orders" element={<PurchaseOrders />} />
                <Route path="sales-orders" element={<SalesOrders />} />
                <Route path="employees" element={<Employees />} />
                <Route path="companies" element={<Companies />} />
                <Route path="suppliers" element={<Suppliers />} />
                <Route path="customers" element={<Customers />} />
                <Route path="work-orders" element={<WorkOrders />} />
                <Route path="items" element={<Items />} />
                <Route path="teams" element={<Teams />} />
                <Route path="tasks" element={<Tasks />} />
                <Route path="leave-requests" element={<LeaveRequests />} />
                <Route path="payrolls" element={<Payrolls />} />
                <Route path="projects" element={<Projects />} />
                <Route path="assets" element={<Assets />} />
                <Route path="accounts" element={<JournalEntries />} />
                <Route path="crm" element={<CRM />} />
                <Route path="reports" element={<Reports />} />
                <Route path="settings" element={<Settings />} />
                <Route path="stock-reconciliation" element={<StockReconciliation />} />
                <Route path="budgets" element={<Budgets />} />
                <Route path="warehouses-branches" element={<WarehousesBranches />} />

                {/* NEW: Project Management routes */}
                <Route path="kanban/:id" element={<KanbanBoard />} />
                <Route path="gantt/:id" element={<GanttChart />} />
                <Route path="time-tracking" element={<TimeTracking />} />
                <Route path="ai-assistant" element={<AIAssistant />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
