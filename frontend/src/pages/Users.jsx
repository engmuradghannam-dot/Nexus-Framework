import React from 'react'
import { motion } from 'framer-motion'
import { Users, Shield, UserPlus } from 'lucide-react'
import KPICard from '../components/KPICard'
import DataTable from '../components/DataTable'

const users = [
  { name: 'Murad Ghannam', email: 'eng.murad.ghannam@gmail.com', department: 'Engineering', role: 'Superuser', level: 'Admin', status: 'Active' },
  { name: 'Ahmed Ali', email: 'ahmed@nexus.com', department: 'Operations', role: 'Branch Manager', level: 'Manager', status: 'Active' },
  { name: 'Sara Hassan', email: 'sara@nexus.com', department: 'Finance', role: 'Auditor', level: 'Editor', status: 'Active' },
  { name: 'Khalid Omar', email: 'khalid@nexus.com', department: 'Sales', role: 'Team Lead', level: 'Manager', status: 'Active' },
  { name: 'Mehmet Yilmaz', email: 'mehmet@nexus.com', department: 'IT', role: 'Developer', level: 'Editor', status: 'Inactive' },
]

const levelBadge = (l) => {
  const map = { Admin: 'badge-danger', Manager: 'badge-warning', Editor: 'badge-info', Viewer: 'badge-success' }
  return <span className={map[l] || 'badge'}>{l}</span>
}

const statusBadge = (s) => s === 'Active' ? <span className="badge-success">Active</span> : <span className="badge">Inactive</span>

export default function UsersPage() {
  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-nexus-50">Team Management</h1>
            <p className="text-sm text-nexus-400 mt-1">HR-linked permissions & role management</p>
          </div>
          <button className="btn-primary flex items-center gap-2">
            <UserPlus className="w-4 h-4" />
            Add User
          </button>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPICard title="Total Users" value="5" icon={Users} color="primary" delay={0} />
        <KPICard title="Admins" value="1" icon={Shield} color="danger" delay={0.1} />
        <KPICard title="Managers" value="2" icon={Users} color="warning" delay={0.2} />
        <KPICard title="Active Now" value="4" icon={Users} color="success" delay={0.3} />
      </div>

      <DataTable title="Team Members" columns={[
        { key: 'name', label: 'Name', render: (v) => (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center text-white text-xs font-bold">
              {v.split(' ').map(n => n[0]).join('')}
            </div>
            <span className="font-medium text-nexus-200">{v}</span>
          </div>
        )},
        { key: 'email', label: 'Email' },
        { key: 'department', label: 'Department' },
        { key: 'role', label: 'Role' },
        { key: 'level', label: 'Permission Level', render: (v) => levelBadge(v) },
        { key: 'status', label: 'Status', render: (v) => statusBadge(v) },
      ]} data={users} />
    </div>
  )
}
