import React from 'react'

export function Input({ className = '', ...props }) {
  return (
    <input
      className={`flex h-10 w-full rounded-md border border-[#d1d1d1] bg-white px-3 py-2 text-sm text-[#323130] placeholder:text-[#a19f9d] focus:outline-none focus:ring-2 focus:ring-[#0078d4]/40 focus:border-[#0078d4] disabled:opacity-50 ${className}`}
      {...props}
    />
  )
}

export default Input
