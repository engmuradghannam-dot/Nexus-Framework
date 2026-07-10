// components/FluentUI/FluentTable.tsx
import { ReactNode, useState } from 'react';
import { ChevronUp, ChevronDown, MoreHorizontal, ChevronLeft, ChevronRight } from 'lucide-react';

interface Column<T> {
  key: string;
  label: string;
  width?: string;
  sortable?: boolean;
  render?: (value: any, row: T) => ReactNode;
}

interface FluentTableProps<T> {
  columns: Column<T>[];
  data: T[];
  title?: string;
  subtitle?: string;
  selectable?: boolean;
  onRowClick?: (row: T) => void;
  actions?: (row: T) => ReactNode;
  emptyMessage?: string;
  pageSize?: number;
}

export function FluentTable<T extends Record<string, any>>({
  columns,
  data,
  title,
  subtitle,
  selectable = false,
  onRowClick,
  actions,
  emptyMessage = 'لا توجد بيانات',
  pageSize = 10,
}: FluentTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sortedData = sortKey
    ? [...data].sort((a, b) => {
        const aVal = a[sortKey];
        const bVal = b[sortKey];
        if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
        return 0;
      })
    : data;

  const totalPages = Math.ceil(sortedData.length / pageSize);
  const paginatedData = sortedData.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const toggleSelectAll = () => {
    if (selectedRows.size === paginatedData.length) {
      setSelectedRows(new Set());
    } else {
      setSelectedRows(new Set(paginatedData.map((row, i) => row.id || String(i))));
    }
  };

  const toggleRow = (id: string) => {
    const newSet = new Set(selectedRows);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelectedRows(newSet);
  };

  return (
    <div className="bg-white border border-[#e1dfdd] rounded-sm shadow-sm">
      {/* Header */}
      {(title || subtitle) && (
        <div className="px-5 py-4 border-b border-[#e1dfdd]">
          {title && <h3 className="text-base font-semibold text-[#323130]">{title}</h3>}
          {subtitle && <p className="text-sm text-[#605e5c] mt-1">{subtitle}</p>}
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[#e1dfdd] bg-[#faf9f8]">
              {selectable && (
                <th className="px-4 py-3 w-12">
                  <input
                    type="checkbox"
                    checked={selectedRows.size === paginatedData.length && paginatedData.length > 0}
                    onChange={toggleSelectAll}
                    className="w-4 h-4 rounded border-[#8a8886] text-[#0078d4] focus:ring-[#0078d4]"
                  />
                </th>
              )}
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`
                    px-4 py-3 text-left text-sm font-semibold text-[#323130]
                    ${col.sortable ? 'cursor-pointer hover:bg-[#f3f2f1]' : ''}
                  `}
                  style={{ width: col.width }}
                  onClick={() => col.sortable && handleSort(col.key)}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {col.sortable && sortKey === col.key && (
                      sortDir === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                    )}
                  </div>
                </th>
              ))}
              {actions && <th className="px-4 py-3 w-10"></th>}
            </tr>
          </thead>
          <tbody>
            {paginatedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length + (selectable ? 1 : 0) + (actions ? 1 : 0)} className="px-4 py-12 text-center text-[#605e5c]">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, idx) => {
                const rowId = row.id || String(idx);
                const isSelected = selectedRows.has(rowId);
                return (
                  <tr
                    key={rowId}
                    className={`
                      border-b border-[#f3f2f1] text-sm
                      ${onRowClick ? 'cursor-pointer' : ''}
                      ${isSelected ? 'bg-[#eff6fc]' : 'hover:bg-[#f3f2f1]'}
                    `}
                    onClick={() => onRowClick?.(row)}
                  >
                    {selectable && (
                      <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleRow(rowId)}
                          className="w-4 h-4 rounded border-[#8a8886] text-[#0078d4] focus:ring-[#0078d4]"
                        />
                      </td>
                    )}
                    {columns.map((col) => (
                      <td key={col.key} className="px-4 py-3 text-[#323130]">
                        {col.render ? col.render(row[col.key], row) : row[col.key]}
                      </td>
                    ))}
                    {actions && (
                      <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                        <div className="relative group">
                          <button className="p-1 text-[#605e5c] hover:bg-[#f3f2f1] rounded">
                            <MoreHorizontal size={16} />
                          </button>
                          <div className="absolute right-0 mt-1 w-40 bg-white border border-[#e1dfdd] shadow-lg rounded-sm hidden group-hover:block z-10">
                            {actions(row)}
                          </div>
                        </div>
                      </td>
                    )}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="px-5 py-3 border-t border-[#e1dfdd] flex items-center justify-between">
          <span className="text-sm text-[#605e5c]">
            الصفوف {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, sortedData.length)} من {sortedData.length}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1.5 text-[#605e5c] hover:bg-[#f3f2f1] rounded disabled:opacity-40"
            >
              <ChevronRight size={18} />
            </button>
            <span className="text-sm text-[#323130] px-3">
              صفحة {currentPage} من {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1.5 text-[#605e5c] hover:bg-[#f3f2f1] rounded disabled:opacity-40"
            >
              <ChevronLeft size={18} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default FluentTable;
