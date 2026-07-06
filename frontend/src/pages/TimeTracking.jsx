import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { timeEntries, timeEntryApi, tasks, projects } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import {
  Clock, Play, Square, Plus, X, Calendar, BarChart3, Timer,
  TrendingUp, DollarSign, Filter
} from 'lucide-react'

export default function TimeTracking() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [activeTimer, setActiveTimer] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const [showNewEntry, setShowNewEntry] = useState(false)
  const [newEntry, setNewEntry] = useState({
    task: '', project: '', description: '', start_time: '', end_time: '',
    entry_type: 'Regular', is_billable: true, hourly_rate: '',
  })
  const [filter, setFilter] = useState('all')

  const { data: entries, isLoading } = useQuery({
    queryKey: ['timeEntries'],
    queryFn: timeEntryApi.myEntries,
  })

  const { data: dashboard } = useQuery({
    queryKey: ['timeDashboard'],
    queryFn: timeEntryApi.dashboard,
  })

  const { data: tasksList } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasks.list(),
  })

  const { data: projectsList } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projects.list(),
  })

  const createEntry = useMutation({
    mutationFn: (data) => timeEntries.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timeEntries'] })
      queryClient.invalidateQueries({ queryKey: ['timeDashboard'] })
      setShowNewEntry(false)
      setNewEntry({ task: '', project: '', description: '', start_time: '', end_time: '', entry_type: 'Regular', is_billable: true, hourly_rate: '' })
    },
  })

  // Timer effect
  useEffect(() => {
    let interval
    if (activeTimer) {
      interval = setInterval(() => {
        const start = new Date(activeTimer.start_time)
        const now = new Date()
        setElapsed(Math.floor((now - start) / 1000))
      }, 1000)
    }
    return () => clearInterval(interval)
  }, [activeTimer])

  const formatDuration = (seconds) => {
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  const formatHours = (hours) => {
    const h = Math.floor(hours)
    const m = Math.round((hours - h) * 60)
    return `${h}س ${m}د`
  }

  const filteredEntries = entries?.results?.filter((entry) => {
    if (filter === 'billable') return entry.is_billable
    if (filter === 'non-billable') return !entry.is_billable
    if (filter === 'today') {
      const entryDate = new Date(entry.start_time).toDateString()
      return entryDate === new Date().toDateString()
    }
    return true
  }) || []

  if (isLoading) {
    return (
      <div className="flex justify-center p-10">
        <div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div>
      </div>
    )
  }

  return (
    <div dir="rtl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">تتبع الوقت</h2>
          <p className="text-gray-500 text-sm">سجل ساعات العمل على المهام والمشاريع</p>
        </div>
        <button
          onClick={() => setShowNewEntry(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus size={18} /> تسجيل يدوي
        </button>
      </div>

      {/* Dashboard Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Clock size={20} className="text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-800">{formatHours(dashboard?.total_hours_this_month || 0)}</p>
              <p className="text-xs text-gray-500">إجمالي الساعات</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <DollarSign size={20} className="text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-800">{formatHours(dashboard?.billable_hours || 0)}</p>
              <p className="text-xs text-gray-500">ساعات قابلة للفوترة</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
              <TrendingUp size={20} className="text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-800">{formatHours(dashboard?.non_billable_hours || 0)}</p>
              <p className="text-xs text-gray-500">ساعات غير قابلة للفوترة</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <BarChart3 size={20} className="text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-800">{dashboard?.total_entries || 0}</p>
              <p className="text-xs text-gray-500">عدد التسجيلات</p>
            </div>
          </div>
        </div>
      </div>

      {/* Active Timer */}
      {activeTimer && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center animate-pulse">
                <Timer size={20} className="text-white" />
              </div>
              <div>
                <p className="font-bold text-blue-800">مؤقت نشط</p>
                <p className="text-sm text-blue-600">{activeTimer.task_subject || activeTimer.project_name || 'مهمة'}</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-3xl font-mono font-bold text-blue-800">{formatDuration(elapsed)}</span>
              <button
                onClick={() => {
                  setActiveTimer(null)
                  setElapsed(0)
                }}
                className="bg-red-500 text-white p-2 rounded-lg hover:bg-red-600"
              >
                <Square size={18} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Entry Modal */}
      {showNewEntry && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">تسجيل وقت جديد</h3>
              <button onClick={() => setShowNewEntry(false)}><X size={20} className="text-gray-400" /></button>
            </div>
            <form onSubmit={(e) => { e.preventDefault(); createEntry.mutate(newEntry) }} className="space-y-3">
              <select
                value={newEntry.task}
                onChange={(e) => setNewEntry({ ...newEntry, task: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                <option value="">اختر مهمة (اختياري)</option>
                {tasksList?.results?.map((t) => (
                  <option key={t.id} value={t.id}>{t.subject}</option>
                ))}
              </select>
              <select
                value={newEntry.project}
                onChange={(e) => setNewEntry({ ...newEntry, project: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                <option value="">اختر مشروع (اختياري)</option>
                {projectsList?.results?.map((p) => (
                  <option key={p.id} value={p.id}>{p.project_name}</option>
                ))}
              </select>
              <textarea
                value={newEntry.description}
                onChange={(e) => setNewEntry({ ...newEntry, description: e.target.value })}
                placeholder="وصف العمل"
                className="w-full border rounded-lg px-3 py-2 text-sm"
                rows={2}
              />
              <div className="flex gap-2">
                <input
                  type="datetime-local"
                  value={newEntry.start_time}
                  onChange={(e) => setNewEntry({ ...newEntry, start_time: e.target.value })}
                  className="flex-1 border rounded-lg px-3 py-2 text-sm"
                />
                <input
                  type="datetime-local"
                  value={newEntry.end_time}
                  onChange={(e) => setNewEntry({ ...newEntry, end_time: e.target.value })}
                  className="flex-1 border rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div className="flex gap-2">
                <select
                  value={newEntry.entry_type}
                  onChange={(e) => setNewEntry({ ...newEntry, entry_type: e.target.value })}
                  className="flex-1 border rounded-lg px-3 py-2 text-sm"
                >
                  <option value="Regular">عادي</option>
                  <option value="Overtime">إضافي</option>
                  <option value="Billable">قابل للفوترة</option>
                  <option value="Non-Billable">غير قابل للفوترة</option>
                </select>
                <input
                  type="number"
                  step="0.01"
                  value={newEntry.hourly_rate}
                  onChange={(e) => setNewEntry({ ...newEntry, hourly_rate: e.target.value })}
                  placeholder="السعر/ساعة"
                  className="flex-1 border rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={newEntry.is_billable}
                  onChange={(e) => setNewEntry({ ...newEntry, is_billable: e.target.checked })}
                  className="rounded"
                />
                قابل للفوترة
              </label>
              <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">
                حفظ
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Filter */}
      <div className="flex items-center gap-2 mb-4">
        <Filter size={16} className="text-gray-400" />
        <button
          onClick={() => setFilter('all')}
          className={`text-xs px-3 py-1.5 rounded-lg ${filter === 'all' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}`}
        >
          الكل
        </button>
        <button
          onClick={() => setFilter('today')}
          className={`text-xs px-3 py-1.5 rounded-lg ${filter === 'today' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}`}
        >
          اليوم
        </button>
        <button
          onClick={() => setFilter('billable')}
          className={`text-xs px-3 py-1.5 rounded-lg ${filter === 'billable' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}
        >
          قابل للفوترة
        </button>
        <button
          onClick={() => setFilter('non-billable')}
          className={`text-xs px-3 py-1.5 rounded-lg ${filter === 'non-billable' ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-600'}`}
        >
          غير قابل للفوترة
        </button>
      </div>

      {/* Entries List */}
      <div className="bg-white rounded-xl shadow-sm border divide-y">
        {filteredEntries.map((entry) => (
          <div key={entry.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${entry.is_billable ? 'bg-green-100' : 'bg-gray-100'}`}>
                <Clock size={18} className={entry.is_billable ? 'text-green-600' : 'text-gray-500'} />
              </div>
              <div>
                <p className="font-medium text-gray-800 text-sm">{entry.description || 'بدون وصف'}</p>
                <div className="flex items-center gap-2 text-xs text-gray-400 mt-0.5">
                  {entry.task_subject && <span className="text-blue-600">{entry.task_subject}</span>}
                  {entry.project_name && <span className="text-purple-600">{entry.project_name}</span>}
                  <span>{new Date(entry.start_time).toLocaleDateString('ar-SA')}</span>
                </div>
              </div>
            </div>
            <div className="text-right">
              <p className="font-bold text-gray-800">{formatHours(entry.duration_hours || 0)}</p>
              <p className="text-xs text-gray-400">
                {entry.entry_type === 'Overtime' ? 'إضافي' : entry.is_billable ? 'قابل للفوترة' : 'غير قابل للفوترة'}
              </p>
            </div>
          </div>
        ))}
        {filteredEntries.length === 0 && (
          <p className="text-gray-400 text-center py-10">لا توجد تسجيلات</p>
        )}
      </div>
    </div>
  )
}
