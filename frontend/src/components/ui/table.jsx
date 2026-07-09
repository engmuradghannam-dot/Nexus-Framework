import React from 'react'

export function Table({ children, className = '' }) {
  return <table className={`w-full text-sm text-left ${className}`}>{children}</table>
}

export function TableHeader({ children, className = '' }) {
  return <thead className={`text-xs text-nexus-400 uppercase bg-nexus-800/50 ${className}`}>{children}</thead>
}

export function TableBody({ children, className = '' }) {
  return <tbody className={`divide-y divide-nexus-700/50 ${className}`}>{children}</tbody>
}

export function TableRow({ children, className = '' }) {
  return <tr className={`hover:bg-nexus-800/30 ${className}`}>{children}</tr>
}

export function TableHead({ children, className = '' }) {
  return <th className={`px-6 py-3 font-medium ${className}`}>{children}</th>
}

export function TableCell({ children, className = '' }) {
  return <td className={`px-6 py-4 ${className}`}>{children}</td>
}
