// pages/HR/HRPage.tsx
import { useEffect, useMemo, useState } from 'react';
import { Users, Plus, RefreshCw, CalendarClock, Wallet, Check, X, AlertTriangle, CheckCircle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { hrApi } from '../../services/api';

const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const LEAVE_STATUS_LABEL: Record<string, string> = { Pending: 'قيد الانتظار', Approved: 'موافَق عليها', Rejected: 'مرفوضة', Cancelled: 'ملغاة' };
const LEAVE_STATUS_VARIANT: Record<string, any> = { Pending: 'warning', Approved: 'success', Rejected: 'error', Cancelled: 'error' };
const PAYROLL_STATUS_LABEL: Record<string, string> = { Draft: 'مسودة', Approved: 'معتمد', Paid: 'مصروف', Cancelled: 'ملغى' };
const PAYROLL_STATUS_VARIANT: Record<string, any> = { Draft: 'warning', Approved: 'info', Paid: 'success', Cancelled: 'error' };

export default function HRPage() {
  const [employees, setEmployees] = useState<any[]>([]);
  const [leaves, setLeaves] = useState<any[]>([]);
  const [payrolls, setPayrolls] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const [empPanel, setEmpPanel] = useState(false);
  const [newEmp, setNewEmp] = useState<any>({});
  const [leavePanel, setLeavePanel] = useState(false);
  const [newLeave, setNewLeave] = useState<any>({});
  const [payPanel, setPayPanel] = useState(false);
  const [newPay, setNewPay] = useState<any>({});

  const reload = () => {
    setLoading(true);
    Promise.all([hrApi.employees(), hrApi.leaveRequests(), hrApi.payrolls()])
      .then(([e, l, p]) => { setEmployees(e); setLeaves(l); setPayrolls(p); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(reload, []);

  const stats = useMemo(() => ({
    employees: employees.length,
    pendingLeaves: leaves.filter((l) => l.status === 'Pending').length,
    payrollDue: payrolls.filter((p) => p.status === 'Approved').reduce((s, p) => s + Number(p.net_salary || 0), 0),
  }), [employees, leaves, payrolls]);

  const openNewEmp = () => { setNewEmp({ employee_id: '', first_name: '', last_name: '' }); setError(''); setEmpPanel(true); };
  const saveEmp = async () => {
    try { await hrApi.createEmployee(newEmp); setEmpPanel(false); reload(); }
    catch (e: any) { setError(formatApiError(e)); }
  };

  const openNewLeave = () => { setNewLeave({ employee: '', leave_type: 'Annual' }); setError(''); setLeavePanel(true); };
  const saveLeave = async () => {
    try { await hrApi.createLeaveRequest(newLeave); setLeavePanel(false); reload(); }
    catch (e: any) { setError(formatApiError(e)); }
  };
  const decideLeave = async (id: number, status: string) => {
    try { await hrApi.updateLeaveRequest(id, { status }); setNotice(status === 'Approved' ? 'تمت الموافقة على الإجازة.' : 'تم رفض الإجازة.'); reload(); }
    catch (e: any) { setError(formatApiError(e)); }
  };

  const openNewPay = () => { setNewPay({ employee: '', pay_period_start: '', pay_period_end: '', basic_salary: 0 }); setError(''); setPayPanel(true); };
  const savePay = async () => {
    try { await hrApi.createPayroll(newPay); setPayPanel(false); reload(); }
    catch (e: any) { setError(formatApiError(e)); }
  };
  const advancePayroll = async (id: number, status: string) => {
    try { await hrApi.updatePayroll(id, { status }); setNotice(status === 'Paid' ? 'تم صرف الراتب.' : 'تم اعتماد الراتب.'); reload(); }
    catch (e: any) { setError(formatApiError(e)); }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar
        title="الموارد البشرية" subtitle="HR — الموظفون والإجازات والرواتب"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new-emp', label: 'موظف جديد', icon: <Plus size={16} />, variant: 'primary', onClick: openNewEmp },
        ]}
      />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-3 gap-4">
          <FluentStatsCard title="عدد الموظفين" value={stats.employees} icon={<Users size={20} />} color="blue" />
          <FluentStatsCard title="إجازات قيد الانتظار" value={stats.pendingLeaves} icon={<CalendarClock size={20} />} color="orange" />
          <FluentStatsCard title="رواتب معتمدة بانتظار الصرف" value={fmt(stats.payrollDue)} icon={<Wallet size={20} />} color="purple" />
        </div>

        {notice && <div className="flex items-center gap-2 rounded-md border border-[#107c10]/30 bg-[#f3faf3] px-3 py-2 text-sm text-[#107c10]"><CheckCircle size={16} /> {notice}</div>}

        <FluentTable
          title="الموظفون"
          subtitle={loading ? 'جارٍ التحميل…' : `${employees.length} موظف`}
          columns={[
            { key: 'employee_id', label: 'الرقم الوظيفي', sortable: true },
            { key: 'full_name', label: 'الاسم' },
            { key: 'department_name', label: 'القسم' },
            { key: 'job_title', label: 'المسمى الوظيفي' },
            { key: 'status', label: 'الحالة', render: (v: string) => <FluentBadge label={v === 'Active' ? 'نشط' : v} variant={v === 'Active' ? 'success' : 'warning'} size="small" /> },
          ]}
          data={employees}
        />

        <FluentTable
          title="طلبات الإجازة"
          subtitle={loading ? 'جارٍ التحميل…' : `${leaves.length} طلب`}
          columns={[
            { key: 'employee_name', label: 'الموظف' },
            { key: 'leave_type', label: 'النوع' },
            { key: 'start_date', label: 'من' },
            { key: 'end_date', label: 'إلى' },
            { key: 'duration_days', label: 'المدة (يوم)' },
            { key: 'status', label: 'الحالة', render: (v: string) => <FluentBadge label={LEAVE_STATUS_LABEL[v] || v} variant={LEAVE_STATUS_VARIANT[v] || 'info'} size="small" /> },
            {
              key: '__decide', label: '', render: (_: any, row: any) => (
                row.status === 'Pending' ? (
                  <div className="flex items-center gap-1 justify-end">
                    <button onClick={(e) => { e.stopPropagation(); decideLeave(row.id, 'Approved'); }} className="flex items-center gap-1 text-xs text-white bg-[#107c10] px-2 py-1 rounded hover:bg-[#0e6e0e]"><Check size={12} /> موافقة</button>
                    <button onClick={(e) => { e.stopPropagation(); decideLeave(row.id, 'Rejected'); }} className="flex items-center gap-1 text-xs text-[#a4262c] border border-[#a4262c] px-2 py-1 rounded hover:bg-[#fdf2f2]"><X size={12} /> رفض</button>
                  </div>
                ) : null
              ),
            },
          ]}
          data={leaves}
        />
        <div className="flex justify-end -mt-4">
          <button onClick={openNewLeave} className="flex items-center gap-1 text-sm text-[#0078d4] hover:underline"><Plus size={14} /> طلب إجازة جديد</button>
        </div>

        <FluentTable
          title="الرواتب"
          subtitle={loading ? 'جارٍ التحميل…' : `${payrolls.length} سجل`}
          columns={[
            { key: 'employee_name', label: 'الموظف' },
            { key: 'pay_period_start', label: 'من' },
            { key: 'pay_period_end', label: 'إلى' },
            { key: 'gross_salary', label: 'الإجمالي', render: (v: any) => fmt(v) },
            { key: 'total_deductions', label: 'الاستقطاعات', render: (v: any) => fmt(v) },
            { key: 'net_salary', label: 'الصافي', render: (v: any) => fmt(v) },
            { key: 'status', label: 'الحالة', render: (v: string) => <FluentBadge label={PAYROLL_STATUS_LABEL[v] || v} variant={PAYROLL_STATUS_VARIANT[v] || 'info'} size="small" /> },
            {
              key: '__advance', label: '', render: (_: any, row: any) => (
                row.status === 'Draft' ? (
                  <button onClick={(e) => { e.stopPropagation(); advancePayroll(row.id, 'Approved'); }} className="text-xs text-white bg-[#0078d4] px-2 py-1 rounded hover:bg-[#106ebe]">اعتماد</button>
                ) : row.status === 'Approved' ? (
                  <button onClick={(e) => { e.stopPropagation(); advancePayroll(row.id, 'Paid'); }} className="text-xs text-white bg-[#107c10] px-2 py-1 rounded hover:bg-[#0e6e0e]">صرف</button>
                ) : null
              ),
            },
          ]}
          data={payrolls}
        />
        <div className="flex justify-end -mt-4">
          <button onClick={openNewPay} className="flex items-center gap-1 text-sm text-[#0078d4] hover:underline"><Plus size={14} /> سجل راتب جديد</button>
        </div>
      </div>

      <FluentPanel isOpen={empPanel} onClose={() => setEmpPanel(false)} title="موظف جديد"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setEmpPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={saveEmp} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        {error && <div className="mb-4 flex items-start gap-2 rounded-md border border-[#a4262c]/30 bg-[#fdf2f2] px-3 py-2 text-sm text-[#a4262c]"><AlertTriangle size={16} className="mt-0.5 shrink-0" /> {error}</div>}
        <div className="space-y-3">
          <FluentFormField label="الرقم الوظيفي" required><FluentInput value={newEmp.employee_id || ''} onChange={(e) => setNewEmp({ ...newEmp, employee_id: e.target.value })} placeholder="EMP-001" /></FluentFormField>
          <FluentFormField label="الاسم الأول" required><FluentInput value={newEmp.first_name || ''} onChange={(e) => setNewEmp({ ...newEmp, first_name: e.target.value })} /></FluentFormField>
          <FluentFormField label="اسم العائلة" required><FluentInput value={newEmp.last_name || ''} onChange={(e) => setNewEmp({ ...newEmp, last_name: e.target.value })} /></FluentFormField>
          <FluentFormField label="المسمى الوظيفي"><FluentInput value={newEmp.job_title || ''} onChange={(e) => setNewEmp({ ...newEmp, job_title: e.target.value })} /></FluentFormField>
          <FluentFormField label="البريد الإلكتروني"><FluentInput type="email" value={newEmp.email || ''} onChange={(e) => setNewEmp({ ...newEmp, email: e.target.value })} /></FluentFormField>
        </div>
      </FluentPanel>

      <FluentPanel isOpen={leavePanel} onClose={() => setLeavePanel(false)} title="طلب إجازة جديد"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setLeavePanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={saveLeave} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        {error && <div className="mb-4 flex items-start gap-2 rounded-md border border-[#a4262c]/30 bg-[#fdf2f2] px-3 py-2 text-sm text-[#a4262c]"><AlertTriangle size={16} className="mt-0.5 shrink-0" /> {error}</div>}
        <div className="space-y-3">
          <FluentFormField label="الموظف" required>
            <FluentSelect value={newLeave.employee || ''} onChange={(e) => setNewLeave({ ...newLeave, employee: e.target.value })}>
              <option value="">— اختر موظفاً —</option>
              {employees.map((e) => <option key={e.id} value={e.id}>{e.full_name}</option>)}
            </FluentSelect>
          </FluentFormField>
          <FluentFormField label="نوع الإجازة">
            <FluentSelect value={newLeave.leave_type || 'Annual'} onChange={(e) => setNewLeave({ ...newLeave, leave_type: e.target.value })}>
              <option value="Annual">سنوية</option>
              <option value="Sick">مرضية</option>
              <option value="Unpaid">بدون راتب</option>
              <option value="Emergency">طارئة</option>
            </FluentSelect>
          </FluentFormField>
          <FluentFormField label="من تاريخ" required><FluentInput type="date" value={newLeave.start_date || ''} onChange={(e) => setNewLeave({ ...newLeave, start_date: e.target.value })} /></FluentFormField>
          <FluentFormField label="إلى تاريخ" required><FluentInput type="date" value={newLeave.end_date || ''} onChange={(e) => setNewLeave({ ...newLeave, end_date: e.target.value })} /></FluentFormField>
        </div>
      </FluentPanel>

      <FluentPanel isOpen={payPanel} onClose={() => setPayPanel(false)} title="سجل راتب جديد"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setPayPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={savePay} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        {error && <div className="mb-4 flex items-start gap-2 rounded-md border border-[#a4262c]/30 bg-[#fdf2f2] px-3 py-2 text-sm text-[#a4262c]"><AlertTriangle size={16} className="mt-0.5 shrink-0" /> {error}</div>}
        <div className="space-y-3">
          <FluentFormField label="الموظف" required>
            <FluentSelect value={newPay.employee || ''} onChange={(e) => setNewPay({ ...newPay, employee: e.target.value })}>
              <option value="">— اختر موظفاً —</option>
              {employees.map((e) => <option key={e.id} value={e.id}>{e.full_name}</option>)}
            </FluentSelect>
          </FluentFormField>
          <FluentFormField label="بداية الفترة" required><FluentInput type="date" value={newPay.pay_period_start || ''} onChange={(e) => setNewPay({ ...newPay, pay_period_start: e.target.value })} /></FluentFormField>
          <FluentFormField label="نهاية الفترة" required><FluentInput type="date" value={newPay.pay_period_end || ''} onChange={(e) => setNewPay({ ...newPay, pay_period_end: e.target.value })} /></FluentFormField>
          <FluentFormField label="الراتب الأساسي"><FluentInput type="number" step="0.01" value={newPay.basic_salary || 0} onChange={(e) => setNewPay({ ...newPay, basic_salary: e.target.value })} /></FluentFormField>
          <FluentFormField label="بدل السكن"><FluentInput type="number" step="0.01" value={newPay.housing_allowance || 0} onChange={(e) => setNewPay({ ...newPay, housing_allowance: e.target.value })} /></FluentFormField>
        </div>
      </FluentPanel>
    </div>
  );
}

function formatApiError(e: any): string {
  const data = e?.response?.data;
  if (!data) return 'حدث خطأ غير متوقع.';
  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  const parts: string[] = [];
  for (const [k, v] of Object.entries(data)) {
    parts.push(Array.isArray(v) ? v.join(' ') : String(v));
  }
  return parts.join(' — ') || 'حدث خطأ غير متوقع.';
}
