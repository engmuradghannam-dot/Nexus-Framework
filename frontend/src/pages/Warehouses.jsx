import React from 'react'
import { motion } from 'framer-motion'
import { Warehouse, Package, AlertTriangle, TrendingUp } from 'lucide-react'
import KPICard from '../components/KPICard'
import DataTable from '../components/DataTable'

const warehouses = [
  { name: 'HQ Main Warehouse', code: 'WH-HQ-01', branch: 'Headquarters', capacity: 5000, current: 4200, occupancy: 84, status: 'Normal' },
  { name: 'HQ Cold Storage', code: 'WH-HQ-02', branch: 'Headquarters', capacity: 2000, current: 1900, occupancy: 95, status: 'Critical' },
  { name: 'Jeddah Central', code: 'WH-JED-01', branch: 'Branch Jeddah', capacity: 3500, current: 2800, occupancy: 80, status: 'Normal' },
  { name: 'Riyadh Main', code: 'WH-RYD-01', branch: 'Branch Riyadh', capacity: 6000, current: 5400, occupancy: 90, status: 'Warning' },
  { name: 'Riyadh Sub-A', code: 'WH-RYD-02', branch: 'Branch Riyadh', capacity: 2500, current: 1200, occupancy: 48, status: 'Normal' },
  { name: 'Cairo Distribution', code: 'WH-CAI-01', branch: 'Branch Cairo', capacity: 4000, current: 3600, occupancy: 90, status: 'Warning' },
]

const statusBadge = (s) => {
  const map = { Normal: 'badge-success', Warning: 'badge-warning', Critical: 'badge-danger' }
  return <span className={map[s] || 'badge'}>{s}</span>
}

export default function Warehouses() {
  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-nexus-50">Warehouse Management</h1>
            <p className="text-sm text-nexus-400 mt-1">Inventory levels, capacity & auto-reorder system</p>
          </div>
          <button className="btn-primary flex items-center gap-2">
            <Package className="w-4 h-4" />
            Add Warehouse
          </button>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KPICard title="Total Warehouses" value="12" icon={Warehouse} color="primary" delay={0} />
        <KPICard title="Total Capacity" value="23,000" subtitle="Units" icon={Package} color="info" delay={0.1} />
        <KPICard title="Avg Occupancy" value="81%" trend="up" trendValue="3%" icon={TrendingUp} color="warning" delay={0.2} />
        <KPICard title="Critical" value="1" subtitle="Needs immediate attention" icon={AlertTriangle} color="danger" delay={0.3} />
      </div>

      <DataTable title="Warehouse Inventory Status" columns={[
        { key: 'name', label: 'Warehouse' },
        { key: 'code', label: 'Code' },
        { key: 'branch', label: 'Branch' },
        { key: 'capacity', label: 'Capacity' },
        { key: 'current', label: 'Current' },
        { key: 'occupancy', label: 'Occupancy %', render: (v) => (
          <div className="flex items-center gap-2">
            <div className="w-20 h-2 bg-nexus-800 rounded-full overflow-hidden">
              <div className={`h-full rounded-full ${v >= 90 ? 'bg-accent-danger' : v >= 80 ? 'bg-accent-warning' : 'bg-accent-success'}`} style={{ width: `${v}%` }} />
            </div>
            <span className="text-xs text-nexus-400">{v}%</span>
          </div>
        )},
        { key: 'status', label: 'Status', render: (v) => statusBadge(v) },
      ]} data={warehouses} />
    </div>
  )
}
