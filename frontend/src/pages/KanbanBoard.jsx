import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
import { projects, tasks, taskApi } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import {
  ArrowLeft, Clock, MessageSquare, GripVertical, Plus, X,
  AlertCircle, CheckCircle2, Circle, Timer, ChevronRight
} from 'lucide-react'

const STATUS_CONFIG = {
  'Open': { label: 'لم تبدأ', color: 'bg-gray-100 border-gray-200', icon: Circle, textColor: 'text-gray-600' },
  'Working': { label: 'قيد التنفيذ', color: 'bg-blue-50 border-blue-200', icon: Timer, textColor: 'text-blue-600' },
  'Pending Review': { label: 'بانتظار المراجعة', color: 'bg-yellow-50 border-yellow-200', icon: AlertCircle, textColor: 'text-yellow-600' },
  'Completed': { label: 'مكتملة', color: 'bg-green-50 border-green-200', icon: CheckCircle2, textColor: 'text-green-600' },
  'Cancelled': { label: 'ملغاة', color: 'bg-red-50 border-red-200', icon: X, textColor: 'text-red-600' },
}

const PRIORITY_COLORS = {
  'Low': 'bg-gray-200 text-gray-700',
  'Medium': 'bg-blue-100 text-blue-700',
  'High': 'bg-orange-100 text-orange-700',
  'Urgent': 'bg-red-100 text-red-700',
}

export default function KanbanBoard() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [draggingTask, setDraggingTask] = useState(null)
  const [showNewTask, setShowNewTask] = useState(false)
  const [newTask, setNewTask] = useState({ subject: '', priority: 'Medium', expected_end: '' })

  const { data: project } = useQuery({
    queryKey: ['project', id],
    queryFn: () => projects.get(id),
  })

  const { data: kanbanData, isLoading } = useQuery({
    queryKey: ['kanban', id],
    queryFn: () => projectApi.kanban(id),
    enabled: !!id,
  })

  const updateStatus = useMutation({
    mutationFn: ({ taskId, status }) => tasks.update(taskId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kanban', id] })
      queryClient.invalidateQueries({ queryKey: ['project', id] })
    },
  })

  const createTask = useMutation({
    mutationFn: (data) => tasks.create({ ...data, project: id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kanban', id] })
      setShowNewTask(false)
      setNewTask({ subject: '', priority: 'Medium', expected_end: '' })
    },
  })

  const handleDragStart = (task) => {
    setDraggingTask(task)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const handleDrop = (e, status) => {
    e.preventDefault()
    if (draggingTask && draggingTask.status !== status) {
      updateStatus.mutate({ taskId: draggingTask.id, status })
      setDraggingTask(null)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center p-10">
        <div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div>
      </div>
    )
  }

  return (
    <div dir="rtl" className="h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/projects')} className="p-2 hover:bg-gray-100 rounded-lg">
            <ArrowLeft size={20} className="text-gray-500" />
          </button>
          <div>
            <h2 className="text-2xl font-bold text-gray-800">لوحة Kanban</h2>
            <p className="text-gray-500 text-sm">{project?.project_name}</p>
          </div>
        </div>
        <button
          onClick={() => setShowNewTask(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus size={18} /> مهمة جديدة
        </button>
      </div>

      {/* New Task Modal */}
      {showNewTask && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold">مهمة جديدة</h3>
              <button onClick={() => setShowNewTask(false)}><X size={20} className="text-gray-400" /></button>
            </div>
            <form onSubmit={(e) => { e.preventDefault(); createTask.mutate(newTask) }} className="space-y-3">
              <input
                required
                value={newTask.subject}
                onChange={(e) => setNewTask({ ...newTask, subject: e.target.value })}
                placeholder="عنوان المهمة"
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
              <select
                value={newTask.priority}
                onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                <option value="Low">منخفضة</option>
                <option value="Medium">متوسطة</option>
                <option value="High">عالية</option>
                <option value="Urgent">عاجلة</option>
              </select>
              <input
                type="date"
                value={newTask.expected_end}
                onChange={(e) => setNewTask({ ...newTask, expected_end: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
              <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">
                إنشاء
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Kanban Columns */}
      <div className="flex gap-4 overflow-x-auto pb-4" style={{ minHeight: 'calc(100vh - 200px)' }}>
        {Object.entries(STATUS_CONFIG).map(([status, config]) => {
          const Icon = config.icon
          const columnTasks = kanbanData?.[status] || []
          return (
            <div
              key={status}
              className={`flex-shrink-0 w-72 rounded-xl border ${config.color} p-3`}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, status)}
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`flex items-center gap-2 ${config.textColor}`}>
                  <Icon size={16} />
                  <span className="font-bold text-sm">{config.label}</span>
                </div>
                <span className="bg-white text-xs font-medium px-2 py-0.5 rounded-full">
                  {columnTasks.length}
                </span>
              </div>

              <div className="space-y-2">
                {columnTasks.map((task) => (
                  <div
                    key={task.id}
                    draggable
                    onDragStart={() => handleDragStart({ ...task, status })}
                    className="bg-white rounded-lg p-3 shadow-sm border cursor-move hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <p className="text-sm font-medium text-gray-800 flex-1">{task.subject}</p>
                      <GripVertical size={14} className="text-gray-300" />
                    </div>

                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${PRIORITY_COLORS[task.priority]}`}>
                        {task.priority === 'Low' ? 'منخفض' : task.priority === 'Medium' ? 'متوسط' : task.priority === 'High' ? 'عالي' : 'عاجل'}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs text-gray-400">
                      <div className="flex items-center gap-3">
                        {task.assignee && (
                          <span className="flex items-center gap-1">
                            <div className="w-5 h-5 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-[10px] font-bold">
                              {task.assignee.charAt(0)}
                            </div>
                          </span>
                        )}
                        {task.comments_count > 0 && (
                          <span className="flex items-center gap-1">
                            <MessageSquare size={12} /> {task.comments_count}
                          </span>
                        )}
                        {task.total_hours > 0 && (
                          <span className="flex items-center gap-1">
                            <Clock size={12} /> {task.total_hours}h
                          </span>
                        )}
                      </div>
                      {task.expected_end && (
                        <span className={new Date(task.expected_end) < new Date() ? 'text-red-500' : ''}>
                          {new Date(task.expected_end).toLocaleDateString('ar-SA')}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
