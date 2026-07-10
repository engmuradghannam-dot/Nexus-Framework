import React, { createContext, useContext, useState } from 'react'

const SelectContext = createContext(null)

export function Select({ value, onValueChange, defaultValue, children }) {
  const [internal, setInternal] = useState(defaultValue ?? '')
  const [open, setOpen] = useState(false)
  const current = value !== undefined ? value : internal
  const setValue = (v) => {
    if (onValueChange) onValueChange(v)
    else setInternal(v)
    setOpen(false)
  }
  return (
    <SelectContext.Provider value={{ value: current, setValue, open, setOpen }}>
      <div className="relative">{children}</div>
    </SelectContext.Provider>
  )
}

export function SelectTrigger({ className = '', children }) {
  const ctx = useContext(SelectContext)
  return (
    <button
      type="button"
      onClick={() => ctx.setOpen(!ctx.open)}
      className={`flex h-10 w-full items-center justify-between rounded-md border border-[#d1d1d1] bg-white px-3 py-2 text-sm text-[#323130] focus:outline-none focus:ring-2 focus:ring-[#0078d4]/40 ${className}`}
    >
      {children}
      <span className="ml-2 text-[#605e5c]">▾</span>
    </button>
  )
}

export function SelectValue({ placeholder }) {
  const ctx = useContext(SelectContext)
  return <span className={ctx.value ? '' : 'text-[#a19f9d]'}>{ctx.value || placeholder}</span>
}

export function SelectContent({ children }) {
  const ctx = useContext(SelectContext)
  if (!ctx.open) return null
  return (
    <div className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border border-[#d1d1d1] bg-white py-1 shadow-lg">
      {children}
    </div>
  )
}

export function SelectItem({ value, children }) {
  const ctx = useContext(SelectContext)
  return (
    <div
      onClick={() => ctx.setValue(value)}
      className={`cursor-pointer px-3 py-2 text-sm hover:bg-[#f3f2f1] ${ctx.value === value ? 'bg-[#e1efff] text-[#0078d4]' : 'text-[#323130]'}`}
    >
      {children}
    </div>
  )
}

export default Select
