// pages/Users/UsersPage.tsx
import { useState } from 'react';
import { Users, Plus, RefreshCw, Download, Shield, Mail, Phone, CheckCircle, XCircle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentSearchBox } from '../../components/FluentUI/FluentSearchBox';
import { FluentPanel, FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { exportToCsv } from '../../utils/exportCsv';

const users = [
  { id: 'USR-001', name: 'أحمد العلي', email: 'ahmed@nexus.com', role: 'مدير النظام', department: 'تقنية', status: 'active', lastLogin: '2026-07-10 09:30' },
  { id: 'USR-002', name: 'سارة أحمد', email: 'sara@nexus.com', role: 'مديرة مبيعات', department: 'مبيعات', status: 'active', lastLogin: '2026-07-10 08:15' },
  { id: 'USR-003', name: 'خالد السالم', email: 'khaled@nexus.com', role: 'محاسب', department: 'مالية', status: 'inactive', lastLogin: '2026-07-05 14:20' },
  { id: 'USR-004', name: 'فاطمة حسن', email: 'fatima@nexus.com', role: 'مهندسة', department: 'تقنية', status: 'active', lastLogin: '2026-07-10 10:00' },
  { id: 'USR-005', name: 'عمر خالد', email: 'omar@nexus.com', role: 'مشرف', department: 'عمليات', status: 'active', lastLogin: '2026-07-09 16:45' },
];

export default function UsersPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showPanel, setShowPanel] = useState(false);
  const [selectedUser, setSelectedUser] = useState<any>(null);

  const filtered = users.filter(u => !searchQuery || u.name.includes(searchQuery) || u.email.includes(searchQuery));

  const stats = [
    { title: 'إجمالي المستخدمين', value: users.length, icon: <Users size={20} />, color: 'blue' as const },
    { title: 'نشط', value: users.filter(u => u.status === 'active').length, icon: <CheckCircle size={20} />, color: 'green' as const },
    { title: 'غير نشط', value: users.filter(u => u.status === 'inactive').length, icon: <XCircle size={20} />, color: 'neutral' as const },
    { title: 'الأدوار', value: new Set(users.map(u => u.role)).size, icon: <Shield size={20} />, color: 'purple' as const },
  ];

  const columns = [
    { key: 'id', label: 'الرمز', sortable: true },
    { key: 'name', label: 'الاسم', sortable: true },
    { key: 'email', label: 'البريد', sortable: true },
    { key: 'role', label: 'الدور', sortable: true },
    { key: 'department', label: 'القسم', sortable: true },
    { key: 'lastLogin', label: 'آخر دخول', sortable: true },
    { key: 'status', label: 'الحالة', sortable: true, render: (v: string) => (
      <FluentBadge label={v === 'active' ? 'نشط' : 'غير نشط'} variant={v === 'active' ? 'success' : 'neutral'} size="small" />
    )},
  ];

  return (
    <div className="min-h-screen bg-[#faf9f8]">
      <FluentCommandBar
        title="المستخدمين"
        subtitle="User Management & Permissions"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: () => window.location.reload() },
          { id: 'export', label: 'تصدير', icon: <Download size={16} />, variant: 'secondary', onClick: () => exportToCsv(users, 'users.csv') },
          { id: 'roles', label: 'الأدوار', icon: <Shield size={16} />, variant: 'secondary' },
          { id: 'new', label: 'مستخدم جديد', icon: <Plus size={16} />, variant: 'primary', onClick: () => { setSelectedUser({}); setShowPanel(true); } },
        ]}
      />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {stats.map((stat) => <FluentStatsCard key={stat.title} {...stat} />)}
        </div>
        <FluentCard padding="small">
          <FluentSearchBox value={searchQuery} onChange={setSearchQuery} placeholder="البحث في المستخدمين..." className="w-80" />
        </FluentCard>
        <FluentTable
          title="قائمة المستخدمين"
          subtitle={`${filtered.length} مستخدم`}
          columns={columns}
          data={filtered}
          selectable
          onRowClick={(row) => { setSelectedUser(row); setShowPanel(true); }}
        />
      </div>
      <FluentPanel isOpen={showPanel} onClose={() => setShowPanel(false)} title={selectedUser?.name || 'تفاصيل المستخدم'} footer={
        <div className="flex items-center justify-end gap-2">
          <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إغلاق</button>
          <button className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>
      }>
        {selectedUser && (
          <div className="space-y-4">
            <FluentFormField label="الرمز"><FluentInput defaultValue={selectedUser.id} disabled /></FluentFormField>
            <FluentFormField label="الاسم الكامل"><FluentInput defaultValue={selectedUser.name} /></FluentFormField>
            <FluentFormField label="البريد الإلكتروني"><FluentInput defaultValue={selectedUser.email} /></FluentFormField>
            <FluentFormField label="الدور"><FluentSelect defaultValue={selectedUser.role}><option>مدير النظام</option><option>مدير مبيعات</option><option>محاسب</option><option>مهندس</option><option>مشرف</option></FluentSelect></FluentFormField>
            <FluentFormField label="القسم"><FluentSelect defaultValue={selectedUser.department}><option>تقنية</option><option>مبيعات</option><option>مالية</option><option>عمليات</option></FluentSelect></FluentFormField>
            <FluentFormField label="الحالة"><FluentSelect defaultValue={selectedUser.status}><option value="active">نشط</option><option value="inactive">غير نشط</option></FluentSelect></FluentFormField>
          </div>
        )}
      </FluentPanel>
    </div>
  );
}
