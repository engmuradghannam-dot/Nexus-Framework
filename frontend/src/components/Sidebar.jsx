import React, { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard, FolderKanban, Building2, BrainCircuit,
  ShieldCheck, Users, MapPin, Warehouse, Settings, ChevronLeft,
  ChevronRight, Zap, LogOut
} from 'lucide-react'

const navGroups = [
  {
    label: 'Overview',
    items: [
      { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
      { path: '/pmo', icon: FolderKanban, label: 'PMO' },
      { path: '/industry', icon: Building2, label: 'Industry' },
      { path: '/ai', icon: BrainCircuit, label: 'AI Engine' },
      { path: '/regulatory', icon: ShieldCheck, label: 'Regulatory' },
    ],
  },
  {
    label: 'Operations',
    items: [
      { path: '/branches', icon: MapPin, label: 'Branches' },
      { path: '/warehouses', icon: Warehouse, label: 'Warehouses' },
      { path: '/users', icon: Users, label: 'Team' },
    ],
  },
  {
    label: 'System',
    items: [
      { path: '/settings', icon: Settings, label: 'Settings' },
    ],
  },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 80 : 260 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className="fixed left-0 top-0 h-screen bg-nexus-900 border-r border-nexus-800 z-50 flex flex-col"
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-5 border-b border-nexus-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center shrink-0">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="overflow-hidden"
              >
                <h1 className="text-lg font-bold tracking-tight whitespace-nowrap">
                  <span className="gradient-text">Nexus</span>
                </h1>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
        {navGroups.map((group) => (
          <div key={group.label}>
            <AnimatePresence>
              {!collapsed && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="px-4 text-xs font-semibold text-nexus-500 uppercase tracking-wider mb-2"
                >
                  {group.label}
                </motion.p>
              )}
            </AnimatePresence>
            <div className="space-y-1">
              {group.items.map((item) => {
                const isActive = location.pathname === item.path
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={isActive ? 'nav-item-active' : 'nav-item'}
                  >
                    <item.icon className="w-5 h-5 shrink-0" />
                    <AnimatePresence>
                      {!collapsed && (
                        <motion.span
                          initial={{ opacity: 0, width: 0 }}
                          animate={{ opacity: 1, width: 'auto' }}
                          exit={{ opacity: 0, width: 0 }}
                          className="whitespace-nowrap text-sm font-medium overflow-hidden"
                        >
                          {item.label}
                        </motion.span>
                      )}
                    </AnimatePresence>
                    {isActive && !collapsed && (
                      <motion.div
                        layoutId="activeIndicator"
                        className="absolute left-0 w-1 h-6 bg-accent-primary rounded-r-full"
                      />
                    )}
                  </NavLink>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-nexus-800 space-y-2">
        <button className="nav-item w-full">
          <LogOut className="w-5 h-5 shrink-0" />
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="whitespace-nowrap text-sm font-medium"
              >
                Sign Out
              </motion.span>
            )}
          </AnimatePresence>
        </button>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center p-2 rounded-xl text-nexus-400 hover:bg-nexus-800 hover:text-nexus-200 transition-colors"
        >
          {collapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
        </button>
      </div>
    </motion.aside>
  )
}
