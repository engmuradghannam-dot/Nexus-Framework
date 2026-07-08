import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Bell, Command, Sun, Moon } from 'lucide-react'

export default function Header() {
  const [searchOpen, setSearchOpen] = useState(false)
  const [notifications, setNotifications] = useState([
    { id: 1, title: 'Project Alpha overdue', type: 'warning', time: '2m ago' },
    { id: 2, title: 'AI Model v2.1 deployed', type: 'success', time: '15m ago' },
    { id: 3, title: 'Compliance check failed', type: 'danger', time: '1h ago' },
  ])
  const [showNotifs, setShowNotifs] = useState(false)

  return (
    <header className="h-16 bg-nexus-900/80 backdrop-blur-xl border-b border-nexus-800 fixed top-0 right-0 left-0 z-40 flex items-center justify-between px-6"
      style={{ marginLeft: '260px' }}>
      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-nexus-500" />
          <input
            type="text"
            placeholder="Search projects, regulations, insights..."
            className="input-field pl-10 pr-4 py-2 w-80 text-sm"
            onFocus={() => setSearchOpen(true)}
            onBlur={() => setSearchOpen(false)}
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-nexus-500 text-xs">
            <Command className="w-3 h-3" />
            <span>K</span>
          </div>
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-3">
        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifs(!showNotifs)}
            className="relative p-2 rounded-xl text-nexus-400 hover:bg-nexus-800 hover:text-nexus-200 transition-colors"
          >
            <Bell className="w-5 h-5" />
            {notifications.length > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-accent-danger rounded-full" />
            )}
          </button>
          <AnimatePresence>
            {showNotifs && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                className="absolute right-0 top-12 w-80 glass-card p-2 shadow-2xl"
              >
                <p className="px-3 py-2 text-sm font-semibold text-nexus-200">Notifications</p>
                {notifications.map((n) => (
                  <div key={n.id} className="px-3 py-2.5 rounded-xl hover:bg-nexus-800/50 cursor-pointer transition-colors">
                    <div className="flex items-start gap-3">
                      <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                        n.type === 'warning' ? 'bg-accent-warning' :
                        n.type === 'danger' ? 'bg-accent-danger' : 'bg-accent-success'
                      }`} />
                      <div>
                        <p className="text-sm text-nexus-200">{n.title}</p>
                        <p className="text-xs text-nexus-500 mt-0.5">{n.time}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* User */}
        <div className="flex items-center gap-3 pl-4 border-l border-nexus-800">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-nexus-200">Murad Ghannam</p>
            <p className="text-xs text-nexus-500">Superuser</p>
          </div>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center text-white font-bold text-sm">
            MG
          </div>
        </div>
      </div>
    </header>
  )
}
