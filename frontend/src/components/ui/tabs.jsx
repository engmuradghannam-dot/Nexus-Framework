import React, { createContext, useContext, useState } from 'react'

const TabsContext = createContext(null)

export function Tabs({ defaultValue, value, onValueChange, className = '', children }) {
  const [internal, setInternal] = useState(defaultValue ?? '')
  const active = value !== undefined ? value : internal
  const setActive = onValueChange || setInternal
  return (
    <TabsContext.Provider value={{ active, setActive }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  )
}

export function TabsList({ className = '', children }) {
  return (
    <div className={`inline-flex items-center gap-1 rounded-lg bg-[#f3f2f1] p-1 ${className}`}>
      {children}
    </div>
  )
}

export function TabsTrigger({ value, className = '', children }) {
  const ctx = useContext(TabsContext)
  const isActive = ctx.active === value
  return (
    <button
      type="button"
      onClick={() => ctx.setActive(value)}
      className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
        isActive ? 'bg-white text-[#0078d4] shadow-sm' : 'text-[#605e5c] hover:text-[#323130]'
      } ${className}`}
    >
      {children}
    </button>
  )
}

export function TabsContent({ value, className = '', children }) {
  const ctx = useContext(TabsContext)
  if (ctx.active !== value) return null
  return <div className={className}>{children}</div>
}

export default Tabs
