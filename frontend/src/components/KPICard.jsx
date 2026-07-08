import React from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

export default function KPICard({ title, value, subtitle, trend, trendValue, icon: Icon, color = 'primary', delay = 0 }) {
  const colorMap = {
    primary: 'from-accent-primary/20 to-accent-primary/5 text-accent-primary',
    success: 'from-accent-success/20 to-accent-success/5 text-accent-success',
    warning: 'from-accent-warning/20 to-accent-warning/5 text-accent-warning',
    danger: 'from-accent-danger/20 to-accent-danger/5 text-accent-danger',
    info: 'from-accent-info/20 to-accent-info/5 text-accent-info',
  }

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus
  const trendColor = trend === 'up' ? 'text-accent-success' : trend === 'down' ? 'text-accent-danger' : 'text-nexus-500'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className="kpi-card"
    >
      <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${colorMap[color]} rounded-full blur-2xl opacity-20 -translate-y-1/2 translate-x-1/2`} />
      <div className="relative">
        <div className="flex items-center justify-between mb-4">
          <div className={`p-2.5 rounded-xl bg-gradient-to-br ${colorMap[color]}`}>
            <Icon className="w-5 h-5" />
          </div>
          {trend && (
            <div className={`kpi-trend ${trendColor}`}>
              <TrendIcon className="w-3.5 h-3.5" />
              <span>{trendValue}</span>
            </div>
          )}
        </div>
        <p className="kpi-value">{value}</p>
        <p className="kpi-label">{title}</p>
        {subtitle && <p className="text-xs text-nexus-500 mt-1">{subtitle}</p>}
      </div>
    </motion.div>
  )
}
