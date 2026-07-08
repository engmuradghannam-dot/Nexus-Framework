import React from 'react'
import { motion } from 'framer-motion'
import { BrainCircuit, Zap, Activity, AlertTriangle, CheckCircle2 } from 'lucide-react'
import KPICard from '../components/KPICard'
import ChartCard from '../components/ChartCard'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const accuracyHistory = [
  { day: 'Mon', modelA: 89, modelC: 92 },
  { day: 'Tue', modelA: 90, modelC: 93 },
  { day: 'Wed', modelA: 91, modelC: 94 },
  { day: 'Thu', modelA: 90, modelC: 95 },
  { day: 'Fri', modelA: 92, modelC: 96 },
  { day: 'Sat', modelA: 93, modelC: 96 },
  { day: 'Sun', modelA: 94, modelC: 97 },
]

const modelTypes = [
  { name: 'Classification', value: 4, fill: '#6366f1' },
  { name: 'NLP', value: 3, fill: '#8b5cf6' },
  { name: 'Forecasting', value: 2, fill: '#10b981' },
  { name: 'Anomaly', value: 2, fill: '#f59e0b' },
  { name: 'CV', value: 1, fill: '#ef4444' },
]

const insights = [
  { title: 'Project Alpha risk prediction: 78% delay probability', severity: 'warning', model: 'RiskNet v2', time: '2m ago' },
  { title: 'Branch 3 inventory anomaly detected', severity: 'critical', model: 'AnomalyGuard', time: '15m ago' },
  { title: 'Market trend forecast: Tech sector +12% next quarter', severity: 'info', model: 'ForeSight', time: '1h ago' },
  { title: 'Compliance check automation ready', severity: 'success', model: 'ReguBot', time: '3h ago' },
]

const severityBadge = (s) => {
  const map = { critical: 'badge-danger', warning: 'badge-warning', info: 'badge-info', success: 'badge-success' }
  return <span className={map[s] || 'badge'}>{s}</span>
}

export default function AI() {
  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-nexus-50">AI Engine</h1>
            <p className="text-sm text-nexus-400 mt-1">Model management, predictions & intelligent insights</p>
          </div>
          <button className="btn-primary flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Deploy Model
          </button>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Models Deployed" value="12" trend="up" trendValue="2 new" icon={BrainCircuit} color="primary" delay={0} />
        <KPICard title="Avg Accuracy" value="94.2%" trend="up" trendValue="1.8%" icon={CheckCircle2} color="success" delay={0.1} />
        <KPICard title="Predictions Today" value="8,432" subtitle="Latency: 45ms avg" icon={Activity} color="info" delay={0.2} />
        <KPICard title="Unread Insights" value="7" subtitle="3 critical, 2 warnings" icon={AlertTriangle} color="warning" delay={0.3} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <ChartCard title="Model Accuracy Trend" className="lg:col-span-2" delay={0.4}>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={accuracyHistory}>
              <defs>
                <linearGradient id="gradA" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/><stop offset="95%" stopColor="#6366f1" stopOpacity={0}/></linearGradient>
                <linearGradient id="gradC" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/><stop offset="95%" stopColor="#10b981" stopOpacity={0}/></linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="day" stroke="#475569" fontSize={12} />
              <YAxis domain={[80, 100]} stroke="#475569" fontSize={12} />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }} />
              <Area type="monotone" dataKey="modelA" stroke="#6366f1" fill="url(#gradA)" strokeWidth={2} />
              <Area type="monotone" dataKey="modelC" stroke="#10b981" fill="url(#gradC)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Model Distribution" delay={0.5}>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={modelTypes} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={5} dataKey="value">
                {modelTypes.map((e, i) => <Cell key={i} fill={e.fill} />)}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-2 justify-center">
            {modelTypes.map(m => (
              <div key={m.name} className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: m.fill }} />
                <span className="text-xs text-nexus-400">{m.name}</span>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>

      <ChartCard title="AI Insights Feed" delay={0.6}>
        <div className="space-y-3">
          {insights.map((ins, i) => (
            <div key={i} className="flex items-center gap-4 p-3 rounded-xl bg-nexus-900/50 hover:bg-nexus-800/50 transition-colors">
              <div className="flex-1">
                <p className="text-sm text-nexus-200">{ins.title}</p>
                <p className="text-xs text-nexus-500 mt-0.5">{ins.model} • {ins.time}</p>
              </div>
              {severityBadge(ins.severity)}
            </div>
          ))}
        </div>
      </ChartCard>
    </div>
  )
}
