// pages/Warehouses/WarehousesPage.tsx
import { useState } from 'react';
import { 
  Warehouse, Plus, Filter, Package, AlertTriangle, CheckCircle, 
  ArrowUpDown, BarChart3, MapPin, RefreshCw, Download, Trash2, Edit3
} from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentSearchBox } from '../../components/FluentUI/FluentSearchBox';
import { FluentPanel, FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';

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
  { id: '1', name: 'لابتوب Dell XPS 15', sku: 'DL-XPS-15-001', category: 'أجهزة الكمبيوتر', quantity: 45, minLevel: 10, maxLevel: 100, reorderPoint: 20, unit: 'جهاز', location: 'مستودع الرياض — رف A1', status: 'in_stock', lastUpdated: '2026-07-10' },
  { id: '2', name: 'شاشة Samsung 27"', sku: 'SAM-MON-27-002', category: 'شاشات', quantity: 8, minLevel: 15, maxLevel: 50, reorderPoint: 15, unit: 'شاشة', location: 'مستودع الرياض — رف B3', status: 'low_stock', lastUpdated: '2026-07-09' },
  { id: '3', name: 'طابعة HP LaserJet', sku: 'HP-PRT-LJ-003', category: 'طابعات', quantity: 0, minLevel: 5, maxLevel: 30, reorderPoint: 8, unit: 'طابعة', location: 'مستودع جدة — رف C2', status: 'out_of_stock', lastUpdated: '2026-07-08' },
  { id: '4', name: 'كيبورد Logitech MX', sku: 'LOG-KB-MX-004', category: 'ملحقات', quantity: 18, minLevel: 20, maxLevel: 80, reorderPoint: 25, unit: 'كيبورد', location: 'مستودع الرياض — رف D4', status: 'reorder', lastUpdated: '2026-07-10' },
  { id: '5', name: 'ماوس Microsoft Surface', sku: 'MS-SUR-MOU-005', category: 'ملحقات', quantity: 120, minLevel: 50, maxLevel: 200, reorderPoint: 60, unit: 'ماوس', location: 'مستودع الدمام — رف E1', status: 'in_stock', lastUpdated: '2026-07-10' },
  { id: '6', name: 'راوتر Cisco ASA', sku: 'CIS-ASA-RT-006', category: 'شبكات', quantity: 3, minLevel: 10, maxLevel: 40, reorderPoint: 12, unit: 'راوتر', location: 'مستودع الرياض — رف F2', status: 'low_stock', lastUpdated: '2026-07-07' },
];

const statusMap = {
  in_stock: { label: 'متوفر', variant: 'success' as const, icon: CheckCircle },
  low_stock: { label: 'منخفض', variant: 'warning' as const, icon: AlertTriangle },
  out_of_stock: { label: 'نفذ', variant: 'error' as const, icon: AlertTriangle },
  reorder: { label: 'إعادة طلب', variant: 'info' as const, icon: ArrowUpDown },
};

export default function WarehousesPage() {
  const [items] = useState<WarehouseItem[]>(demoItems);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [showPanel, setShowPanel] = useState(false);
  const [selectedItem, setSelectedItem] = useState<WarehouseItem | null>(null);

  const filtered = items.filter(i => {
    const matchSearch = !searchQuery || i.name.includes(searchQuery) || i.sku.includes(searchQuery);
    const matchStatus = !filterStatus || i.status === filterStatus;
    return matchSearch && matchStatus;
  });

  const columns = [
    { key: 'name', label: 'الصنف', sortable: true, render: (v: string, row: WarehouseItem) => (
      <div>
        <p className="font-medium text-[#323130]">{v}</p>
        <p className="text-xs text-[#605e5c]">{row.sku}</p>
      </div>
    )},
    { key: 'category', label: 'الفئة', sortable: true },
    { key: 'quantity', label: 'الكمية', sortable: true, render: (v: number, row: WarehouseItem) => (
      <div className="flex items-center gap-2">
        <span className="font-medium">{v}</span>
        <span className="text-xs text-[#605e5c]">{row.unit}</span>
      </div>
    )},
    { key: 'location', label: 'الموقع', sortable: true, render: (v: string) => (
      <div className="flex items-center gap-1 text-[#605e5c]">
        <MapPin size={14} />
        <span className="text-sm">{v}</span>
      </div>
    )},
    { key: 'status', label: 'الحالة', sortable: true, render: (v: string) => {
      const config = statusMap[v as keyof typeof statusMap];
      return <FluentBadge label={config.label} variant={config.variant} />;
    }},
    { key: 'lastUpdated', label: 'آخر تحديث', sortable: true },
  ];

  const stats = [
    { title: 'إجمالي الأصناف', value: items.length, icon: <Package size={20} />, color: 'blue' as const },
    { title: 'متوفر', value: items.filter(i => i.status === 'in_stock').length, icon: <CheckCircle size={20} />, color: 'green' as const },
    { title: 'منخفض', value: items.filter(i => i.status === 'low_stock').length, icon: <AlertTriangle size={20} />, color: 'orange' as const },
    { title: 'نفذ', value: items.filter(i => i.status === 'out_of_stock').length, icon: <AlertTriangle size={20} />, color: 'red' as const },
  ];

  return (
    <div className="min-h-screen bg-[#faf9f8]">
      <FluentCommandBar
        title="المستودعات والمخزون"
        subtitle="Inventory & Warehouses — إدارة المخزون والطلبات"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary' },
          { id: 'export', label: 'تصدير', icon: <Download size={16} />, variant: 'secondary' },
          { id: 'report', label: 'تقرير', icon: <BarChart3 size={16} />, variant: 'secondary' },
          { id: 'new', label: 'إضافة صنف', icon: <Plus size={16} />, variant: 'primary' },
        ]}
      />

      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <FluentStatsCard key={stat.title} {...stat} />
          ))}
        </div>

        {/* Filters */}
        <FluentCard padding="small">
          <div className="flex flex-wrap items-center gap-3">
            <FluentSearchBox
              placeholder="البحث في الأصناف..."
              value={searchQuery}
              onChange={setSearchQuery}
              className="w-80"
            />
            <FluentSelect
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-40"
            >
              <option value="">كل الحالات</option>
              <option value="in_stock">متوفر</option>
              <option value="low_stock">منخفض</option>
              <option value="out_of_stock">نفذ</option>
              <option value="reorder">إعادة طلب</option>
            </FluentSelect>
            <button className="flex items-center gap-2 px-3 py-2 text-sm text-[#323130] border border-[#e1dfdd] rounded-sm hover:bg-[#f3f2f1]">
              <Filter size={16} /> تصفية متقدمة
            </button>
          </div>
        </FluentCard>

        {/* Table */}
        <FluentTable
          title="قائمة المخزون"
          subtitle={`${filtered.length} صنف`}
          columns={columns}
          data={filtered}
          selectable
          onRowClick={(row) => { setSelectedItem(row); setShowPanel(true); }}
          actions={(row) => (
            <div className="py-1">
              <button className="w-full px-4 py-2 text-right text-sm text-[#323130] hover:bg-[#f3f2f1] flex items-center gap-2">
                <Edit3 size={14} /> تعديل
              </button>
              <button className="w-full px-4 py-2 text-right text-sm text-[#d83b01] hover:bg-[#fdf2f2] flex items-center gap-2">
                <Trash2 size={14} /> حذف
              </button>
            </div>
          )}
          emptyMessage="لا توجد أصناف مطابقة"
        />
      </div>

      {/* Detail Panel */}
      <FluentPanel
        isOpen={showPanel}
        onClose={() => setShowPanel(false)}
        title={selectedItem?.name || 'تفاصيل الصنف'}
        subtitle={selectedItem?.sku}
        footer={
          <div className="flex items-center justify-end gap-2">
            <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">
              إغلاق
            </button>
            <button className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">
              حفظ التغييرات
            </button>
          </div>
        }
      >
        {selectedItem && (
          <div className="space-y-4">
            <FluentFormField label="اسم الصنف" required>
              <FluentInput defaultValue={selectedItem.name} />
            </FluentFormField>
            <FluentFormField label="الرمز (SKU)">
              <FluentInput defaultValue={selectedItem.sku} disabled />
            </FluentFormField>
            <FluentFormField label="الفئة">
              <FluentSelect defaultValue={selectedItem.category}>
                <option>أجهزة الكمبيوتر</option>
                <option>شاشات</option>
                <option>طابعات</option>
                <option>ملحقات</option>
                <option>شبكات</option>
              </FluentSelect>
            </FluentFormField>
            <div className="grid grid-cols-2 gap-4">
              <FluentFormField label="الكمية الحالية">
                <FluentInput type="number" defaultValue={selectedItem.quantity} />
              </FluentFormField>
              <FluentFormField label="الوحدة">
                <FluentInput defaultValue={selectedItem.unit} />
              </FluentFormField>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <FluentFormField label="الحد الأدنى">
                <FluentInput type="number" defaultValue={selectedItem.minLevel} />
              </FluentFormField>
              <FluentFormField label="نقطة إعادة الطلب">
                <FluentInput type="number" defaultValue={selectedItem.reorderPoint} />
              </FluentFormField>
            </div>
            <FluentFormField label="الموقع">
              <FluentInput defaultValue={selectedItem.location} />
            </FluentFormField>
            <FluentFormField label="الحالة">
              <FluentSelect defaultValue={selectedItem.status}>
                <option value="in_stock">متوفر</option>
                <option value="low_stock">منخفض</option>
                <option value="out_of_stock">نفذ</option>
                <option value="reorder">إعادة طلب</option>
              </FluentSelect>
            </FluentFormField>
          </div>
        )}
      </FluentPanel>
    </div>
  );
}
