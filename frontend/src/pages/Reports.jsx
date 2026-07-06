import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { purchaseOrders, salesOrders, tasks, risks } from '../lib/api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid } from 'recharts'
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react'

const STATUS_COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6']

function KpiCard({ title, value, icon: Icon, color }) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm text-gray-500 mb-1">{title}</p>
          <h3 className="text-2xl font-bold text-gray-800">{value}</h3>
        </div>
        <div className={`p-2.5 rounded-lg ${color}`}>
          <Icon size={18} className="text-white" />
        </div>
      </div>
    </div>
  )
}

export default function Reports() {
  const { data: poData } = useQuery({ queryKey: ['purchaseOrders'], queryFn: () => purchaseOrders.list() })
  const { data: soData } = useQuery({ queryKey: ['salesOrders'], queryFn: () => salesOrders.list() })
  const { data: taskData } = useQuery({ queryKey: ['tasks'], queryFn: () => tasks.list() })
  const { data: riskData } = useQuery({ queryKey: ['risks'], queryFn: () => risks.list() })

  const totalPurchases = poData?.results?.reduce((sum, po) => sum + Number(po.grand_total || 0), 0) || 0
  const totalSales = soData?.results?.reduce((sum, so) => sum + Number(so.grand_total || 0), 0) || 0
  const netMargin = totalSales - totalPurchases

  const poByStatus = Object.entries(
    (poData?.results || []).reduce((acc, po) => { acc[po.status] = (acc[po.status] || 0) + 1; return acc }, {})
  ).map(([status, count]) => ({ status, count }))

  const soByStatus = Object.entries(
    (soData?.results || []).reduce((acc, so) => { acc[so.status] = (acc[so.status] || 0) + 1; return acc }, {})
  ).map(([status, count]) => ({ status, count }))

  const taskByStatus = Object.entries(
    (taskData?.results || []).reduce((acc, t) => { acc[t.status] = (acc[t.status] || 0) + 1; return acc }, {})
  ).map(([name, value]) => ({ name, value }))

  const riskByLevel = Object.entries(
    (riskData?.results || []).reduce((acc, r) => { acc[r.risk_level] = (acc[r.risk_level] || 0) + 1; return acc }, {})
  ).map(([name, value]) => ({ name, value }))

  return (
    <div dir="rtl">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">التقارير</h2>
        <p className="text-gray-500 text-sm">أرقام حية من بيانات النظام الفعلية</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <KpiCard title="إجمالي المشتريات" value={`${totalPurchases.toLocaleString()} SAR`} icon={TrendingDown} color="bg-red-500" />
        <KpiCard title="إجمالي المبيعات" value={`${totalSales.toLocaleString()} SAR`} icon={TrendingUp} color="bg-green-500" />
        <KpiCard title="الهامش الصافي" value={`${netMargin.toLocaleString()} SAR`} icon={DollarSign} color={netMargin >= 0 ? 'bg-blue-500' : 'bg-orange-500'} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="bg-white rounded-xl shadow-sm border p-5">
          <h3 className="font-semibold text-gray-700 mb-4">أوامر الشراء حسب الحالة</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={poByStatus}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="status" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow-sm border p-5">
          <h3 className="font-semibold text-gray-700 mb-4">أوامر البيع حسب الحالة</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={soByStatus}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="status" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow-sm border p-5">
          <h3 className="font-semibold text-gray-700 mb-4">توزيع حالة المهام</h3>
          {taskByStatus.length ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={taskByStatus} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {taskByStatus.map((entry, i) => <Cell key={i} fill={STATUS_COLORS[i % STATUS_COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-gray-400 text-center py-16 text-sm">لا يوجد مهام بعد</p>}
        </div>

        <div className="bg-white rounded-xl shadow-sm border p-5">
          <h3 className="font-semibold text-gray-700 mb-4">توزيع مستوى المخاطر</h3>
          {riskByLevel.length ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={riskByLevel} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {riskByLevel.map((entry, i) => <Cell key={i} fill={['#ef4444', '#f59e0b', '#eab308', '#10b981'][i % 4]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-gray-400 text-center py-16 text-sm">لا يوجد مخاطر مسجلة بعد</p>}
        </div>
      </div>
    </div>
  )
}
