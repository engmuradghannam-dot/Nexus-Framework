import React, { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { projects, projectApi } from '../lib/api'
import { ArrowLeft, Calendar, Clock, ChevronRight, ChevronLeft } from 'lucide-react'

const STATUS_COLORS = {
  'Open': '#9CA3AF',
  'Working': '#3B82F6',
  'Pending Review': '#F59E0B',
  'Completed': '#10B981',
  'Cancelled': '#EF4444',
}

const TYPE_COLORS = {
  'task': '#3B82F6',
  'milestone': '#8B5CF6',
}

export default function GanttChart() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [zoom, setZoom] = useState(40) // pixels per day

  const { data: project } = useQuery({
    queryKey: ['project', id],
    queryFn: () => projects.get(id),
  })

  const { data: timeline, isLoading } = useQuery({
    queryKey: ['timeline', id],
    queryFn: () => projectApi.timeline(id),
    enabled: !!id,
  })

  const items = timeline?.items || []

  // Calculate date range
  const { minDate, maxDate, totalDays } = useMemo(() => {
    const dates = items
      .map(i => i.start)
      .filter(Boolean)
      .map(d => new Date(d))
    if (dates.length === 0) return { minDate: new Date(), maxDate: new Date(), totalDays: 30 }
    const min = new Date(Math.min(...dates))
    const max = new Date(Math.max(...dates))
    // Add padding
    min.setDate(min.getDate() - 3)
    max.setDate(max.getDate() + 7)
    const days = Math.ceil((max - min) / (1000 * 60 * 60 * 24))
    return { minDate: min, maxDate: max, totalDays: Math.max(days, 14) }
  }, [items])

  const getPosition = (startStr, endStr) => {
    const start = new Date(startStr)
    const end = endStr ? new Date(endStr) : new Date(start.getTime() + 86400000)
    const offsetDays = Math.ceil((start - minDate) / (1000 * 60 * 60 * 24))
    const duration = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) || 1
    return {
      left: offsetDays * zoom,
      width: Math.max(duration * zoom, 20),
    }
  }

  const formatDate = (date) => {
    return new Date(date).toLocaleDateString('ar-SA', { month: 'short', day: 'numeric' })
  }

  // Generate month headers
  const monthHeaders = useMemo(() => {
    const headers = []
    let current = new Date(minDate)
    while (current <= maxDate) {
      const monthStart = new Date(current)
      const monthEnd = new Date(current.getFullYear(), current.getMonth() + 1, 0)
      const startDay = Math.ceil((monthStart - minDate) / (1000 * 60 * 60 * 24))
      const daysInMonth = Math.ceil((Math.min(monthEnd, maxDate) - monthStart) / (1000 * 60 * 60 * 24)) + 1
      headers.push({
        label: monthStart.toLocaleDateString('ar-SA', { month: 'long', year: 'numeric' }),
        left: startDay * zoom,
        width: daysInMonth * zoom,
      })
      current = new Date(current.getFullYear(), current.getMonth() + 1, 1)
    }
    return headers
  }, [minDate, maxDate, zoom])

  if (isLoading) {
    return (
      <div className="flex justify-center p-10">
        <div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div>
      </div>
    )
  }

  return (
    <div dir="rtl" className="h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 px-4">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/projects')} className="p-2 hover:bg-gray-100 rounded-lg">
            <ArrowLeft size={20} className="text-gray-500" />
          </button>
          <div>
            <h2 className="text-2xl font-bold text-gray-800">شريط زمني (Gantt)</h2>
            <p className="text-gray-500 text-sm">{project?.project_name}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setZoom(Math.max(20, zoom - 10))} className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200">
            <ChevronRight size={16} />
          </button>
          <span className="text-sm text-gray-500">{zoom}px/يوم</span>
          <button onClick={() => setZoom(Math.min(100, zoom + 10))} className="p-2 bg-gray-100 rounded-lg hover:bg-gray-200">
            <ChevronLeft size={16} />
          </button>
        </div>
      </div>

      {/* Gantt Chart */}
      <div className="bg-white rounded-xl shadow-sm border overflow-auto" style={{ height: 'calc(100vh - 180px)' }}>
        <div style={{ width: Math.max(totalDays * zoom + 300, 800), minHeight: '100%' }}>
          {/* Month headers */}
          <div className="flex border-b bg-gray-50 sticky top-0 z-10">
            <div className="flex-shrink-0 w-64 p-3 border-l font-bold text-sm text-gray-700 sticky right-0 bg-gray-50 z-20">
              المهمة
            </div>
            <div className="flex-1 relative" style={{ height: 40 }}>
              {monthHeaders.map((h, i) => (
                <div
                  key={i}
                  className="absolute top-0 border-l text-xs font-medium text-gray-500 p-2"
                  style={{ left: h.left, width: h.width }}
                >
                  {h.label}
                </div>
              ))}
            </div>
          </div>

          {/* Items */}
          {items.length === 0 ? (
            <div className="p-10 text-center text-gray-400">
              <Calendar size={48} className="mx-auto mb-3 opacity-50" />
              <p>لا توجد مهام أو معالم مسجلة لهذا المشروع</p>
            </div>
          ) : (
            items.map((item, idx) => {
              const pos = getPosition(item.start, item.end)
              const color = item.type === 'milestone' ? TYPE_COLORS.milestone : (STATUS_COLORS[item.status] || '#9CA3AF')
              return (
                <div key={item.id} className="flex border-b hover:bg-gray-50">
                  {/* Task label */}
                  <div className="flex-shrink-0 w-64 p-3 border-l sticky right-0 bg-white z-10">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: color }}
                      />
                      <div>
                        <p className="text-sm font-medium text-gray-800">{item.name}</p>
                        <p className="text-xs text-gray-400">
                          {item.type === 'milestone' ? 'معلم' : item.assignee || 'غير معين'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Timeline bar */}
                  <div className="flex-1 relative" style={{ height: 56 }}>
                    <div
                      className="absolute top-3 rounded-md shadow-sm cursor-pointer hover:opacity-80 transition-opacity"
                      style={{
                        left: pos.left,
                        width: item.type === 'milestone' ? 12 : pos.width,
                        height: item.type === 'milestone' ? 12 : 28,
                        backgroundColor: color,
                        borderRadius: item.type === 'milestone' ? '50%' : 6,
                        transform: item.type === 'milestone' ? 'rotate(45deg)' : 'none',
                      }}
                      title={`${item.name} (${formatDate(item.start)}${item.end ? ` - ${formatDate(item.end)}` : ''})`}
                    />
                    {/* Progress fill for tasks */}
                    {item.type === 'task' && item.progress > 0 && (
                      <div
                        className="absolute top-3 rounded-md opacity-30"
                        style={{
                          left: pos.left,
                          width: pos.width * (item.progress / 100),
                          height: 28,
                          backgroundColor: '#10B981',
                          borderRadius: 6,
                        }}
                      />
                    )}
                    {/* Date label */}
                    <span className="absolute top-8 text-[10px] text-gray-400" style={{ left: pos.left }}>
                      {formatDate(item.start)}
                    </span>
                  </div>
                </div>
              )
            })
          )}

          {/* Today line */}
          {(() => {
            const today = new Date()
            if (today >= minDate && today <= maxDate) {
              const offset = Math.ceil((today - minDate) / (1000 * 60 * 60 * 24)) * zoom
              return (
                <div
                  className="absolute top-0 bottom-0 border-l-2 border-red-400 z-30 pointer-events-none"
                  style={{ left: offset + 256 }}
                >
                  <span className="absolute -top-1 -left-6 bg-red-400 text-white text-[10px] px-1.5 py-0.5 rounded">
                    اليوم
                  </span>
                </div>
              )
            }
            return null
          })()}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-3 px-4 text-xs text-gray-500">
        <span className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-blue-500" /> مهمة</span>
        <span className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-purple-500" /> معلم</span>
        <span className="flex items-center gap-1"><div className="w-8 h-2 bg-green-500 opacity-30 rounded" /> إنجاز</span>
      </div>
    </div>
  )
}
