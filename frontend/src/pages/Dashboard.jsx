import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import {
  LayoutDashboard, FolderKanban, Building2, BrainCircuit,
  ShieldCheck, TrendingUp, Activity, AlertTriangle
} from 'lucide-react'
import KPICard from '../components/KPICard'
import ChartCard from '../components/ChartCard'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis
} from 'recharts'

const activityData = [
  { name: 'Mon', projects: 12, tasks: 45, compliance: 8 },
  { name: 'Tue', projects: 15, tasks: 38, compliance: 12 },
  { name: 'Wed', projects: 18, tasks: 52, compliance: 10 },
  { name: 'Thu', projects: 14, tasks: 41, compliance: 15 },
  { name: 'Fri', projects: 20, tasks: 48, compliance: 11 },
  { name: 'Sat', projects: 8, tasks: 22, compliance: 5 },
  { name: 'Sun', projects: 5, tasks: 15, compliance: 3 },
]

const moduleHealth = [
  { name: 'PMO', value: 92, fill: '#6366f1' },
  { name: 'Industry', value: 87, fill: '#8b5cf6' },
  { name: 'AI', value: 95, fill: '#10b981' },
  { name: 'Regulatory', value: 78, fill: '#f59e0b' },
]

const riskRadar = [
  { subject: 'Financial', A: 85, fullMark: 100 },
  { subject: 'Operational', A: 70, fullMark: 100 },
  { subject: 'Legal', A: 60, fullMark: 100 },
  { subject: 'Reputational', A: 90, fullMark: 100 },
  { subject: 'Strategic', A: 75, fullMark: 100 },
  { subject: 'Compliance', A: 65, fullMark: 100 },
]

export default function Dashboard() {
  const [stats, setStats] = useState({
    projects: 24, tasks: 156, compliance: 94, aiModels: 12,
    risks: 8, branches: 6
  })

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-nexus-50">Command Center</h1>
          <p className="text-sm text-nexus-400 mt-1">Real-time enterprise overview across all modules</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge-success">All Systems Operational</span>
          <span className="text-xs text-nexus-500">Last updated: just now</span>
        </div>
      </motion.div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Active Projects"
          value={stats.projects}
          subtitle="3 overdue, 2 on hold"
          trend="up"
          trendValue="12%"
          icon={FolderKanban}
          color="primary"
          delay={0}
        />
        <KPICard
          title="Open Tasks"
          value={stats.tasks}
          subtitle="87 in progress, 45 pending"
          trend="down"
          trendValue="5%"
          icon={Activity}
          color="warning"
          delay={0.1}
        />
        <KPICard
          title="Compliance Rate"
          value={`${stats.compliance}%`}
          subtitle="2 branches need attention"
          trend="up"
          trendValue="3%"
          icon={ShieldCheck}
          color="success"
          delay={0.2}
        />
        <KPICard
          title="AI Models Deployed"
          value={stats.aiModels}
          subtitle="Avg accuracy: 94.2%"
          trend="up"
          trendValue="2 new"
          icon={BrainCircuit}
          color="info"
          delay={0.3}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <ChartCard title="Weekly Activity" className="lg:col-span-2" delay={0.4}>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={activityData}>
              <defs>
                <linearGradient id="colorProjects" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorTasks" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" stroke="#475569" fontSize={12} />
              <YAxis stroke="#475569" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }}
                labelStyle={{ color: '#e2e8f0' }}
              />
              <Area type="monotone" dataKey="projects" stroke="#6366f1" fillOpacity={1} fill="url(#colorProjects)" strokeWidth={2} />
              <Area type="monotone" dataKey="tasks" stroke="#10b981" fillOpacity={1} fill="url(#colorTasks)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Module Health" delay={0.5}>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={moduleHealth}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={4}
                dataKey="value"
              >
                {moduleHealth.map((entry, index) => (
                  <Cell key={index} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-3 mt-2 justify-center">
            {moduleHealth.map((m) => (
              <div key={m.name} className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: m.fill }} />
                <span className="text-xs text-nexus-400">{m.name} ({m.value}%)</span>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Risk Profile" delay={0.6}>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={riskRadar}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis dataKey="subject" stroke="#94a3b8" fontSize={12} />
              <PolarRadiusAxis stroke="#475569" fontSize={10} />
              <Radar name="Risk" dataKey="A" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Recent Alerts" delay={0.7}>
          <div className="space-y-3">
            {[
              { icon: AlertTriangle, color: 'text-accent-danger', bg: 'bg-accent-danger/10', title: 'Critical: Compliance breach in Branch 3', time: '2 min ago' },
              { icon: TrendingUp, color: 'text-accent-success', bg: 'bg-accent-success/10', title: 'AI Model accuracy improved to 96.4%', time: '15 min ago' },
              { icon: Activity, color: 'text-accent-warning', bg: 'bg-accent-warning/10', title: 'Project Phoenix milestone delayed', time: '1 hour ago' },
              { icon: Building2, color: 'text-accent-info', bg: 'bg-accent-info/10', title: 'New sector data imported: Manufacturing', time: '3 hours ago' },
            ].map((alert, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-nexus-900/50 hover:bg-nexus-800/50 transition-colors cursor-pointer">
                <div className={`p-2 rounded-lg ${alert.bg} ${alert.color}`}>
                  <alert.icon className="w-4 h-4" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-nexus-200">{alert.title}</p>
                  <p className="text-xs text-nexus-500 mt-0.5">{alert.time}</p>
                </div>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>
    </div>
  )
}
