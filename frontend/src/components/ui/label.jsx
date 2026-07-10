import React from 'react'

export function Label({ className = '', children, ...props }) {
  return (
    <label
      className={`block text-sm font-medium text-[#323130] mb-1 ${className}`}
      {...props}
    >
      {children}
    </label>
  )
}

export default Label
