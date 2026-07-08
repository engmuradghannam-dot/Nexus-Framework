import React, { useState } from 'react'
import { ChevronLeft, ChevronRight, Search, Filter, ArrowUpDown } from 'lucide-react'

export default function DataTable({ columns, data, title, searchable = true, filterable = true }) {
  const [search, setSearch] = useState('')
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' })
  const [page, setPage] = useState(1)
  const perPage = 10

  const filtered = data.filter((row) =>
    columns.some((col) =>
      String(row[col.key] || '').toLowerCase().includes(search.toLowerCase())
    )
  )

  const sorted = [...filtered].sort((a, b) => {
    if (!sortConfig.key) return 0
    const aVal = a[sortConfig.key]
    const bVal = b[sortConfig.key]
    if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1
    if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1
    return 0
  })

  const paginated = sorted.slice((page - 1) * perPage, page * perPage)
  const totalPages = Math.ceil(sorted.length / perPage)

  const toggleSort = (key) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }))
  }

  return (
    <div className="glass-card overflow-hidden">
      {(title || searchable || filterable) && (
        <div className="flex items-center justify-between p-4 border-b border-nexus-800">
          {title && <h3 className="text-sm font-semibold text-nexus-200">{title}</h3>}
          <div className="flex items-center gap-2">
            {searchable && (
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-nexus-500" />
                <input
                  type="text"
                  placeholder="Search..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="input-field pl-9 py-1.5 text-sm w-56"
                />
              </div>
            )}
            {filterable && (
              <button className="p-2 rounded-lg text-nexus-400 hover:bg-nexus-800 hover:text-nexus-200 transition-colors">
                <Filter className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-nexus-800">
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => col.sortable !== false && toggleSort(col.key)}
                  className={`px-4 py-3 text-left text-xs font-semibold text-nexus-400 uppercase tracking-wider ${
                    col.sortable !== false ? 'cursor-pointer hover:text-nexus-200' : ''
                  }`}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {col.sortable !== false && <ArrowUpDown className="w-3 h-3" />}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginated.map((row, idx) => (
              <tr
                key={idx}
                className="border-b border-nexus-800/50 hover:bg-nexus-800/30 transition-colors"
              >
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3 text-sm text-nexus-300">
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-between p-4 border-t border-nexus-800">
          <p className="text-xs text-nexus-500">
            Showing {(page - 1) * perPage + 1} to {Math.min(page * perPage, sorted.length)} of {sorted.length}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1.5 rounded-lg text-nexus-400 hover:bg-nexus-800 disabled:opacity-30"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-nexus-300">{page} / {totalPages}</span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-1.5 rounded-lg text-nexus-400 hover:bg-nexus-800 disabled:opacity-30"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
