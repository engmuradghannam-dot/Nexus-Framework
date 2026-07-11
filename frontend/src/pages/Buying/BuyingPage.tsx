// pages/Buying/BuyingPage.tsx
import { useState } from 'react';
import { Store, Plus, RefreshCw, Download, FileText, CheckCircle, Clock, Truck } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentSearchBox } from '../../components/FluentUI/FluentSearchBox';
import { FluentPanel, FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { exportToCsv } from '../../utils/exportCsv';

const purchaseOrders = [
  { id: 'PO-2026-001', supplier: 'شركة Dell Technologies', date: '2026-07-10', total: 125000, status: 'approved', items: 10 },
  { id: 'PO-2026-002', supplier: 'HP Enterprise', date: '2026-07-09', total: 45000, status: 'pending', items: 5 },
  { id: 'PO-2026-003', supplier: 'Samsung Electronics', date: '2026-07-08', total: 78000, status: 'received', items: 7 },
  { id: 'PO-2026-004', supplier: 'Cisco Systems', date: '2026-07-07', total: 95000, status: 'draft', items: 4 },
  { id: 'PO-2026-005', supplier: 'Logitech International', date: '2026-07-06', total: 12000, status: 'approved', items: 2 },
];

export default function BuyingPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showPanel, setShowPanel] = useState(false);
  const [selectedPO, setSelectedPO] = useState<any>(null);

  const filtered = purchaseOrders.filter(p => !searchQuery || p.supplier.includes(searchQuery) || p.id.includes(searchQuery));

  const stats = [
    { title: 'إجمالي الطلبات', value: purchaseOrders.length, icon: <Store size={20} />, color: 'blue' as const },
    { title: 'معتمد', value: purchaseOrders.filter(p => p.status === 'approved').length, icon: <CheckCircle size={20} />, color: 'green' as const },
    { title: 'معلق', value: purchaseOrders.filter(p => p.status === 'pending').length, icon: <Clock size={20} />, color: 'orange' as const },
    { title: 'إجمالي المشتريات', value: `${(purchaseOrders.reduce((s, p) => s + p.total, 0) / 1000).toFixed(0)}K ر.س`, icon: <FileText size={20} />, color: 'purple' as const },
  ];

  const columns = [
    { key: 'id', label: 'رقم الطلب', sortable: true },
    { key: 'supplier', label: 'المورد', sortable: true },
    { key: 'date', label: 'التاريخ', sortable: true },
    { key: 'items', label: 'الأصناف', sortable: true },
    { key: 'total', label: 'الإجمالي', sortable: true, render: (v: number) => <span className="font-medium">{v.toLocaleString()} ر.س</span> },
    { key: 'status', label: 'الحالة', sortable: true, render: (v: string) => (
      <FluentBadge label={v === 'approved' ? 'معتمد' : v === 'pending' ? 'معلق' : v === 'received' ? 'مستلم' : 'مسودة'} 
        variant={v === 'approved' ? 'success' : v === 'pending' ? 'warning' : v === 'received' ? 'info' : 'neutral'} size="small" />
    )},
  ];

  return (
    <div className="min-h-screen bg-[#faf9f8]">
      <FluentCommandBar
        title="المشتريات"
        subtitle="Purchase Orders & Supplier Management"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: () => window.location.reload() },
          { id: 'export', label: 'تصدير', icon: <Download size={16} />, variant: 'secondary', onClick: () => exportToCsv(purchaseOrders, 'buying.csv') },
          { id: 'rfq', label: 'طلب عرض سعر', icon: <FileText size={16} />, variant: 'secondary' },
          { id: 'new', label: 'طلب شراء', icon: <Plus size={16} />, variant: 'primary', onClick: () => { setSelectedPO({}); setShowPanel(true); } },
        ]}
      />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {stats.map((stat) => <FluentStatsCard key={stat.title} {...stat} />)}
        </div>
        <FluentCard padding="small">
          <FluentSearchBox value={searchQuery} onChange={setSearchQuery} placeholder="البحث في الطلبات..." className="w-80" />
        </FluentCard>
        <FluentTable
          title="طلبات الشراء"
          subtitle={`${filtered.length} طلب`}
          columns={columns}
          data={filtered}
          selectable
          onRowClick={(row) => { setSelectedPO(row); setShowPanel(true); }}
        />
      </div>
      <FluentPanel isOpen={showPanel} onClose={() => setShowPanel(false)} title={selectedPO?.id || 'تفاصيل الطلب'} footer={
        <div className="flex items-center justify-end gap-2">
          <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إغلاق</button>
          <button className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>
      }>
        {selectedPO && (
          <div className="space-y-4">
            <FluentFormField label="رقم الطلب"><FluentInput defaultValue={selectedPO.id} disabled /></FluentFormField>
            <FluentFormField label="المورد"><FluentInput defaultValue={selectedPO.supplier} /></FluentFormField>
            <FluentFormField label="التاريخ"><FluentInput type="date" defaultValue={selectedPO.date} /></FluentFormField>
            <FluentFormField label="الحالة"><FluentSelect defaultValue={selectedPO.status}><option value="approved">معتمد</option><option value="pending">معلق</option><option value="received">مستلم</option><option value="draft">مسودة</option></FluentSelect></FluentFormField>
            <FluentFormField label="الإجمالي"><FluentInput type="number" defaultValue={selectedPO.total} /></FluentFormField>
          </div>
        )}
      </FluentPanel>
    </div>
  );
}
