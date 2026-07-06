import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { salesOrders, salesOrderItems, customers, warehouses, items as itemsApi } from '../lib/api'
import { Plus, X, Package, CheckCircle2, Truck } from 'lucide-react'

const STATUS_STYLES = {
  Draft: 'bg-yellow-100 text-yellow-700',
  Submitted: 'bg-blue-100 text-blue-700',
  Delivered: 'bg-green-100 text-green-700',
  Cancelled: 'bg-gray-100 text-gray-500',
}

function apiErrorMessage(err) {
  const data = err?.response?.data
  if (!data) return 'حدث خطأ غير متوقع.'
  if (Array.isArray(data)) return data.join(' ')
  if (typeof data === 'string') return data
  return Object.values(data).flat().join(' ')
}

function NewSOModal({ onClose }) {
  const queryClient = useQueryClient()
  const { data: customerData } = useQuery({ queryKey: ['customers'], queryFn: () => customers.list() })
  const { data: warehouseData } = useQuery({ queryKey: ['warehouses'], queryFn: () => warehouses.list() })
  const [form, setForm] = useState({ so_number: '', customer: '', warehouse: '', transaction_date: new Date().toISOString().slice(0, 10) })
  const [error, setError] = useState('')

  const createMutation = useMutation({
    mutationFn: (data) => salesOrders.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['salesOrders'] })
      onClose()
    },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-gray-800">أمر بيع جديد</h3>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>
        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}
        <form
          onSubmit={(e) => { e.preventDefault(); createMutation.mutate({ ...form, company: customerData?.results?.[0]?.company }) }}
          className="space-y-3"
        >
          <div>
            <label className="block text-sm text-gray-600 mb-1">رقم الأمر</label>
            <input required value={form.so_number} onChange={(e) => setForm({ ...form, so_number: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="SO-2026-001" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">العميل</label>
            <select required value={form.customer} onChange={(e) => setForm({ ...form, customer: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm">
              <option value="">اختر عميل</option>
              {customerData?.results?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">المستودع</label>
            <select value={form.warehouse} onChange={(e) => setForm({ ...form, warehouse: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm">
              <option value="">بدون تحديد الآن</option>
              {warehouseData?.results?.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
            <p className="text-xs text-gray-400 mt-1">لازم تحدد مستودع قبل ما تعمل "تسليم" للأمر.</p>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">تاريخ الأمر</label>
            <input type="date" required value={form.transaction_date}
              onChange={(e) => setForm({ ...form, transaction_date: e.target.value })}
              className="w-full border rounded-lg px-3 py-2 text-sm" />
          </div>
          <button type="submit" disabled={createMutation.isPending}
            className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50">
            {createMutation.isPending ? 'جارِ الإنشاء...' : 'إنشاء الأمر'}
          </button>
        </form>
      </div>
    </div>
  )
}

function SOPanel({ so, onClose }) {
  const queryClient = useQueryClient()
  const { data: itemLines } = useQuery({
    queryKey: ['so-items', so.id],
    queryFn: () => salesOrderItems.list({ sales_order: so.id }),
  })
  const { data: itemsData } = useQuery({ queryKey: ['items'], queryFn: () => itemsApi.list() })
  const [lineForm, setLineForm] = useState({ item: '', qty: '', rate: '' })
  const [error, setError] = useState('')

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['so-items', so.id] })
    queryClient.invalidateQueries({ queryKey: ['salesOrders'] })
    queryClient.invalidateQueries({ queryKey: ['items'] })
  }

  const addLine = useMutation({
    mutationFn: (data) => salesOrderItems.create({ ...data, sales_order: so.id }),
    onSuccess: () => { invalidate(); setLineForm({ item: '', qty: '', rate: '' }); setError('') },
    onError: (err) => setError(apiErrorMessage(err)),
  })

  const transition = useMutation({
    mutationFn: (status) => salesOrders.update(so.id, { status }),
    onSuccess: invalidate,
    onError: (err) => setError(apiErrorMessage(err)),
  })

  const isDraft = so.status === 'Draft'
  const isSubmitted = so.status === 'Submitted'

  const stockFor = (itemId) => itemsData?.results?.find((i) => i.id === itemId)?.stock_quantity

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg font-bold text-gray-800">{so.so_number}</h3>
            <span className={`inline-block mt-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[so.status]}`}>{so.status}</span>
          </div>
          <button onClick={onClose}><X size={20} className="text-gray-400" /></button>
        </div>

        {error && <div className="bg-red-50 text-red-700 text-sm px-3 py-2 rounded-lg mb-3 border border-red-200">{error}</div>}

        <div className="grid grid-cols-3 gap-3 text-sm mb-4 bg-gray-50 rounded-lg p-3">
          <div><span className="text-gray-400">الكمية</span><div className="font-semibold">{so.total_qty}</div></div>
          <div><span className="text-gray-400">الإجمالي</span><div className="font-semibold">{so.total_amount} {so.currency}</div></div>
          <div><span className="text-gray-400">الصافي</span><div className="font-semibold">{so.grand_total} {so.currency}</div></div>
        </div>

        <h4 className="font-semibold text-gray-700 mb-2 flex items-center gap-2"><Package size={16} /> الأصناف</h4>
        <table className="w-full text-sm mb-3">
          <thead>
            <tr className="text-gray-400 text-xs">
              <th className="text-right py-1">الصنف</th>
              <th className="text-right py-1">الكمية</th>
              <th className="text-right py-1">السعر</th>
              <th className="text-right py-1">الإجمالي</th>
              <th className="text-right py-1">المتاح بالمخزون</th>
            </tr>
          </thead>
          <tbody>
            {itemLines?.results?.map((line) => (
              <tr key={line.id} className="border-t">
                <td className="py-2">{itemsData?.results?.find((i) => i.id === line.item)?.item_name || line.item}</td>
                <td className="py-2">{line.qty}</td>
                <td className="py-2">{line.rate}</td>
                <td className="py-2 font-medium">{line.amount}</td>
                <td className={`py-2 ${stockFor(line.item) < line.qty ? 'text-red-600 font-semibold' : 'text-gray-500'}`}>
                  {stockFor(line.item)}
                </td>
              </tr>
            ))}
            {!itemLines?.results?.length && (
              <tr><td colSpan={5} className="text-center text-gray-400 py-4">لا يوجد أصناف بعد</td></tr>
            )}
          </tbody>
        </table>

        {isDraft && (
          <form
            onSubmit={(e) => { e.preventDefault(); addLine.mutate({ item: lineForm.item, qty: lineForm.qty, rate: lineForm.rate }) }}
            className="flex gap-2 mb-4"
          >
            <select required value={lineForm.item} onChange={(e) => setLineForm({ ...lineForm, item: e.target.value })}
              className="flex-1 border rounded-lg px-2 py-1.5 text-sm">
              <option value="">اختر صنف</option>
              {itemsData?.results?.map((i) => <option key={i.id} value={i.id}>{i.item_name} (متاح: {i.stock_quantity})</option>)}
            </select>
            <input required type="number" step="0.01" placeholder="الكمية" value={lineForm.qty}
              onChange={(e) => setLineForm({ ...lineForm, qty: e.target.value })}
              className="w-24 border rounded-lg px-2 py-1.5 text-sm" />
            <input required type="number" step="0.01" placeholder="السعر" value={lineForm.rate}
              onChange={(e) => setLineForm({ ...lineForm, rate: e.target.value })}
              className="w-24 border rounded-lg px-2 py-1.5 text-sm" />
            <button type="submit" className="bg-blue-600 text-white px-3 rounded-lg text-sm hover:bg-blue-700">إضافة</button>
          </form>
        )}

        <div className="flex gap-2 justify-end pt-3 border-t">
          {isDraft && (
            <button onClick={() => transition.mutate('Submitted')}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
              <CheckCircle2 size={16} /> اعتماد الأمر
            </button>
          )}
          {isSubmitted && (
            <button onClick={() => transition.mutate('Delivered')}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-700">
              <Truck size={16} /> تأكيد التسليم (ينقص المخزون)
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default function SalesOrders() {
  const { data, isLoading } = useQuery({ queryKey: ['salesOrders'], queryFn: () => salesOrders.list() })
  const { data: customerData } = useQuery({ queryKey: ['customers'], queryFn: () => customers.list() })
  const [showNew, setShowNew] = useState(false)
  const [selectedSO, setSelectedSO] = useState(null)

  const customerName = (id) => customerData?.results?.find((c) => c.id === id)?.name || id

  if (isLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>

  return (
    <div dir="rtl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">أوامر البيع</h2>
          <p className="text-gray-500 text-sm">إدارة أوامر البيع للعملاء ومتابعة التسليم</p>
        </div>
        <button onClick={() => setShowNew(true)} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> أمر بيع جديد
        </button>
      </div>
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">رقم الأمر</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">العميل</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">التاريخ</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">الإجمالي</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">الحالة</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data?.results?.map((so) => (
              <tr key={so.id} onClick={() => setSelectedSO(so)} className="hover:bg-gray-50 cursor-pointer">
                <td className="px-6 py-4 font-medium text-blue-600">{so.so_number}</td>
                <td className="px-6 py-4 text-gray-700">{customerName(so.customer)}</td>
                <td className="px-6 py-4 text-gray-600 text-sm">{so.transaction_date}</td>
                <td className="px-6 py-4 font-medium">{so.grand_total} {so.currency}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_STYLES[so.status] || 'bg-gray-100 text-gray-700'}`}>{so.status}</span>
                </td>
              </tr>
            ))}
            {!data?.results?.length && (
              <tr><td colSpan={5} className="text-center text-gray-400 py-8">لا يوجد أوامر بيع بعد</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {showNew && <NewSOModal onClose={() => setShowNew(false)} />}
      {selectedSO && <SOPanel so={selectedSO} onClose={() => setSelectedSO(null)} />}
    </div>
  )
}
