import React from 'react'

export function Button({ children, variant = 'default', size = 'default', className = '', ...props }) {
  const variants = {
    default: 'bg-accent-primary hover:bg-accent-primary/90 text-white',
    outline: 'border border-nexus-600 hover:bg-nexus-800 text-nexus-200',
    ghost: 'hover:bg-nexus-800 text-nexus-200',
    danger: 'bg-red-500 hover:bg-red-600 text-white',
  }

  const sizes = {
    default: 'px-4 py-2',
    sm: 'px-3 py-1.5 text-sm',
    lg: 'px-6 py-3',
    icon: 'p-2',
  }

  return (
    <button
      className={`inline-flex items-center justify-center rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-accent-primary/50 disabled:opacity-50 ${variants[variant] || variants.default} ${sizes[size] || sizes.default} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
