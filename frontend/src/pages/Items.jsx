import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { items as itemsApi } from '../lib/api'
import { Plus, X, Package, AlertTriangle } from 'lucide-react'

function apiErrorMessage(err) {
  const data = err?.response?.data
  if (!data) return 'حدث خطأ غير متوقع.'
  if (Array.isArray(data)) return data.join(' ')
  if (typeof data === 'string') return data
  return Object.values(data).flat().join(' ')
}

function NewItemModal({ onClose }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({ item_code: '', item_name: '', standard_rate: '', reorder_level: '' })
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => itemsApi.create(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['items'] }); onClose() },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">صنف جديد</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="space-y-3">
          <div>
            <label className="block text-sm text-gray-600 mb-1">كود الصنف</label>
            <input required value={form.item_code} onChange={(e) => setForm({ ...form, item_code: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="ITM-001" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">اسم الصنف</label>
            <input required value={form.item_name} onChange={(e) => setForm({ ...form, item_name: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">السعر القياسي</label>
            <input type="number" step="0.01" value={form.standard_rate} onChange={(e) => setForm({ ...form, standard_rate: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">حد إعادة الطلب</label>
            <input type="number" step="0.01" value={form.reorder_level} onChange={(e) => setForm({ ...form, reorder_level: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <button type="submit" disabled={createMutation.isPending}
            className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50">
            {createMutation.isPending ? 'جارِ الإنشاء...' : 'إنشاء الصنف'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default function Items() {
  const { data, isLoading } = useQuery({ queryKey: ['items'], queryFn: () => itemsApi.list() })
  const [showNew, setShowNew] = useState(false)

  if (isLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>

  return (
    <div dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">المخزون</h2>
          <p className="text-gray-500 text-sm">رصيد المخزون محسوب حي من كل حركات الاستلام والصرف</p>
        </div>
        <button onClick={() => setShowNew(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> صنف جديد
        </button>
      </div>
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">الكود</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">الاسم</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">السعر</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">الرصيد الحالي</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">حد إعادة الطلب</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data?.results?.map((item) => {
              const low = item.reorder_level && Number(item.stock_quantity) <= Number(item.reorder_level)
              return (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-blue-600 flex items-center gap-2">
                    <Package size={16} className="text-gray-400" /> {item.item_code}
                  </td>
                  <td className="px-6 py-4 text-gray-700">{item.item_name}</td>
                  <td className="px-6 py-4 text-gray-600">{item.standard_rate}</td>
                  <td className="px-6 py-4">
                    <span className={`font-semibold ${low ? 'text-red-600' : 'text-gray-800'}`}>{item.stock_quantity}</span>
                    {low && (
                      <span className="inline-flex items-center gap-1 text-xs text-red-600 mr-2">
                        <AlertTriangle size={12} /> منخفض
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-gray-500">{item.reorder_level}</td>
                </tr>
              )
            })}
            {!data?.results?.length && (
              <tr><td colSpan={5} className="text-center text-gray-400 py-8">لا يوجد أصناف بعد</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {showNew && <NewItemModal onClose={() => setShowNew(false)} />}
    </div>
  )
}
