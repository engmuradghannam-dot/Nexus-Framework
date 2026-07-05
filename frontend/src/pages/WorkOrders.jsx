import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchWorkOrders } from '../lib/api';
import { Plus, Search, Edit, Trash2, Eye } from 'lucide-react';

export default function WorkOrders() {
  const { data, isLoading } = useQuery({ queryKey: ['workOrders'], queryFn: fetchWorkOrders });

  if (isLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Work Orders</h2>
          <p className="text-gray-500 text-sm">Manage manufacturing work orders</p>
        </div>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> New WO
        </button>
      </div>
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="p-4 border-b">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
            <input type="text" placeholder="Search work orders..." className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
          </div>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">WO Number</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Item</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Qty</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data?.results?.map((wo) => (
              <tr key={wo.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium text-blue-600">{wo.wo_number}</td>
                <td className="px-6 py-4 text-gray-700">{wo.item_to_manufacture}</td>
                <td className="px-6 py-4 text-gray-600 text-sm">{wo.qty_to_produce}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                    wo.status === 'Completed' ? 'bg-green-100 text-green-700' :
                    wo.status === 'In Progress' ? 'bg-blue-100 text-blue-700' :
                    wo.status === 'Draft' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>{wo.status}</span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex gap-2">
                    <button className="p-1.5 text-gray-600 hover:bg-gray-100 rounded-lg"><Eye size={16} /></button>
                    <button className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg"><Edit size={16} /></button>
                    <button className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg"><Trash2 size={16} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
