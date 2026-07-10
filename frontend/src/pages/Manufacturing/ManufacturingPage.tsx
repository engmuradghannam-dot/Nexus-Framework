// pages/Manufacturing/ManufacturingPage.tsx
import { useState } from 'react';
import { Factory, Plus, RefreshCw, Download, CheckCircle, Clock, AlertTriangle, Cog } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentSearchBox } from '../../components/FluentUI/FluentSearchBox';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';

const workOrders = [
  { id: 'MO-001', product: 'وحدة تحكم صناعية', quantity: 500, completed: 340, dueDate: '2026-07-20', status: 'in_progress' },
  { id: 'MO-002', product: 'لوحة كهربائية رئيسية', quantity: 120, completed: 120, dueDate: '2026-07-08', status: 'completed' },
  { id: 'MO-003', product: 'خزان معالجة مياه', quantity: 30, completed: 0, dueDate: '2026-07-28', status: 'planned' },
  { id: 'MO-004', product: 'مضخة هيدروليكية', quantity: 75, completed: 20, dueDate: '2026-07-15', status: 'delayed' },
];

export default function ManufacturingPage() {
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = workOrders.filter(
    (w) => !searchQuery || w.product.includes(searchQuery) || w.id.includes(searchQuery)
  );

  const stats = [
    { title: 'أوامر التصنيع', value: workOrders.length, icon: <Factory size={20} />, color: 'blue' as const },
    { title: 'مكتملة', value: workOrders.filter((w) => w.status === 'completed').length, icon: <CheckCircle size={20} />, color: 'green' as const },
    { title: 'قيد التنفيذ', value: workOrders.filter((w) => w.status === 'in_progress').length, icon: <Cog size={20} />, color: 'orange' as const },
    { title: 'متأخرة', value: workOrders.filter((w) => w.status === 'delayed').length, icon: <AlertTriangle size={20} />, color: 'red' as const },
  ];

  const columns = [
    { key: 'id', label: 'الرمز', sortable: true },
    { key: 'product', label: 'المنتج', sortable: true },
    { key: 'quantity', label: 'الكمية', sortable: true },
    { key: 'completed', label: 'المنجز', sortable: true, render: (v: number, row: any) => (
      <span>{v} / {row.quantity} <span className="text-[#605e5c]">({Math.round((v / row.quantity) * 100)}%)</span></span>
    )},
    { key: 'dueDate', label: 'تاريخ التسليم', sortable: true },
    { key: 'status', label: 'الحالة', sortable: true, render: (v: string) => (
      <FluentBadge
        label={v === 'completed' ? 'مكتمل' : v === 'in_progress' ? 'قيد التنفيذ' : v === 'delayed' ? 'متأخر' : 'مخطّط'}
        variant={v === 'completed' ? 'success' : v === 'in_progress' ? 'info' : v === 'delayed' ? 'error' : 'neutral'}
        size="small"
      />
    )},
  ];

  return (
    <div className="min-h-screen bg-[#faf9f8]" dir="rtl">
      <FluentCommandBar
        title="التصنيع"
        subtitle="Manufacturing & Production Orders"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary' },
          { id: 'export', label: 'تصدير', icon: <Download size={16} />, variant: 'secondary' },
          { id: 'new', label: 'أمر تصنيع', icon: <Plus size={16} />, variant: 'primary' },
        ]}
      />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {stats.map((stat) => <FluentStatsCard key={stat.title} {...stat} />)}
        </div>
        <FluentCard padding="small">
          <FluentSearchBox value={searchQuery} onChange={setSearchQuery} placeholder="البحث في أوامر التصنيع..." className="w-80" />
        </FluentCard>
        <FluentTable
          title="أوامر التصنيع"
          subtitle={`${filtered.length} أمر`}
          columns={columns}
          data={filtered}
        />
      </div>
    </div>
  );
}
