import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { MapPin, Plus, Phone, Warehouse } from 'lucide-react'
import KPICard from '../components/KPICard'
import DataTable from '../components/DataTable'

const branches = [
  { name: 'Headquarters', code: 'HQ-001', address: '123 Main St, Dubai, UAE', manager: 'Murad Ghannam', phone: '+971-4-123-4567', warehouses: 3, lat: 25.2048, lng: 55.2708 },
  { name: 'Branch Jeddah', code: 'JED-001', address: '456 King Rd, Jeddah, KSA', manager: 'Ahmed Ali', phone: '+966-12-345-6789', warehouses: 2, lat: 21.4858, lng: 39.1925 },
  { name: 'Branch Riyadh', code: 'RYD-001', address: '789 Olaya St, Riyadh, KSA', manager: 'Khalid Omar', phone: '+966-11-234-5678', warehouses: 4, lat: 24.7136, lng: 46.6753 },
  { name: 'Branch Cairo', code: 'CAI-001', address: '321 Nile St, Cairo, Egypt', manager: 'Sara Hassan', phone: '+20-2-123-4567', warehouses: 2, lat: 30.0444, lng: 31.2357 },
  { name: 'Branch Istanbul', code: 'IST-001', address: '654 Taksim Sq, Istanbul, Turkey', manager: 'Mehmet Yilmaz', phone: '+90-212-345-6789', warehouses: 1, lat: 41.0082, lng: 28.9784 },
]

export default function Branches() {
  const [showMap, setShowMap] = useState(false)

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-nexus-50">Branches & Locations</h1>
            <p className="text-sm text-nexus-400 mt-1">Manage branches with Google Maps integration</p>
          </div>
          <button className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Add Branch
          </button>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KPICard title="Total Branches" value="5" icon={MapPin} color="primary" delay={0} />
        <KPICard title="Active Warehouses" value="12" icon={Warehouse} color="success" delay={0.1} />
        <KPICard title="Countries" value="4" icon={MapPin} color="info" delay={0.2} />
      </div>

      <div className="glass-card overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-nexus-800">
          <h3 className="text-sm font-semibold text-nexus-200">Branch Directory</h3>
          <button onClick={() => setShowMap(!showMap)} className="btn-secondary text-sm">
            {showMap ? 'List View' : 'Map View'}
          </button>
        </div>

        {showMap ? (
          <div className="h-96 bg-nexus-900 flex items-center justify-center">
            <div className="text-center">
              <MapPin className="w-12 h-12 text-nexus-600 mx-auto mb-4" />
              <p className="text-nexus-400">Google Maps integration ready</p>
              <p className="text-xs text-nexus-500 mt-2">API Key required for live map</p>
            </div>
          </div>
        ) : (
          <DataTable columns={[
            { key: 'name', label: 'Branch Name' },
            { key: 'code', label: 'Code' },
            { key: 'address', label: 'Address' },
            { key: 'manager', label: 'Manager', render: (v) => (
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-accent-primary/20 flex items-center justify-center text-xs text-accent-primary font-bold">{v.split(' ').map(n => n[0]).join('')}</div>
                <span>{v}</span>
              </div>
            )},
            { key: 'phone', label: 'Phone' },
            { key: 'warehouses', label: 'Warehouses' },
            { key: 'lat', label: 'Coordinates', render: (v, row) => <span className="text-xs text-nexus-500 font-mono">{v.toFixed(4)}, {row.lng.toFixed(4)}</span> },
          ]} data={branches} searchable={false} filterable={false} />
        )}
      </div>
    </div>
  )
}
