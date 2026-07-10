// pages/Warehouses/WarehousesPage.tsx
import { useState } from 'react';
import { 
  Warehouse, Plus, Search, Filter, Package, AlertTriangle, 
  TrendingDown, CheckCircle, ArrowUpDown, BarChart3, MapPin 
} from 'lucide-react';

interface WarehouseItem {
  id: string;
  name: string;
  sku: string;
  category: string;
  quantity: number;
  minLevel: number;
  maxLevel: number;
  reorderPoint: number;
  unit: string;
  location: string;
  status: 'in_stock' | 'low_stock' | 'out_of_stock' | 'reorder';
  lastUpdated: string;
}

const demoItems: WarehouseItem[] = [
  {
    id: '1', name: 'لابتوب Dell XPS 15', sku: 'DL-XPS-15-001', category: 'أجهزة الكمبيوتر',
    quantity: 45, minLevel: 10, maxLevel: 100, reorderPoint: 20, unit: 'جهاز',
    location: 'مستودع الرياض — رف A1', status: 'in_stock', lastUpdated: '2026-07-10'
  },
  {
    id: '2', name: 'شاشة Samsung 27"', sku: 'SAM-MON-27-002', category: 'شاشات',
    quantity: 8, minLevel: 15, maxLevel: 50, reorderPoint: 15, unit: 'شاشة',
    location: 'مستودع الرياض — رف B3', status: 'low_stock', lastUpdated: '2026-07-09'
  },
  {
    id: '3', name: 'طابعة HP LaserJet', sku: 'HP-PRT-LJ-003', category: 'طابعات',
    quantity: 0, minLevel: 5, maxLevel: 30, reorderPoint: 8, unit: 'طابعة',
    location: 'مستودع جدة — رف C2', status: 'out_of_stock', lastUpdated: '2026-07-08'
  },
  {
    id: '4', name: 'كيبورد Logitech MX', sku: 'LOG-KB-MX-004', category: 'ملحقات',
    quantity: 18, minLevel: 20, maxLevel: 80, reorderPoint: 25, unit: 'كيبورد',
    location: 'مستودع الرياض — رف D4', status: 'reorder', lastUpdated: '2026-07-10'
  }
];

const statusConfig = {
  in_stock: { label: 'متوفر', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  low_stock: { label: 'منخفض', color: 'bg-yellow-100 text-yellow-700', icon: AlertTriangle },
  out_of_stock: { label: 'نفذ', color: 'bg-red-100 text-red-700', icon: AlertTriangle },
  reorder: { label: 'إعادة طلب', color: 'bg-orange-100 text-orange-700', icon: ArrowUpDown }
};

export default function WarehousesPage() {
  const [items, setItems] = useState<WarehouseItem[]>(demoItems);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterCategory, setFilterCategory] = useState('');

  const filtered = items.filter(i => {
    const matchSearch = !searchQuery || i.name.includes(searchQuery) || i.sku.includes(searchQuery);
    const matchStatus = !filterStatus || i.status === filterStatus;
    const matchCategory = !filterCategory || i.category === filterCategory;
    return matchSearch && matchStatus && matchCategory;
  });

  const categories = [...new Set(items.map(i => i.category))];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-100 rounded-xl"><Warehouse className="text-amber-600" size={24} /></div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">المستودعات والمخزون</h1>
              <p className="text-sm text-gray-500">Inventory & Warehouses — إدارة المخزون والطلبات</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-2 px-4 py-2.5 border border-gray-200 rounded-xl hover:bg-gray-50">
              <BarChart3 size={18} /> تقرير
            </button>
            <button className="flex items-center gap-2 px-4 py-2.5 bg-amber-600 text-white rounded-xl hover:bg-amber-700 transition-colors">
              <Plus size={18} /> إضافة صنف
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 p-6">
        {[
          { label: 'إجمالي الأصناف', value: items.length, icon: Package, color: 'bg-blue-500' },
          { label: 'متوفر', value: items.filter(i => i.status === 'in_stock').length, icon: CheckCircle, color: 'bg-green-500' },
          { label: 'منخفض', value: items.filter(i => i.status === 'low_stock').length, icon: AlertTriangle, color: 'bg-yellow-500' },
          { label: 'نفذ', value: items.filter(i => i.status === 'out_of_stock').length, icon: TrendingDown, color: 'bg-red-500' }
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl border p-4 flex items-center gap-4">
            <div className={`w-12 h-12 ${stat.color} rounded-xl flex items-center justify-center text-white`}>
              <stat.icon size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-800">{stat.value}</p>
              <p className="text-sm text-gray-500">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="px-6 pb-4">
        <div className="bg-white rounded-xl border p-4 flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[300px]">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="البحث باسم الصنف أو SKU..."
              className="w-full pr-10 pl-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-amber-500" />
          </div>
          <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}
            className="border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-amber-500">
            <option value="">كل الفئات</option>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
            className="border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-amber-500">
            <option value="">كل الحالات</option>
            <option value="in_stock">متوفر</option>
            <option value="low_stock">منخفض</option>
            <option value="out_of_stock">نفذ</option>
            <option value="reorder">إعادة طلب</option>
          </select>
        </div>
      </div>

      {/* Items Table */}
      <div className="px-6 pb-6">
        <div className="bg-white rounded-2xl border shadow-sm overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الصنف</th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">SKU</th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الكمية</th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الحد الأدنى</th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">نقطة إعادة الطلب</th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الحالة</th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الموقع</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filtered.map((item) => {
                const StatusIcon = statusConfig[item.status].icon;
                const progress = (item.quantity / item.maxLevel) * 100;
                return (
                  <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-semibold text-gray-800">{item.name}</p>
                        <p className="text-sm text-gray-500">{item.category}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm font-mono text-gray-600">{item.sku}</td>
                    <td className="px-6 py-4">
                      <div className="w-24">
                        <div className="flex justify-between text-sm mb-1">
                          <span className="font-semibold">{item.quantity}</span>
                          <span className="text-gray-400">{item.unit}</span>
                        </div>
                        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full ${progress > 50 ? 'bg-green-500' : progress > 20 ? 'bg-yellow-500' : 'bg-red-500'}`}
                            style={{ width: `${Math.min(progress, 100)}%` }} />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{item.minLevel}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{item.reorderPoint}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${statusConfig[item.status].color}`}>
                        <StatusIcon size={12} /> {statusConfig[item.status].label}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      <div className="flex items-center gap-1"><MapPin size={12} className="text-amber-500" /> {item.location}</div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
