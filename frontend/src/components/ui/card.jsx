import React from 'react'

export function Card({ children, className = '' }) {
  return (
    <div className={`bg-nexus-800/50 backdrop-blur-sm border border-nexus-700/50 rounded-xl ${className}`}>
      {children}
    </div>
  )
}

export function CardHeader({ children, className = '' }) {
  return <div className={`p-6 pb-4 ${className}`}>{children}</div>
}

export function CardTitle({ children, className = '' }) {
  return <h3 className={`text-lg font-semibold text-nexus-100 ${className}`}>{children}</h3>
}

export function CardContent({ children, className = '' }) {
  return <div className={`p-6 pt-0 ${className}`}>{children}</div>
}

export function CardDescription({ children, className = '' }) {
  return <p className={`text-sm text-nexus-400 ${className}`}>{children}</p>
}
