import React, { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { projects, tasks, api } from '../lib/api'
import {
  Brain, Sparkles, AlertTriangle, TrendingUp, Users, Clock,
  ChevronDown, ChevronUp, Loader2, Send, BarChart3, Target
} from 'lucide-react'

const AI_ENDPOINTS = {
  analyze_risks: '/ai-assistant/analyze_risks/',
  suggest_assignment: '/ai-assistant/suggest_task_assignment/',
  predict_delay: '/ai-assistant/predict_delay/',
  status_report: '/ai-assistant/generate_status_report/',
}

export default function AIAssistant() {
  const [selectedProject, setSelectedProject] = useState('')
  const [selectedTask, setSelectedTask] = useState('')
  const [activeTab, setActiveTab] = useState('risks')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const { data: projectsList } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projects.list(),
  })

  const { data: tasksList } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasks.list(),
    enabled: !!selectedProject,
  })

  const projectTasks = tasksList?.results?.filter(t => t.project === parseInt(selectedProject)) || []

  const runAnalysis = async (endpoint, data) => {
    setLoading(true)
    try {
      const response = await api.post(endpoint, data)
      setResult(response.data)
    } catch (err) {
      setResult({ error: err.response?.data?.error || 'حدث خطأ' })
    }
    setLoading(false)
  }

  const tabs = [
    { key: 'risks', label: 'تحليل المخاطر', icon: AlertTriangle },
    { key: 'assignment', label: 'توزيع المهام', icon: Users },
    { key: 'delay', label: 'توقع التأخير', icon: Clock },
    { key: 'report', label: 'تقرير الحالة', icon: BarChart3 },
  ]

  const renderResult = () => {
    if (!result) return null
    if (result.error) return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
        {result.error}
      </div>
    )

    switch (activeTab) {
      case 'risks':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-4 gap-3">
              <div className="bg-white rounded-lg p-3 border text-center">
                <p className="text-2xl font-bold text-gray-800">{result.risk_summary?.total_risks}</p>
                <p className="text-xs text-gray-500">إجمالي المخاطر</p>
              </div>
              <div className="bg-red-50 rounded-lg p-3 border border-red-200 text-center">
                <p className="text-2xl font-bold text-red-600">{result.risk_summary?.high_risks}</p>
                <p className="text-xs text-red-500">مخاطر عالية</p>
              </div>
              <div className="bg-orange-50 rounded-lg p-3 border border-orange-200 text-center">
                <p className="text-2xl font-bold text-orange-600">{result.risk_summary?.medium_risks}</p>
                <p className="text-xs text-orange-500">مخاطر متوسطة</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-3 border border-blue-200 text-center">
                <p className="text-2xl font-bold text-blue-600">{result.health_score}</p>
                <p className="text-xs text-blue-500">درجة الصحة</p>
              </div>
            </div>
            {result.recommendations?.map((rec, i) => (
              <div key={i} className={`rounded-lg p-4 border ${
                rec.severity === 'high' ? 'bg-red-50 border-red-200' :
                rec.severity === 'medium' ? 'bg-orange-50 border-orange-200' :
                'bg-blue-50 border-blue-200'
              }`}>
                <div className="flex items-start gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    rec.severity === 'high' ? 'bg-red-100' :
                    rec.severity === 'medium' ? 'bg-orange-100' :
                    'bg-blue-100'
                  }`}>
                    <AlertTriangle size={16} className={
                      rec.severity === 'high' ? 'text-red-600' :
                      rec.severity === 'medium' ? 'text-orange-600' :
                      'text-blue-600'
                    } />
                  </div>
                  <div>
                    <p className="font-medium text-gray-800">{rec.message}</p>
                    <p className="text-sm text-gray-500 mt-1">💡 {rec.action}</p>
                    {rec.affected && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {rec.affected.map((a, j) => (
                          <span key={j} className="text-xs bg-white px-2 py-1 rounded border">
                            {a.name} ({a.active_tasks} مهام)
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )

      case 'assignment':
        return (
          <div className="space-y-4">
            <p className="text-sm text-gray-500">أفضل الموظفين لتعيينهم على مهمة: <strong>{result.task}</strong></p>
            {result.top_suggestions?.map((s, i) => (
              <div key={i} className={`flex items-center justify-between p-3 rounded-lg border ${
                i === 0 ? 'bg-green-50 border-green-200' : 'bg-white'
              }`}>
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold ${
                    i === 0 ? 'bg-green-500' : 'bg-gray-400'
                  }`}>
                    {i + 1}
                  </div>
                  <div>
                    <p className="font-medium text-gray-800">{s.name}</p>
                    <p className="text-xs text-gray-500">{s.active_tasks} مهام نشطة | {s.completed_in_project} مكتملة في المشروع</p>
                    {s.reason && <p className="text-xs text-blue-600 mt-0.5">{s.reason}</p>}
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-gray-800">{s.suitability_score}</p>
                  <p className="text-xs text-gray-400">درجة التناسب</p>
                </div>
              </div>
            ))}
          </div>
        )

      case 'delay':
        return (
          <div className="space-y-4">
            <div className={`p-4 rounded-xl border ${result.on_track ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${result.on_track ? 'bg-green-100' : 'bg-red-100'}`}>
                  <Clock size={24} className={result.on_track ? 'text-green-600' : 'text-red-600'} />
                </div>
                <div>
                  <p className={`text-lg font-bold ${result.on_track ? 'text-green-800' : 'text-red-800'}`}>
                    {result.on_track ? 'المشروع في المسار الصحيح ✅' : `متوقع تأخير ${result.delay_days} يوم ⚠️`}
                  </p>
                  <p className="text-sm text-gray-500">
                    السرعة: {result.velocity} مهمة/يوم | المتبقي: {result.tasks_remaining} مهمة
                  </p>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white rounded-lg p-3 border">
                <p className="text-xs text-gray-500">تاريخ الانتهاء المتوقع</p>
                <p className="font-bold text-gray-800">{new Date(result.predicted_end).toLocaleDateString('ar-SA')}</p>
              </div>
              <div className="bg-white rounded-lg p-3 border">
                <p className="text-xs text-gray-500">تاريخ الانتهاء المخطط</p>
                <p className="font-bold text-gray-800">{result.expected_end ? new Date(result.expected_end).toLocaleDateString('ar-SA') : 'غير محدد'}</p>
              </div>
            </div>
          </div>
        )

      case 'report':
        return (
          <div className="space-y-4">
            <div className="bg-white rounded-xl p-4 border">
              <h4 className="font-bold text-gray-800 mb-2">ملخص تنفيذي</h4>
              <p className="text-sm text-gray-600 whitespace-pre-line">{result.executive_summary}</p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-blue-50 rounded-lg p-3 border border-blue-200 text-center">
                <p className="text-xl font-bold text-blue-700">{result.key_metrics?.total_tasks}</p>
                <p className="text-xs text-blue-600">إجمالي المهام</p>
              </div>
              <div className="bg-green-50 rounded-lg p-3 border border-green-200 text-center">
                <p className="text-xl font-bold text-green-700">{result.key_metrics?.completed}</p>
                <p className="text-xs text-green-600">مكتملة</p>
              </div>
              <div className="bg-orange-50 rounded-lg p-3 border border-orange-200 text-center">
                <p className="text-xl font-bold text-orange-700">{result.key_metrics?.overdue}</p>
                <p className="text-xs text-orange-600">متأخرة</p>
              </div>
              <div className="bg-purple-50 rounded-lg p-3 border border-purple-200 text-center">
                <p className="text-xl font-bold text-purple-700">{result.key_metrics?.budget_used_pct}%</p>
                <p className="text-xs text-purple-600">الميزانية المستخدمة</p>
              </div>
            </div>

            <div className="bg-white rounded-xl p-4 border">
              <h4 className="font-bold text-gray-800 mb-2">الرؤى والملاحظات</h4>
              <ul className="space-y-2">
                {result.insights?.map((insight, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                    <Sparkles size={16} className="text-amber-500 flex-shrink-0 mt-0.5" />
                    {insight}
                  </li>
                ))}
              </ul>
            </div>

            {result.recommendations?.length > 0 && (
              <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
                <h4 className="font-bold text-amber-800 mb-2">التوصيات</h4>
                <ul className="space-y-2">
                  {result.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-amber-700">
                      <Target size={16} className="flex-shrink-0 mt-0.5" />
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div dir="rtl">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
          <Brain size={24} className="text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-800">مساعد المشاريع الذكي</h2>
          <p className="text-gray-500 text-sm">تحليل ذكي للمشاريع بدون الحاجة لـ API خارجي</p>
        </div>
      </div>

      {/* Project Selection */}
      <div className="bg-white rounded-xl p-4 border mb-6">
        <div className="flex flex-wrap gap-3">
          <select
            value={selectedProject}
            onChange={(e) => { setSelectedProject(e.target.value); setSelectedTask(''); setResult(null); }}
            className="border rounded-lg px-3 py-2 text-sm min-w-[200px]"
          >
            <option value="">اختر مشروع...</option>
            {projectsList?.results?.map((p) => (
              <option key={p.id} value={p.id}>{p.project_name}</option>
            ))}
          </select>

          {activeTab === 'assignment' && (
            <select
              value={selectedTask}
              onChange={(e) => setSelectedTask(e.target.value)}
              className="border rounded-lg px-3 py-2 text-sm min-w-[200px]"
            >
              <option value="">اختر مهمة...</option>
              {projectTasks.map((t) => (
                <option key={t.id} value={t.id}>{t.subject}</option>
              ))}
            </select>
          )}

          <button
            onClick={() => {
              if (!selectedProject) return
              const data = activeTab === 'assignment' ? { task_id: selectedTask } : { project_id: selectedProject }
              runAnalysis(AI_ENDPOINTS[activeTab], data)
            }}
            disabled={!selectedProject || (activeTab === 'assignment' && !selectedTask) || loading}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}
            تحليل
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.key}
              onClick={() => { setActiveTab(tab.key); setResult(null); }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap ${
                activeTab === tab.key
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 border hover:bg-gray-50'
              }`}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Results */}
      {renderResult()}
    </div>
  )
}
