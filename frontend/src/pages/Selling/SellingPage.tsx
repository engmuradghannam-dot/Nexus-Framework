// pages/Selling/SellingPage.tsx
import { useState } from 'react';
import { ShoppingCart, Plus, RefreshCw, Download, FileText, CheckCircle, Clock, XCircle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentSearchBox } from '../../components/FluentUI/FluentSearchBox';
import { FluentPanel, FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { exportToCsv } from '../../utils/exportCsv';

const orders = [
  { id: 'SO-2026-001', customer: 'شركة التقنية المتقدمة', date: '2026-07-10', total: 45000, status: 'confirmed', items: 5 },
  { id: 'SO-2026-002', customer: 'مؤسسة النور للتجارة', date: '2026-07-09', total: 12000, status: 'pending', items: 2 },
  { id: 'SO-2026-003', customer: 'مصنع الصلب الوطني', date: '2026-07-08', total: 89000, status: 'shipped', items: 8 },
  { id: 'SO-2026-004', customer: 'مستشفى الأمل', date: '2026-07-07', total: 23000, status: 'cancelled', items: 3 },
  { id: 'SO-2026-005', customer: 'شركة الإنشاءات الحديثة', date: '2026-07-06', total: 67000, status: 'confirmed', items: 6 },
];

export default function SellingPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showPanel, setShowPanel] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<any>(null);

  const filtered = orders.filter(o => !searchQuery || o.customer.includes(searchQuery) || o.id.includes(searchQuery));

  const stats = [
    { title: 'إجمالي الطلبات', value: orders.length, icon: <ShoppingCart size={20} />, color: 'blue' as const },
    { title: 'مؤكد', value: orders.filter(o => o.status === 'confirmed').length, icon: <CheckCircle size={20} />, color: 'green' as const },
    { title: 'معلق', value: orders.filter(o => o.status === 'pending').length, icon: <Clock size={20} />, color: 'orange' as const },
    { title: 'إجمالي المبيعات', value: `${(orders.reduce((s, o) => s + o.total, 0) / 1000).toFixed(0)}K ر.س`, icon: <FileText size={20} />, color: 'purple' as const },
  ];

  const columns = [
    { key: 'id', label: 'رقم الطلب', sortable: true },
    { key: 'customer', label: 'العميل', sortable: true },
    { key: 'date', label: 'التاريخ', sortable: true },
    { key: 'items', label: 'الأصناف', sortable: true },
    { key: 'total', label: 'الإجمالي', sortable: true, render: (v: number) => <span className="font-medium">{v.toLocaleString()} ر.س</span> },
    { key: 'status', label: 'الحالة', sortable: true, render: (v: string) => (
      <FluentBadge label={v === 'confirmed' ? 'مؤكد' : v === 'pending' ? 'معلق' : v === 'shipped' ? 'تم الشحن' : 'ملغى'} 
        variant={v === 'confirmed' ? 'success' : v === 'pending' ? 'warning' : v === 'shipped' ? 'info' : 'error'} size="small" />
    )},
  ];

  return (
    <div className="min-h-screen bg-[#faf9f8]">
      <FluentCommandBar
        title="المبيعات"
        subtitle="Sales Orders & Quotations"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: () => window.location.reload() },
          { id: 'export', label: 'تصدير', icon: <Download size={16} />, variant: 'secondary', onClick: () => exportToCsv(orders, 'selling.csv') },
          { id: 'quote', label: 'عرض سعر', icon: <FileText size={16} />, variant: 'secondary' },
          { id: 'new', label: 'طلب بيع', icon: <Plus size={16} />, variant: 'primary', onClick: () => { setSelectedOrder({}); setShowPanel(true); } },
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
          title="طلبات البيع"
          subtitle={`${filtered.length} طلب`}
          columns={columns}
          data={filtered}
          selectable
          onRowClick={(row) => { setSelectedOrder(row); setShowPanel(true); }}
        />
      </div>
      <FluentPanel isOpen={showPanel} onClose={() => setShowPanel(false)} title={selectedOrder?.id || 'تفاصيل الطلب'} footer={
        <div className="flex items-center justify-end gap-2">
          <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إغلاق</button>
          <button className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>
      }>
        {selectedOrder && (
          <div className="space-y-4">
            <FluentFormField label="رقم الطلب"><FluentInput defaultValue={selectedOrder.id} disabled /></FluentFormField>
            <FluentFormField label="العميل"><FluentInput defaultValue={selectedOrder.customer} /></FluentFormField>
            <FluentFormField label="التاريخ"><FluentInput type="date" defaultValue={selectedOrder.date} /></FluentFormField>
            <FluentFormField label="الحالة"><FluentSelect defaultValue={selectedOrder.status}><option value="confirmed">مؤكد</option><option value="pending">معلق</option><option value="shipped">تم الشحن</option><option value="cancelled">ملغى</option></FluentSelect></FluentFormField>
            <FluentFormField label="الإجمالي"><FluentInput type="number" defaultValue={selectedOrder.total} /></FluentFormField>
          </div>
        )}
      </FluentPanel>
    </div>
  );
}
