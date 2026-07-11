// pages/Inventory/InventoryPage.tsx
import { useState } from 'react';
import { Boxes, Plus, RefreshCw, Download, AlertTriangle, CheckCircle, ArrowUpDown, Package } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentSearchBox } from '../../components/FluentUI/FluentSearchBox';
import { FluentPanel, FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { exportToCsv } from '../../utils/exportCsv';

const stockItems = [
  { id: '1', name: 'لابتوب Dell XPS 15', sku: 'DL-XPS-15-001', warehouse: 'الرياض', quantity: 45, minLevel: 10, reorderPoint: 20, status: 'in_stock' },
  { id: '2', name: 'شاشة Samsung 27"', sku: 'SAM-MON-27-002', warehouse: 'الرياض', quantity: 8, minLevel: 15, reorderPoint: 15, status: 'low_stock' },
  { id: '3', name: 'طابعة HP LaserJet', sku: 'HP-PRT-LJ-003', warehouse: 'جدة', quantity: 0, minLevel: 5, reorderPoint: 8, status: 'out_of_stock' },
  { id: '4', name: 'كيبورد Logitech MX', sku: 'LOG-KB-MX-004', warehouse: 'الرياض', quantity: 18, minLevel: 20, reorderPoint: 25, status: 'reorder' },
  { id: '5', name: 'ماوس Microsoft Surface', sku: 'MS-SUR-MOU-005', warehouse: 'الدمام', quantity: 120, minLevel: 50, reorderPoint: 60, status: 'in_stock' },
  { id: '6', name: 'راوتر Cisco ASA', sku: 'CIS-ASA-RT-006', warehouse: 'الرياض', quantity: 3, minLevel: 10, reorderPoint: 12, status: 'low_stock' },
];

export default function InventoryPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showPanel, setShowPanel] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any>(null);

  const filtered = stockItems.filter(i => !searchQuery || i.name.includes(searchQuery) || i.sku.includes(searchQuery));

  const stats = [
    { title: 'إجمالي الأصناف', value: stockItems.length, icon: <Boxes size={20} />, color: 'blue' as const },
    { title: 'متوفر', value: stockItems.filter(i => i.status === 'in_stock').length, icon: <CheckCircle size={20} />, color: 'green' as const },
    { title: 'منخفض', value: stockItems.filter(i => i.status === 'low_stock').length, icon: <AlertTriangle size={20} />, color: 'orange' as const },
    { title: 'إعادة طلب', value: stockItems.filter(i => i.status === 'reorder').length, icon: <ArrowUpDown size={20} />, color: 'red' as const },
  ];

  const columns = [
    { key: 'sku', label: 'الرمز', sortable: true },
    { key: 'name', label: 'الصنف', sortable: true },
    { key: 'warehouse', label: 'المستودع', sortable: true },
    { key: 'quantity', label: 'الكمية', sortable: true },
    { key: 'minLevel', label: 'الحد الأدنى', sortable: true },
    { key: 'reorderPoint', label: 'نقطة إعادة الطلب', sortable: true },
    { key: 'status', label: 'الحالة', sortable: true, render: (v: string) => (
      <FluentBadge label={v === 'in_stock' ? 'متوفر' : v === 'low_stock' ? 'منخفض' : v === 'out_of_stock' ? 'نفذ' : 'إعادة طلب'} 
        variant={v === 'in_stock' ? 'success' : v === 'low_stock' ? 'warning' : v === 'out_of_stock' ? 'error' : 'info'} size="small" />
    )},
  ];

  return (
    <div className="min-h-screen bg-[#faf9f8]">
      <FluentCommandBar
        title="المخزون"
        subtitle="Stock Overview & Inventory Control"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: () => window.location.reload() },
          { id: 'export', label: 'تصدير', icon: <Download size={16} />, variant: 'secondary', onClick: () => exportToCsv(stockItems, 'inventory.csv') },
          { id: 'reorder', label: 'إعادة طلب', icon: <ArrowUpDown size={16} />, variant: 'secondary' },
          { id: 'new', label: 'إضافة صنف', icon: <Plus size={16} />, variant: 'primary', onClick: () => { setSelectedItem({}); setShowPanel(true); } },
        ]}
      />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {stats.map((stat) => <FluentStatsCard key={stat.title} {...stat} />)}
        </div>
        <FluentCard padding="small">
          <FluentSearchBox value={searchQuery} onChange={setSearchQuery} placeholder="البحث في المخزون..." className="w-80" />
        </FluentCard>
        <FluentTable
          title="نظرة عامة على المخزون"
          subtitle={`${filtered.length} صنف`}
          columns={columns}
          data={filtered}
          selectable
          onRowClick={(row) => { setSelectedItem(row); setShowPanel(true); }}
        />
      </div>
      <FluentPanel isOpen={showPanel} onClose={() => setShowPanel(false)} title={selectedItem?.name || 'تفاصيل الصنف'} footer={
        <div className="flex items-center justify-end gap-2">
          <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إغلاق</button>
          <button className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>
      }>
        {selectedItem && (
          <div className="space-y-4">
            <FluentFormField label="الرمز (SKU)"><FluentInput defaultValue={selectedItem.sku} disabled /></FluentFormField>
            <FluentFormField label="اسم الصنف"><FluentInput defaultValue={selectedItem.name} /></FluentFormField>
            <FluentFormField label="المستودع"><FluentSelect defaultValue={selectedItem.warehouse}><option>الرياض</option><option>جدة</option><option>الدمام</option></FluentSelect></FluentFormField>
            <div className="grid grid-cols-2 gap-4">
              <FluentFormField label="الكمية"><FluentInput type="number" defaultValue={selectedItem.quantity} /></FluentFormField>
              <FluentFormField label="الحد الأدنى"><FluentInput type="number" defaultValue={selectedItem.minLevel} /></FluentFormField>
            </div>
            <FluentFormField label="نقطة إعادة الطلب"><FluentInput type="number" defaultValue={selectedItem.reorderPoint} /></FluentFormField>
            <FluentFormField label="الحالة"><FluentSelect defaultValue={selectedItem.status}><option value="in_stock">متوفر</option><option value="low_stock">منخفض</option><option value="out_of_stock">نفذ</option><option value="reorder">إعادة طلب</option></FluentSelect></FluentFormField>
          </div>
        )}
      </FluentPanel>
    </div>
  );
}
