// pages/Branches/BranchesPage.tsx
import { useState } from 'react';
import { 
  MapPin, Plus, Search, Filter, Grid, List, Phone, Mail, 
  Users, Building2, MoreVertical, Edit2, Trash2, Navigation 
} from 'lucide-react';

interface Branch {
  id: string;
  name: string;
  address: string;
  city: string;
  country: string;
  phone: string;
  email: string;
  manager: string;
  employees: number;
  status: 'active' | 'inactive';
  coordinates: { lat: number; lng: number };
  type: 'main' | 'branch' | 'warehouse';
}

const demoBranches: Branch[] = [
  {
    id: '1', name: 'الفرع الرئيسي — الرياض', address: 'شارع الملك فهد، برج المملكة',
    city: 'الرياض', country: 'السعودية', phone: '+966 11 123 4567', email: 'riyadh@company.com',
    manager: 'أحمد العلي', employees: 150, status: 'active',
    coordinates: { lat: 24.7136, lng: 46.6753 }, type: 'main'
  },
  {
    id: '2', name: 'فرع جدة', address: 'شارع التحلية، حي الروضة',
    city: 'جدة', country: 'السعودية', phone: '+966 12 987 6543', email: 'jeddah@company.com',
    manager: 'سارة أحمد', employees: 80, status: 'active',
    coordinates: { lat: 21.4858, lng: 39.1925 }, type: 'branch'
  },
  {
    id: '3', name: 'مستودع الدمام', address: 'المنطقة الصناعية الثانية',
    city: 'الدمام', country: 'السعودية', phone: '+966 13 456 7890', email: 'dammam@company.com',
    manager: 'خالد السالم', employees: 45, status: 'active',
    coordinates: { lat: 26.3927, lng: 50.0916 }, type: 'warehouse'
  }
];

export default function BranchesPage() {
  const [branches, setBranches] = useState<Branch[]>(demoBranches);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterCity, setFilterCity] = useState('');

  const filtered = branches.filter(b => {
    const matchSearch = !searchQuery || b.name.includes(searchQuery) || b.city.includes(searchQuery);
    const matchType = !filterType || b.type === filterType;
    const matchCity = !filterCity || b.city === filterCity;
    return matchSearch && matchType && matchCity;
  });

  const cities = [...new Set(branches.map(b => b.city))];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-xl"><MapPin className="text-orange-600" size={24} /></div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">الفروع والمواقع</h1>
              <p className="text-sm text-gray-500">Branches & Locations — إدارة الفروع والمستودعات</p>
            </div>
          </div>
          <button className="flex items-center gap-2 px-4 py-2.5 bg-orange-600 text-white rounded-xl hover:bg-orange-700 transition-colors">
            <Plus size={18} /> إضافة فرع
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white border-b p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[300px]">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="البحث في الفروع..."
              className="w-full pr-10 pl-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-500" />
          </div>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)}
            className="border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-orange-500">
            <option value="">كل الأنواع</option>
            <option value="main">رئيسي</option>
            <option value="branch">فرع</option>
            <option value="warehouse">مستودع</option>
          </select>
          <select value={filterCity} onChange={(e) => setFilterCity(e.target.value)}
            className="border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-orange-500">
            <option value="">كل المدن</option>
            {cities.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <div className="flex border border-gray-200 rounded-xl overflow-hidden">
            <button onClick={() => setViewMode('grid')} className={`p-2.5 ${viewMode === 'grid' ? 'bg-orange-600 text-white' : 'hover:bg-gray-50'}`}><Grid size={18} /></button>
            <button onClick={() => setViewMode('list')} className={`p-2.5 ${viewMode === 'list' ? 'bg-orange-600 text-white' : 'hover:bg-gray-50'}`}><List size={18} /></button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((branch) => (
              <div key={branch.id} className="bg-white rounded-2xl border shadow-sm hover:shadow-md transition-shadow overflow-hidden">
                <div className="h-32 bg-gradient-to-br from-orange-100 to-amber-50 flex items-center justify-center">
                  <MapPin size={48} className="text-orange-300" />
                </div>
                <div className="p-6">
                  <div className="flex items-center justify-between mb-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${branch.type === 'main' ? 'bg-purple-100 text-purple-700' : branch.type === 'branch' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'}`}>
                      {branch.type === 'main' ? 'رئيسي' : branch.type === 'branch' ? 'فرع' : 'مستودع'}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${branch.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                      {branch.status === 'active' ? 'نشط' : 'غير نشط'}
                    </span>
                  </div>
                  <h3 className="font-bold text-lg text-gray-800 mb-2">{branch.name}</h3>
                  <p className="text-sm text-gray-500 mb-4">{branch.address}، {branch.city}</p>
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center gap-2"><Phone size={14} className="text-orange-500" /> {branch.phone}</div>
                    <div className="flex items-center gap-2"><Mail size={14} className="text-orange-500" /> {branch.email}</div>
                    <div className="flex items-center gap-2"><Users size={14} className="text-orange-500" /> {branch.employees} موظف</div>
                    <div className="flex items-center gap-2"><Navigation size={14} className="text-orange-500" /> {branch.coordinates.lat.toFixed(4)}, {branch.coordinates.lng.toFixed(4)}</div>
                  </div>
                  <div className="flex gap-2 mt-4 pt-4 border-t">
                    <button className="flex-1 py-2 text-sm text-orange-600 hover:bg-orange-50 rounded-lg transition-colors">تعديل</button>
                    <button className="flex-1 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors">حذف</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-2xl border shadow-sm overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الفرع</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">المدينة</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">النوع</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الموظفين</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الحالة</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filtered.map((branch) => (
                  <tr key={branch.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-orange-50 rounded-lg"><Building2 className="text-orange-600" size={18} /></div>
                        <div>
                          <p className="font-semibold text-gray-800">{branch.name}</p>
                          <p className="text-sm text-gray-500">{branch.manager}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{branch.city}</td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${branch.type === 'main' ? 'bg-purple-100 text-purple-700' : branch.type === 'branch' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'}`}>
                        {branch.type === 'main' ? 'رئيسي' : branch.type === 'branch' ? 'فرع' : 'مستودع'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{branch.employees}</td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${branch.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {branch.status === 'active' ? 'نشط' : 'غير نشط'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
