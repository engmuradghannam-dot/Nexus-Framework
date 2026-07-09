import React from 'react'

export function Progress({ value = 0, className = '' }) {
  return (
    <div className={`w-full bg-nexus-700 rounded-full h-2 ${className}`}>
      <div
        className="bg-gradient-to-r from-accent-primary to-accent-secondary h-2 rounded-full transition-all duration-300"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  )
}
