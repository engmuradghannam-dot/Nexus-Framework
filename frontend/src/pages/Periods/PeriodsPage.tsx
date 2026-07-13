// pages/Periods/PeriodsPage.tsx
import { useEffect, useState } from 'react';
import { CalendarClock, Plus, RefreshCw, Lock, Unlock, CheckCircle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput } from '../../components/FluentUI';
import { accountingApi } from '../../services/api';

export default function PeriodsPage() {
  const [periods, setPeriods] = useState<any[]>([]);
  const [showPanel, setShowPanel] = useState(false);
  const [form, setForm] = useState<any>({});
  const [msg, setMsg] = useState('');

  const reload = () => accountingApi.periods().then(setPeriods).catch(() => {});
  useEffect(reload, []);
  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));
  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(''), 4000); };

  const save = async () => {
    if (!form.name || !form.start_date || !form.end_date) return alert('أكمل الاسم والتواريخ');
    try { await accountingApi.createPeriod(form); setShowPanel(false); setForm({}); reload(); }
    catch { alert('تعذّر الحفظ'); }
  };
  const toggle = async (p: any) => {
    try {
      const r = p.status === 'closed' ? await accountingApi.reopenPeriod(p.id) : await accountingApi.closePeriod(p.id);
      flash(r.message); reload();
    } catch { alert('تعذّر التغيير'); }
  };

  const closed = periods.filter((p) => p.status === 'closed').length;

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="الفترات المحاسبية" subtitle="Accounting Periods — إقفال الفترات يمنع الترحيل بتاريخ ضمنها"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new', label: 'فترة جديدة', icon: <Plus size={16} />, variant: 'primary', onClick: () => { setForm({}); setShowPanel(true); } },
        ]} />
      <div className="p-6 space-y-6">
        {msg && <div className="flex items-center gap-2 rounded-md border border-[#107c10]/30 bg-[#f3faf3] px-4 py-2 text-sm text-[#107c10]"><CheckCircle size={16} /> {msg}</div>}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <FluentStatsCard title="إجمالي الفترات" value={periods.length} icon={<CalendarClock size={20} />} color="blue" />
          <FluentStatsCard title="مقفلة" value={closed} icon={<Lock size={20} />} color="red" />
          <FluentStatsCard title="مفتوحة" value={periods.length - closed} icon={<Unlock size={20} />} color="green" />
        </div>
        <FluentTable
          title="الفترات" subtitle={`${periods.length} فترة`}
          columns={[
            { key: 'name', label: 'الفترة' },
            { key: 'start_date', label: 'من' },
            { key: 'end_date', label: 'إلى' },
            { key: 'status', label: 'الحالة', render: (v: string) => <FluentBadge label={v === 'closed' ? 'مقفلة' : 'مفتوحة'} variant={v === 'closed' ? 'error' : 'success'} size="small" /> },
            { key: '__act', label: '', render: (_: any, p: any) => (
              <button onClick={(e) => { e.stopPropagation(); toggle(p); }}
                className={`flex items-center gap-1 text-xs px-2 py-1 rounded border ${p.status === 'closed' ? 'text-[#107c10] border-[#107c10] hover:bg-[#f3faf3]' : 'text-[#a4262c] border-[#a4262c] hover:bg-[#fdf3f4]'}`}>
                {p.status === 'closed' ? <><Unlock size={12} /> فتح</> : <><Lock size={12} /> إقفال</>}
              </button>
            ) },
          ]}
          data={periods}
          emptyMessage="لا فترات — أنشئ فترة (مثلاً شهرية) لتتحكّم بالإقفال"
        />
      </div>
      <FluentPanel isOpen={showPanel} onClose={() => setShowPanel(false)} title="فترة محاسبية جديدة"
        footer={<div className="flex gap-2 justify-end"><button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm border border-[#8a8886] rounded-sm">إلغاء</button><button onClick={save} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm">حفظ</button></div>}>
        <div className="space-y-3">
          <FluentFormField label="اسم الفترة"><FluentInput value={form.name || ''} onChange={(e) => set('name', e.target.value)} placeholder="2026-01 / يناير 2026" /></FluentFormField>
          <FluentFormField label="من تاريخ"><FluentInput type="date" value={form.start_date || ''} onChange={(e) => set('start_date', e.target.value)} /></FluentFormField>
          <FluentFormField label="إلى تاريخ"><FluentInput type="date" value={form.end_date || ''} onChange={(e) => set('end_date', e.target.value)} /></FluentFormField>
          <p className="text-xs text-[#605e5c]">بعد الإقفال، يُرفض أي ترحيل (فاتورة/دفعة/إشعار دائن/إلغاء/عكس قيد) بتاريخ ضمن الفترة.</p>
        </div>
      </FluentPanel>
    </div>
  );
}
