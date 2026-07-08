import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  FolderKanban, CheckCircle2, Clock, AlertCircle, Target,
  Calendar, Users, DollarSign, TrendingUp, BarChart3
} from 'lucide-react'
import KPICard from '../components/KPICard'
import ChartCard from '../components/ChartCard'
import DataTable from '../components/DataTable'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend
} from 'recharts'

const projectProgress = [
  { name: 'Alpha', planned: 100, actual: 85 },
  { name: 'Beta', planned: 80, actual: 92 },
  { name: 'Gamma', planned: 60, actual: 45 },
  { name: 'Delta', planned: 40, actual: 38 },
  { name: 'Epsilon', planned: 20, actual: 25 },
]

const budgetData = [
  { month: 'Jan', budget: 50000, spent: 42000 },
  { month: 'Feb', budget: 55000, spent: 48000 },
  { month: 'Mar', budget: 60000, spent: 62000 },
  { month: 'Apr', budget: 65000, spent: 58000 },
  { month: 'May', budget: 70000, spent: 71000 },
  { month: 'Jun', budget: 75000, spent: 68000 },
]

const projects = [
  { code: 'PRJ-001', name: 'Alpha Platform', status: 'Active', progress: 85, budget: '$120K', spent: '$102K', team: 8, endDate: '2026-08-15' },
  { code: 'PRJ-002', name: 'Beta Integration', status: 'Active', progress: 92, budget: '$80K', spent: '$74K', team: 5, endDate: '2026-07-30' },
  { code: 'PRJ-003', name: 'Gamma Migration', status: 'At Risk', progress: 45, budget: '$200K', spent: '$95K', team: 12, endDate: '2026-09-01' },
  { code: 'PRJ-004', name: 'Delta Analytics', status: 'Planning', progress: 38, budget: '$60K', spent: '$23K', team: 4, endDate: '2026-10-20' },
  { code: 'PRJ-005', name: 'Epsilon Security', status: 'Completed', progress: 100, budget: '$45K', spent: '$43K', team: 3, endDate: '2026-06-15' },
]

const statusBadge = (status) => {
  const map = {
    'Active': 'badge-success',
    'At Risk': 'badge-warning',
    'Planning': 'badge-info',
    'Completed': 'badge-success',
  }
  return <span className={map[status] || 'badge'}>{status}</span>
}

export default function PMO() {
  const [tab, setTab] = useState('overview')

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-nexus-50">Project Management Office</h1>
            <p className="text-sm text-nexus-400 mt-1">Portfolio tracking, resource allocation & milestone management</p>
          </div>
          <button className="btn-primary flex items-center gap-2">
            <Target className="w-4 h-4" />
            New Project
          </button>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-nexus-800 pb-0">
        {['overview', 'projects', 'tasks', 'milestones'].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium rounded-t-xl transition-colors ${
              tab === t
                ? 'text-accent-primary border-b-2 border-accent-primary bg-accent-primary/5'
                : 'text-nexus-400 hover:text-nexus-200'
            }`}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <KPICard title="Total Projects" value="24" trend="up" trendValue="4 new" icon={FolderKanban} color="primary" delay={0} />
            <KPICard title="Active Tasks" value="156" trend="down" trendValue="12 done" icon={CheckCircle2} color="success" delay={0.1} />
            <KPICard title="At Risk" value="3" subtitle="2 overdue, 1 blocked" icon={AlertCircle} color="danger" delay={0.2} />
            <KPICard title="Budget Utilized" value="78%" subtitle="$2.1M of $2.7M" icon={DollarSign} color="warning" delay={0.3} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartCard title="Project Progress vs Plan" delay={0.4}>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={projectProgress}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#475569" fontSize={12} />
                  <YAxis stroke="#475569" fontSize={12} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }} />
                  <Legend />
                  <Bar dataKey="planned" fill="#475569" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="actual" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Budget Burn Rate" delay={0.5}>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={budgetData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="month" stroke="#475569" fontSize={12} />
                  <YAxis stroke="#475569" fontSize={12} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }} />
                  <Legend />
                  <Line type="monotone" dataKey="budget" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="spent" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>
        </>
      )}

      {tab === 'projects' && (
        <DataTable
          title="All Projects"
          columns={[
            { key: 'code', label: 'Code' },
            { key: 'name', label: 'Project Name' },
            { key: 'status', label: 'Status', render: (v) => statusBadge(v) },
            { key: 'progress', label: 'Progress', render: (v) => (
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-nexus-800 rounded-full overflow-hidden">
                  <div className="h-full bg-accent-primary rounded-full transition-all" style={{ width: `${v}%` }} />
                </div>
                <span className="text-xs text-nexus-400">{v}%</span>
              </div>
            )},
            { key: 'budget', label: 'Budget' },
            { key: 'spent', label: 'Spent' },
            { key: 'team', label: 'Team' },
            { key: 'endDate', label: 'End Date' },
          ]}
          data={projects}
        />
      )}

      {tab === 'tasks' && (
        <div className="glass-card p-8 text-center">
          <CheckCircle2 className="w-12 h-12 text-nexus-600 mx-auto mb-4" />
          <p className="text-nexus-400">Task board view coming soon with Kanban layout</p>
        </div>
      )}

      {tab === 'milestones' && (
        <div className="glass-card p-8 text-center">
          <Calendar className="w-12 h-12 text-nexus-600 mx-auto mb-4" />
          <p className="text-nexus-400">Timeline & Gantt view coming soon</p>
        </div>
      )}
    </div>
  )
}
