import React from 'react'
import { motion } from 'framer-motion'

export default function ChartCard({ title, children, delay = 0, className = '' }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className={`glass-card p-6 ${className}`}
    >
      <h3 className="text-sm font-semibold text-nexus-200 mb-4 tracking-wide">{title}</h3>
      {children}
    </motion.div>
  )
}
