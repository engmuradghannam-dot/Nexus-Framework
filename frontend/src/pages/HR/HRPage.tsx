// pages/HR/HRPage.tsx
import { useState } from 'react';
import { ModuleForm } from '../../components/ModuleForm';
import { MODULE_FIELDS } from '../../config/moduleFields';
import { Users, Plus, RefreshCw, Download, Briefcase, Calendar, CheckCircle, Clock } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentSearchBox } from '../../components/FluentUI/FluentSearchBox';
import { FluentPanel, FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { exportToCsv } from '../../utils/exportCsv';

const employees = [
  { id: 'EMP-001', name: 'أحمد العلي', position: 'مدير تقني', department: 'تقنية', email: 'ahmed@company.com', phone: '+966 50 111 1111', status: 'active', joinDate: '2020-03-15' },
  { id: 'EMP-002', name: 'سارة أحمد', position: 'مديرة مبيعات', department: 'مبيعات', email: 'sara@company.com', phone: '+966 50 222 2222', status: 'active', joinDate: '2021-06-20' },
  { id: 'EMP-003', name: 'خالد السالم', position: 'محاسب', department: 'مالية', email: 'khaled@company.com', phone: '+966 50 333 3333', status: 'on_leave', joinDate: '2019-01-10' },
  { id: 'EMP-004', name: 'فاطمة حسن', position: 'مهندسة', department: 'تقنية', email: 'fatima@company.com', phone: '+966 50 444 4444', status: 'active', joinDate: '2022-09-01' },
  { id: 'EMP-005', name: 'عمر خالد', position: 'مشرف مستودع', department: 'عمليات', email: 'omar@company.com', phone: '+966 50 555 5555', status: 'terminated', joinDate: '2018-05-15' },
];

export default function HRPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showPanel, setShowPanel] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<any>(null);

  const filtered = employees.filter(e => !searchQuery || e.name.includes(searchQuery) || e.id.includes(searchQuery));

  const stats = [
    { title: 'إجمالي الموظفين', value: employees.length, icon: <Users size={20} />, color: 'blue' as const },
    { title: 'نشط', value: employees.filter(e => e.status === 'active').length, icon: <CheckCircle size={20} />, color: 'green' as const },
    { title: 'إجازة', value: employees.filter(e => e.status === 'on_leave').length, icon: <Calendar size={20} />, color: 'orange' as const },
    { title: 'الأقسام', value: new Set(employees.map(e => e.department)).size, icon: <Briefcase size={20} />, color: 'purple' as const },
  ];

  const columns = [
    { key: 'id', label: 'الرمز', sortable: true },
    { key: 'name', label: 'الاسم', sortable: true },
    { key: 'position', label: 'المنصب', sortable: true },
    { key: 'department', label: 'القسم', sortable: true },
    { key: 'email', label: 'البريد', sortable: true },
    { key: 'phone', label: 'الهاتف', sortable: true },
    { key: 'joinDate', label: 'تاريخ الانضمام', sortable: true },
    { key: 'status', label: 'الحالة', sortable: true, render: (v: string) => (
      <FluentBadge label={v === 'active' ? 'نشط' : v === 'on_leave' ? 'إجازة' : 'منتهي'} 
        variant={v === 'active' ? 'success' : v === 'on_leave' ? 'warning' : 'neutral'} size="small" />
    )},
  ];

  return (
    <div className="min-h-screen bg-[#faf9f8]">
      <FluentCommandBar
        title="الموارد البشرية"
        subtitle="Human Resources Management"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: () => window.location.reload() },
          { id: 'export', label: 'تصدير', icon: <Download size={16} />, variant: 'secondary', onClick: () => exportToCsv(employees, 'hr.csv') },
          { id: 'leave', label: 'طلب إجازة', icon: <Calendar size={16} />, variant: 'secondary' },
          { id: 'new', label: 'موظف جديد', icon: <Plus size={16} />, variant: 'primary', onClick: () => { setSelectedEmployee({}); setShowPanel(true); } },
        ]}
      />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {stats.map((stat) => <FluentStatsCard key={stat.title} {...stat} />)}
        </div>
        <FluentCard padding="small">
          <FluentSearchBox value={searchQuery} onChange={setSearchQuery} placeholder="البحث في الموظفين..." className="w-80" />
        </FluentCard>
        <FluentTable
          title="قائمة الموظفين"
          subtitle={`${filtered.length} موظف`}
          columns={columns}
          data={filtered}
          selectable
          onRowClick={(row) => { setSelectedEmployee(row); setShowPanel(true); }}
        />
      </div>
      <FluentPanel isOpen={showPanel} onClose={() => setShowPanel(false)} title={selectedEmployee?.name || 'تفاصيل الموظف'} footer={
        <div className="flex items-center justify-end gap-2">
          <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إغلاق</button>
          <button className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>
      }>
        {selectedEmployee && (
          <ModuleForm fields={MODULE_FIELDS.hr} value={selectedEmployee} onChange={setSelectedEmployee} />
        )}
      </FluentPanel>
    </div>
  );
}
