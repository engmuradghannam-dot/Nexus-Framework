import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import PMO from './pages/PMO'
import Industry from './pages/Industry'
import AI from './pages/AI'
import Regulatory from './pages/Regulatory'
import Branches from './pages/Branches'
import Warehouses from './pages/Warehouses'
import Users from './pages/Users'
import Settings from './pages/Settings'

export default function App() {
  return (
    <div className="min-h-screen bg-nexus-950">
      <Sidebar />
      <div className="ml-[260px] min-h-screen">
        <Header />
        <main className="pt-20 px-6 pb-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/pmo" element={<PMO />} />
            <Route path="/industry" element={<Industry />} />
            <Route path="/ai" element={<AI />} />
            <Route path="/regulatory" element={<Regulatory />} />
            <Route path="/branches" element={<Branches />} />
            <Route path="/warehouses" element={<Warehouses />} />
            <Route path="/users" element={<Users />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
