import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { ShieldCheck, AlertTriangle, FileText, CheckCircle2, Scale, Gavel } from 'lucide-react'
import KPICard from '../components/KPICard'
import ChartCard from '../components/ChartCard'
import DataTable from '../components/DataTable'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter, ZAxis } from 'recharts'

const complianceByBranch = [
  { branch: 'HQ', pass: 95, fail: 5, partial: 0 },
  { branch: 'Branch 1', pass: 82, fail: 12, partial: 6 },
  { branch: 'Branch 2', pass: 78, fail: 15, partial: 7 },
  { branch: 'Branch 3', pass: 45, fail: 40, partial: 15 },
  { branch: 'Branch 4', pass: 90, fail: 8, partial: 2 },
  { branch: 'Branch 5', pass: 88, fail: 10, partial: 2 },
]

const riskHeatmap = [
  { x: 2, y: 3, z: 6, name: 'Cyber Risk' },
  { x: 4, y: 5, z: 20, name: 'Data Breach' },
  { x: 3, y: 4, z: 12, name: 'Non-Compliance' },
  { x: 1, y: 2, z: 2, name: 'Minor Audit' },
  { x: 5, y: 5, z: 25, name: 'System Failure' },
  { x: 3, y: 2, z: 6, name: 'Vendor Risk' },
]

const regulations = [
  { code: 'GDPR-2026', title: 'Data Protection Regulation', jurisdiction: 'EU', severity: 'Critical', status: 'Active', effective: '2026-01-01', review: '2026-12-31' },
  { code: 'SOX-11', title: 'Sarbanes-Oxley Act', jurisdiction: 'US', severity: 'High', status: 'Active', effective: '2025-07-01', review: '2026-07-01' },
  { code: 'PCI-DSS-v4', title: 'Payment Card Security', jurisdiction: 'Global', severity: 'High', status: 'Under Review', effective: '2025-03-01', review: '2026-09-01' },
  { code: 'HIPAA-2026', title: 'Health Data Privacy', jurisdiction: 'US', severity: 'Medium', status: 'Active', effective: '2026-02-01', review: '2026-08-01' },
  { code: 'ISO-27001', title: 'Information Security Mgmt', jurisdiction: 'Global', severity: 'Medium', status: 'Active', effective: '2025-01-01', review: '2026-06-01' },
]

const sevBadge = (s) => {
  const map = { Critical: 'badge-danger', High: 'badge-warning', Medium: 'badge-info', Low: 'badge-success' }
  return <span className={map[s] || 'badge'}>{s}</span>
}

const statusBadge = (s) => {
  const map = { Active: 'badge-success', 'Under Review': 'badge-warning', Draft: 'badge-info', Superseded: 'badge' }
  return <span className={map[s] || 'badge'}>{s}</span>
}

export default function Regulatory() {
  const [tab, setTab] = useState('overview')

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-nexus-50">Regulatory & Compliance</h1>
            <p className="text-sm text-nexus-400 mt-1">Regulation tracking, compliance audits & risk management</p>
          </div>
          <button className="btn-primary flex items-center gap-2">
            <FileText className="w-4 h-4" />
            New Regulation
          </button>
        </div>
      </motion.div>

      <div className="flex gap-2 border-b border-nexus-800 pb-0">
        {['overview', 'regulations', 'compliance', 'risks'].map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium rounded-t-xl transition-colors ${tab === t ? 'text-accent-primary border-b-2 border-accent-primary bg-accent-primary/5' : 'text-nexus-400 hover:text-nexus-200'}`}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <KPICard title="Active Regulations" value="24" subtitle="5 critical, 12 high" icon={Gavel} color="primary" delay={0} />
            <KPICard title="Compliance Rate" value="78%" trend="down" trendValue="5%" icon={CheckCircle2} color="warning" delay={0.1} />
            <KPICard title="Open Risks" value="12" subtitle="3 critical, 4 high" icon={AlertTriangle} color="danger" delay={0.2} />
            <KPICard title="Overdue Reviews" value="3" subtitle="Next: GDPR-2026" icon={Scale} color="info" delay={0.3} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartCard title="Compliance by Branch" delay={0.4}>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={complianceByBranch}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="branch" stroke="#475569" fontSize={12} />
                  <YAxis stroke="#475569" fontSize={12} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }} />
                  <Bar dataKey="pass" stackId="a" fill="#10b981" />
                  <Bar dataKey="partial" stackId="a" fill="#f59e0b" />
                  <Bar dataKey="fail" stackId="a" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Risk Heatmap (Likelihood × Impact)" delay={0.5}>
              <ResponsiveContainer width="100%" height={260}>
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis type="number" dataKey="x" name="Likelihood" stroke="#475569" fontSize={12} domain={[0, 6]} />
                  <YAxis type="number" dataKey="y" name="Impact" stroke="#475569" fontSize={12} domain={[0, 6]} />
                  <ZAxis type="number" dataKey="z" range={[50, 400]} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }} />
                  <Scatter data={riskHeatmap} fill="#ef4444" />
                </ScatterChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>
        </>
      )}

      {tab === 'regulations' && (
        <DataTable title="Regulation Library" columns={[
          { key: 'code', label: 'Code' },
          { key: 'title', label: 'Title' },
          { key: 'jurisdiction', label: 'Jurisdiction' },
          { key: 'severity', label: 'Severity', render: (v) => sevBadge(v) },
          { key: 'status', label: 'Status', render: (v) => statusBadge(v) },
          { key: 'effective', label: 'Effective' },
          { key: 'review', label: 'Review Date' },
        ]} data={regulations} />
      )}

      {tab !== 'overview' && tab !== 'regulations' && (
        <div className="glass-card p-8 text-center">
          <ShieldCheck className="w-12 h-12 text-nexus-600 mx-auto mb-4" />
          <p className="text-nexus-400">{tab} view with full audit trail coming soon</p>
        </div>
      )}
    </div>
  )
}
