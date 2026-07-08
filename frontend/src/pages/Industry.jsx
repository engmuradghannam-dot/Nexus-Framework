import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Building2, TrendingUp, Globe, BarChart3, Award } from 'lucide-react'
import KPICard from '../components/KPICard'
import ChartCard from '../components/ChartCard'
import DataTable from '../components/DataTable'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'

const marketData = [
  { sector: 'Tech', marketCap: 850, revenue: 420 },
  { sector: 'Finance', marketCap: 620, revenue: 310 },
  { sector: 'Health', marketCap: 480, revenue: 240 },
  { sector: 'Energy', marketCap: 390, revenue: 180 },
  { sector: 'Retail', marketCap: 280, revenue: 150 },
]

const trendData = [
  { month: 'Jan', tech: 12, finance: 8, health: 5 },
  { month: 'Feb', tech: 15, finance: 9, health: 6 },
  { month: 'Mar', tech: 18, finance: 11, health: 8 },
  { month: 'Apr', tech: 22, finance: 13, health: 10 },
  { month: 'May', tech: 25, finance: 15, health: 12 },
  { month: 'Jun', tech: 28, finance: 17, health: 14 },
]

const companies = [
  { name: 'TechCorp Inc.', ticker: 'TCI', sector: 'Technology', marketCap: '$850B', revenue: '$420B', employees: '45K', growth: '+12%' },
  { name: 'FinanceFirst', ticker: 'FFI', sector: 'Finance', marketCap: '$620B', revenue: '$310B', employees: '32K', growth: '+8%' },
  { name: 'HealthPlus', ticker: 'HPL', sector: 'Healthcare', marketCap: '$480B', revenue: '$240B', employees: '28K', growth: '+15%' },
  { name: 'EnergyX', ticker: 'ENX', sector: 'Energy', marketCap: '$390B', revenue: '$180B', employees: '55K', growth: '+5%' },
  { name: 'RetailMax', ticker: 'RTM', sector: 'Retail', marketCap: '$280B', revenue: '$150B', employees: '120K', growth: '+3%' },
]

export default function Industry() {
  const [tab, setTab] = useState('overview')

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-nexus-50">Industry Intelligence</h1>
            <p className="text-sm text-nexus-400 mt-1">Sector analysis, company benchmarking & market metrics</p>
          </div>
          <button className="btn-primary flex items-center gap-2">
            <Globe className="w-4 h-4" />
            Import Data
          </button>
        </div>
      </motion.div>

      <div className="flex gap-2 border-b border-nexus-800 pb-0">
        {['overview', 'companies', 'sectors', 'metrics'].map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium rounded-t-xl transition-colors ${tab === t ? 'text-accent-primary border-b-2 border-accent-primary bg-accent-primary/5' : 'text-nexus-400 hover:text-nexus-200'}`}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <KPICard title="Tracked Sectors" value="12" trend="up" trendValue="2 new" icon={Globe} color="info" delay={0} />
            <KPICard title="Companies" value="48" subtitle="Top 10 by market cap" icon={Building2} color="primary" delay={0.1} />
            <KPICard title="Avg Growth" value="8.6%" trend="up" trendValue="1.2%" icon={TrendingUp} color="success" delay={0.2} />
            <KPICard title="Market Leaders" value="5" subtitle="Across all sectors" icon={Award} color="warning" delay={0.3} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartCard title="Market Cap by Sector ($B)" delay={0.4}>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={marketData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="sector" stroke="#475569" fontSize={12} />
                  <YAxis stroke="#475569" fontSize={12} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }} />
                  <Bar dataKey="marketCap" fill="#6366f1" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Sector Growth Trends" delay={0.5}>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="month" stroke="#475569" fontSize={12} />
                  <YAxis stroke="#475569" fontSize={12} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }} />
                  <Line type="monotone" dataKey="tech" stroke="#6366f1" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="finance" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="health" stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>
        </>
      )}

      {tab === 'companies' && (
        <DataTable title="Company Directory" columns={[
          { key: 'name', label: 'Company' },
          { key: 'ticker', label: 'Ticker' },
          { key: 'sector', label: 'Sector' },
          { key: 'marketCap', label: 'Market Cap' },
          { key: 'revenue', label: 'Revenue' },
          { key: 'employees', label: 'Employees' },
          { key: 'growth', label: 'Growth', render: (v) => <span className="text-accent-success">{v}</span> },
        ]} data={companies} />
      )}

      {tab !== 'overview' && tab !== 'companies' && (
        <div className="glass-card p-8 text-center">
          <BarChart3 className="w-12 h-12 text-nexus-600 mx-auto mb-4" />
          <p className="text-nexus-400">{tab} view coming with full data integration</p>
        </div>
      )}
    </div>
  )
}
