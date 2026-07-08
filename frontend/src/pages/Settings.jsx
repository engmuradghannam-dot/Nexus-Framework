import React from 'react'
import { motion } from 'framer-motion'
import { Database, Bell, Lock, Globe } from 'lucide-react'

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-2xl font-bold text-nexus-50">System Settings</h1>
        <p className="text-sm text-nexus-400 mt-1">Configure Nexus Framework preferences</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {[
          { icon: Database, title: 'Database', desc: 'PostgreSQL connection & Redis cache settings' },
          { icon: Bell, title: 'Notifications', desc: 'Email, Slack & in-app alert preferences' },
          { icon: Lock, title: 'Security', desc: 'Auth tokens, MFA & session management' },
          { icon: Globe, title: 'Integrations', desc: 'Google Maps, AI APIs & third-party services' },
        ].map((s, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
            className="glass-card-hover p-6 cursor-pointer">
            <div className="p-3 rounded-xl bg-accent-primary/10 text-accent-primary w-fit mb-4">
              <s.icon className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-semibold text-nexus-100">{s.title}</h3>
            <p className="text-sm text-nexus-400 mt-2">{s.desc}</p>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
