import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchPurchaseOrders, fetchSalesOrders, fetchItems, fetchEmployees } from '../lib/api'
import { TrendingUp, TrendingDown, DollarSign, Package, Users, ShoppingCart } from 'lucide-react'

function StatCard({ title, value, icon: Icon, trend, color }) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm text-gray-500 mb-1">{title}</p>
          <h3 className="text-2xl font-bold text-gray-800">{value}</h3>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon size={20} className="text-white" />
        </div>
      </div>
      {trend && (
        <div className="flex items-center gap-1 mt-4">
          {trend > 0 ? <TrendingUp size={16} className="text-green-500" /> : <TrendingDown size={16} className="text-red-500" />}
          <span className={`text-sm ${trend > 0 ? 'text-green-500' : 'text-red-500'}`}>{Math.abs(trend)}%</span>
          <span className="text-sm text-gray-400">vs last month</span>
        </div>
      )}
    </div>
  )
}

export default function Dashboard() {
  const { data: poData } = useQuery({ queryKey: ['purchaseOrders'], queryFn: fetchPurchaseOrders })
  const { data: soData } = useQuery({ queryKey: ['salesOrders'], queryFn: fetchSalesOrders })
  const { data: itemsData } = useQuery({ queryKey: ['items'], queryFn: fetchItems })
  const { data: empData } = useQuery({ queryKey: ['employees'], queryFn: fetchEmployees })

  const poCount = poData?.results?.length || poData?.count || 0
  const soCount = soData?.results?.length || soData?.count || 0
  const itemCount = itemsData?.results?.length || itemsData?.count || 0
  const empCount = empData?.results?.length || empData?.count || 0

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard title="Total Sales Orders" value={soCount} icon={ShoppingCart} trend={12} color="bg-blue-500" />
        <StatCard title="Purchase Orders" value={poCount} icon={DollarSign} trend={-5} color="bg-green-500" />
        <StatCard title="Inventory Items" value={itemCount} icon={Package} trend={8} color="bg-purple-500" />
        <StatCard title="Employees" value={empCount} icon={Users} trend={3} color="bg-orange-500" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Purchase Orders</h3>
          <div className="space-y-3">
            {(poData?.results || []).slice(0, 5).map((po) => (
              <div key={po.id} className="flex justify-between items-center py-2 border-b last:border-0">
                <div>
                  <p className="font-medium text-gray-800">{po.po_number}</p>
                  <p className="text-sm text-gray-500">{po.supplier_name || po.supplier}</p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  po.status === 'Submitted' ? 'bg-green-100 text-green-700' :
                  po.status === 'Draft' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-700'
                }`}>{po.status}</span>
              </div>
            ))}
            {(!poData?.results || poData.results.length === 0) && (
              <p className="text-gray-400 text-sm text-center py-4">No purchase orders yet</p>
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Sales Orders</h3>
          <div className="space-y-3">
            {(soData?.results || []).slice(0, 5).map((so) => (
              <div key={so.id} className="flex justify-between items-center py-2 border-b last:border-0">
                <div>
                  <p className="font-medium text-gray-800">{so.so_number}</p>
                  <p className="text-sm text-gray-500">{so.customer_name || so.customer}</p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  so.status === 'Submitted' ? 'bg-green-100 text-green-700' :
                  so.status === 'Draft' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-700'
                }`}>{so.status}</span>
              </div>
            ))}
            {(!soData?.results || soData.results.length === 0) && (
              <p className="text-gray-400 text-sm text-center py-4">No sales orders yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
