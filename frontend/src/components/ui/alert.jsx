import React from 'react'

export function Alert({ children, variant = 'default', className = '' }) {
  const variants = {
    default: 'bg-nexus-800/50 border-nexus-700/50 text-nexus-200',
    destructive: 'bg-red-500/10 border-red-500/20 text-red-400',
  }

  return (
    <div className={`p-4 rounded-lg border ${variants[variant] || variants.default} ${className}`}>
      {children}
    </div>
  )
}

export function AlertDescription({ children, className = '' }) {
  return <p className={`text-sm ${className}`}>{children}</p>
}
