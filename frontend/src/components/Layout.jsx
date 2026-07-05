import React, { useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, ShoppingCart, Package, Users, Building2,
  Factory, Briefcase, BarChart3, Settings, Menu, X, ChevronDown,
  Warehouse, Landmark, Contact, FolderKanban, Box, FileText
} from 'lucide-react'

const menuItems = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/' },
  { label: 'Companies', icon: Building2, path: '/companies' },
  { label: 'Purchase Orders', icon: ShoppingCart, path: '/purchase-orders' },
  { label: 'Sales Orders', icon: FileText, path: '/sales-orders' },
  { label: 'Suppliers', icon: Warehouse, path: '/suppliers' },
  { label: 'Customers', icon: Contact, path: '/customers' },
  { label: 'Inventory', icon: Package, path: '/items' },
  { label: 'Work Orders', icon: Factory, path: '/work-orders' },
  { label: 'Employees', icon: Users, path: '/employees' },
  { label: 'Projects', icon: FolderKanban, path: '/projects' },
  { label: 'Assets', icon: Box, path: '/assets' },
  { label: 'Accounts', icon: Landmark, path: '/accounts' },
  { label: 'Reports', icon: BarChart3, path: '/reports' },
  { label: 'Settings', icon: Settings, path: '/settings' },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const location = useLocation()

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-white border-r transition-all duration-300 flex flex-col`}>
        <div className="h-16 flex items-center justify-between px-4 border-b">
          {sidebarOpen && <h1 className="text-xl font-bold text-blue-600">Nexus ERP</h1>}
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-1 hover:bg-gray-100 rounded">
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto py-4">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 mx-2 rounded-lg transition-colors ${
                  isActive ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon size={20} />
                {sidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
              </Link>
            )
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
