// pages/CRM/CRMPage.tsx
import { useState } from 'react';
import { HeartHandshake, Plus, RefreshCw, Download, Phone, Mail, Building2, Star, Trash2, Edit3 } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentSearchBox } from '../../components/FluentUI/FluentSearchBox';
import { FluentPanel, FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';

const customers = [
  { id: '1', name: 'شركة التقنية المتقدمة', contact: 'أحمد العلي', email: 'info@tech-adv.com', phone: '+966 11 111 1111', industry: 'تقنية', status: 'active', rating: 5, revenue: 2500000 },
  { id: '2', name: 'مؤسسة النور للتجارة', contact: 'سارة أحمد', email: 'contact@alnoor.com', phone: '+966 12 222 2222', industry: 'تجارة', status: 'active', rating: 4, revenue: 1200000 },
  { id: '3', name: 'مصنع الصلب الوطني', contact: 'خالد السالم', email: 'sales@steel-nat.com', phone: '+966 13 333 3333', industry: 'صناعة', status: 'prospect', rating: 3, revenue: 0 },
  { id: '4', name: 'مستشفى الأمل', contact: 'فاطمة حسن', email: 'admin@alamal-hosp.com', phone: '+966 14 444 4444', industry: 'صحة', status: 'active', rating: 5, revenue: 800000 },
  { id: '5', name: 'شركة الإنشاءات الحديثة', contact: 'عمر خالد', email: 'info@modern-build.com', phone: '+966 11 555 5555', industry: 'إنشاءات', status: 'inactive', rating: 2, revenue: 500000 },
];

export default function CRMPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showPanel, setShowPanel] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<any>(null);

  const filtered = customers.filter(c => 
    !searchQuery || c.name.includes(searchQuery) || c.contact.includes(searchQuery)
  );

  const stats = [
    { title: 'إجمالي العملاء', value: customers.length, icon: <HeartHandshake size={20} />, color: 'blue' as const },
    { title: 'نشط', value: customers.filter(c => c.status === 'active').length, icon: <Star size={20} />, color: 'green' as const },
    { title: ' prospects', value: customers.filter(c => c.status === 'prospect').length, icon: <Building2 size={20} />, color: 'orange' as const },
    { title: 'إجمالي الإيرادات', value: `${(customers.reduce((s, c) => s + c.revenue, 0) / 1000000).toFixed(1)}M ر.س`, icon: <Phone size={20} />, color: 'purple' as const },
  ];

  const columns = [
    { key: 'name', label: 'العميل', sortable: true, render: (v: string, row: any) => (
      <div>
        <p className="font-medium text-[#323130]">{v}</p>
        <p className="text-xs text-[#605e5c]">{row.contact}</p>
      </div>
    )},
    { key: 'industry', label: 'القطاع', sortable: true },
    { key: 'phone', label: 'الهاتف', sortable: true },
    { key: 'email', label: 'البريد', sortable: true },
    { key: 'status', label: 'الحالة', sortable: true, render: (v: string) => (
      <FluentBadge label={v === 'active' ? 'نشط' : v === 'prospect' ? ' prospect' : 'غير نشط'} variant={v === 'active' ? 'success' : v === 'prospect' ? 'warning' : 'neutral'} size="small" />
    )},
    { key: 'rating', label: 'التقييم', sortable: true, render: (v: number) => (
      <div className="flex gap-0.5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Star key={i} size={14} className={i < v ? 'text-[#ffc107] fill-[#ffc107]' : 'text-[#e1dfdd]'} />
        ))}
      </div>
    )},
  ];

  return (
    <div className="min-h-screen bg-[#faf9f8]">
      <FluentCommandBar
        title="إدارة العملاء (CRM)"
        subtitle="Customer Relationship Management"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary' },
          { id: 'export', label: 'تصدير', icon: <Download size={16} />, variant: 'secondary' },
          { id: 'new', label: 'عميل جديد', icon: <Plus size={16} />, variant: 'primary' },
        ]}
      />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {stats.map((stat) => <FluentStatsCard key={stat.title} {...stat} />)}
        </div>
        <FluentCard padding="small">
          <FluentSearchBox value={searchQuery} onChange={setSearchQuery} placeholder="البحث في العملاء..." className="w-80" />
        </FluentCard>
        <FluentTable
          title="قائمة العملاء"
          subtitle={`${filtered.length} عميل`}
          columns={columns}
          data={filtered}
          selectable
          onRowClick={(row) => { setSelectedCustomer(row); setShowPanel(true); }}
          actions={(row) => (
            <div className="py-1">
              <button className="w-full px-4 py-2 text-right text-sm text-[#323130] hover:bg-[#f3f2f1] flex items-center gap-2"><Edit3 size={14} /> تعديل</button>
              <button className="w-full px-4 py-2 text-right text-sm text-[#d83b01] hover:bg-[#fdf2f2] flex items-center gap-2"><Trash2 size={14} /> حذف</button>
            </div>
          )}
        />
      </div>
      <FluentPanel isOpen={showPanel} onClose={() => setShowPanel(false)} title={selectedCustomer?.name || 'تفاصيل العميل'} footer={
        <div className="flex items-center justify-end gap-2">
          <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إغلاق</button>
          <button className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>
      }>
        {selectedCustomer && (
          <div className="space-y-4">
            <FluentFormField label="اسم الشركة" required><FluentInput defaultValue={selectedCustomer.name} /></FluentFormField>
            <FluentFormField label="اسم المسؤول"><FluentInput defaultValue={selectedCustomer.contact} /></FluentFormField>
            <FluentFormField label="البريد الإلكتروني"><FluentInput defaultValue={selectedCustomer.email} /></FluentFormField>
            <FluentFormField label="الهاتف"><FluentInput defaultValue={selectedCustomer.phone} /></FluentFormField>
            <FluentFormField label="القطاع"><FluentSelect defaultValue={selectedCustomer.industry}><option>تقنية</option><option>تجارة</option><option>صناعة</option><option>صحة</option><option>إنشاءات</option></FluentSelect></FluentFormField>
            <FluentFormField label="الحالة"><FluentSelect defaultValue={selectedCustomer.status}><option value="active">نشط</option><option value="prospect"> prospect</option><option value="inactive">غير نشط</option></FluentSelect></FluentFormField>
          </div>
        )}
      </FluentPanel>
    </div>
  );
}
