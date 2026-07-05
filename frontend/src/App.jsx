import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import PurchaseOrders from './pages/PurchaseOrders'
import SalesOrders from './pages/SalesOrders'
import Employees from './pages/Employees'
import Companies from './pages/Companies'
import Suppliers from './pages/Suppliers'
import Customers from './pages/Customers'
import WorkOrders from './pages/WorkOrders'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="purchase-orders" element={<PurchaseOrders />} />
        <Route path="sales-orders" element={<SalesOrders />} />
        <Route path="employees" element={<Employees />} />
        <Route path="companies" element={<Companies />} />
        <Route path="suppliers" element={<Suppliers />} />
        <Route path="customers" element={<Customers />} />
        <Route path="work-orders" element={<WorkOrders />} />
        <Route path="*" element={<div className="p-10 text-center text-gray-500">Page not found</div>} />
      </Route>
    </Routes>
  )
}

export default App
