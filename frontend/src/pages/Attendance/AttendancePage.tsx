// pages/Attendance/AttendancePage.tsx
import { useEffect, useMemo, useState } from 'react';
import { Clock, RefreshCw, CalendarCheck, Timer } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { attendanceApi } from '../../services/api';

const statusMeta: Record<string, { label: string; variant: any }> = {
  present: { label: 'حاضر', variant: 'success' },
  late: { label: 'متأخر', variant: 'warning' },
  absent: { label: 'غائب', variant: 'error' },
  leave: { label: 'إجازة', variant: 'info' },
};

export default function AttendancePage() {
  const [tab, setTab] = useState<'attendance' | 'timesheets'>('attendance');
  const [attendance, setAttendance] = useState<any[]>([]);
  const [timesheets, setTimesheets] = useState<any[]>([]);
  const reload = () => {
    attendanceApi.attendance().then(setAttendance).catch(() => {});
    attendanceApi.timesheets().then(setTimesheets).catch(() => {});
  };
  useEffect(reload, []);

  const stats = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);
    const todayRows = attendance.filter((a) => a.date === today);
    return {
      present: todayRows.filter((a) => a.status === 'present').length,
      late: todayRows.filter((a) => a.status === 'late').length,
      totalHours: timesheets.reduce((s, t) => s + Number(t.hours || 0), 0),
    };
  }, [attendance, timesheets]);

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="الحضور وكشف الساعات" subtitle="Attendance & Timesheets"
        commands={[{ id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload }]} />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-3 gap-4">
          <FluentStatsCard title="حاضرون اليوم" value={stats.present} icon={<CalendarCheck size={20} />} color="green" />
          <FluentStatsCard title="متأخرون اليوم" value={stats.late} icon={<Clock size={20} />} color="orange" />
          <FluentStatsCard title="إجمالي الساعات المسجّلة" value={stats.totalHours} icon={<Timer size={20} />} color="blue" />
        </div>

        <div className="flex gap-1 border-b border-[#e1dfdd]">
          {[['attendance', 'الحضور والانصراف'], ['timesheets', 'كشف الساعات']].map(([id, label]) => (
            <button key={id} onClick={() => setTab(id as any)}
              className={`px-4 py-2 text-sm border-b-2 -mb-px ${tab === id ? 'border-[#0078d4] text-[#0078d4] font-medium' : 'border-transparent text-[#605e5c]'}`}>
              {label}
            </button>
          ))}
        </div>

        {tab === 'attendance' ? (
          <FluentTable
            title="سجل الحضور"
            subtitle={`${attendance.length} سجل`}
            columns={[
              { key: 'employee_name', label: 'الموظف', sortable: true },
              { key: 'date', label: 'التاريخ', sortable: true },
              { key: 'check_in', label: 'الحضور' },
              { key: 'check_out', label: 'الانصراف' },
              { key: 'hours', label: 'الساعات' },
              { key: 'status', label: 'الحالة', render: (v: string) => { const m = statusMeta[v]; return m ? <FluentBadge label={m.label} variant={m.variant} size="small" /> : v; } },
            ]}
            data={attendance}
          />
        ) : (
          <FluentTable
            title="كشف ساعات العمل"
            subtitle={`${timesheets.length} إدخال`}
            columns={[
              { key: 'employee_name', label: 'الموظف', sortable: true },
              { key: 'date', label: 'التاريخ', sortable: true },
              { key: 'project', label: 'المشروع' },
              { key: 'task', label: 'المهمة' },
              { key: 'hours', label: 'الساعات' },
              { key: 'billable', label: 'قابل للفوترة', render: (v: any) => (v ? '✓' : '—') },
            ]}
            data={timesheets}
          />
        )}
      </div>
    </div>
  );
}
