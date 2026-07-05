import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchCompanies } from '../lib/api';
import { Plus, Search, Edit, Trash2, Eye } from 'lucide-react';

export default function Companies() {
  const { data, isLoading } = useQuery({ queryKey: ['companies'], queryFn: fetchCompanies });

  if (isLoading) return <div className="flex justify-center p-10"><div className="animate-spin h-10 w-10 border-b-2 border-blue-600 rounded-full"></div></div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Companies</h2>
          <p className="text-gray-500 text-sm">Manage company profiles and branches</p>
        </div>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700">
          <Plus size={18} /> New Company
        </button>
      </div>
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="p-4 border-b">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
            <input type="text" placeholder="Search companies..." className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none" />
          </div>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Name</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Tax ID</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Email</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Currency</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data?.results?.map((company) => (
              <tr key={company.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium text-blue-600">{company.name}</td>
                <td className="px-6 py-4 text-gray-700">{company.tax_id}</td>
                <td className="px-6 py-4 text-gray-600 text-sm">{company.email}</td>
                <td className="px-6 py-4 text-gray-700">{company.currency}</td>
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
