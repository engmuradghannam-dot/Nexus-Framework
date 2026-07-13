// pages/HRExtras/HRExtrasPage.tsx
import { useEffect, useState } from 'react';
import { Users, Plus, RefreshCw, Check, Wallet, Calculator, Briefcase, Star } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { hrExtrasApi } from '../../services/api';

const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const TABS = [['claims', 'المصاريف'], ['loans', 'السلف'], ['eos', 'نهاية الخدمة'], ['recruit', 'التوظيف'], ['appraisal', 'التقييم']];

export default function HRExtrasPage() {
  const [tab, setTab] = useState('claims');
  const [claims, setClaims] = useState<any[]>([]);
  const [loans, setLoans] = useState<any[]>([]);
  const [openings, setOpenings] = useState<any[]>([]);
  const [applicants, setApplicants] = useState<any[]>([]);
  const [selOpening, setSelOpening] = useState<any>(null);
  const [appraisals, setAppraisals] = useState<any[]>([]);
  const [panel, setPanel] = useState<string | null>(null);
  const [form, setForm] = useState<any>({});
  const [eos, setEos] = useState<any>({ last_wage: 10000, years: 5, reason: 'termination' });
  const [eosResult, setEosResult] = useState<number | null>(null);

  const reload = () => {
    hrExtrasApi.claims().then(setClaims).catch(() => {});
    hrExtrasApi.loans().then(setLoans).catch(() => {});
    hrExtrasApi.openings().then((o) => { setOpenings(o); if (o[0]) pickOpening(o[0]); }).catch(() => {});
    hrExtrasApi.appraisals().then(setAppraisals).catch(() => {});
  };
  useEffect(reload, []);
  const pickOpening = (o: any) => { setSelOpening(o); hrExtrasApi.applicants(o.id).then(setApplicants).catch(() => {}); };
  useEffect(() => { hrExtrasApi.eos(eos).then((r) => setEosResult(r.gratuity)).catch(() => setEosResult(null)); }, [eos]);
  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));

  const save = async () => {
    try {
      if (panel === 'claim') await hrExtrasApi.createClaim(form);
      else if (panel === 'loan') await hrExtrasApi.createLoan(form);
      else if (panel === 'opening') await hrExtrasApi.createOpening(form);
      else if (panel === 'applicant') await hrExtrasApi.createApplicant({ ...form, opening: selOpening.id });
      else if (panel === 'appraisal') await hrExtrasApi.createAppraisal(form);
      setPanel(null); setForm({}); reload();
    } catch { alert('تعذّر الحفظ'); }
  };
  const approve = async (id: number, status: string) => { await hrExtrasApi.claimStatus(id, status); reload(); };
  const pay = async (id: number) => { await hrExtrasApi.payInstallment(id); reload(); };

  const claimStatus: Record<string, any> = { pending: ['warning', 'معلّق'], approved: ['info', 'معتمد'], rejected: ['error', 'مرفوض'], paid: ['success', 'مدفوع'] };
  const newBtn = (p: string) => ({ id: 'new', label: 'إضافة', icon: <Plus size={16} />, variant: 'primary' as const, onClick: () => { setForm({}); setPanel(p); } });

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="شؤون الموظفين" subtitle="HR — مصاريف · سلف · نهاية خدمة · توظيف · تقييم"
        commands={[{ id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          ...(tab === 'claims' ? [newBtn('claim')] : tab === 'loans' ? [newBtn('loan')] : tab === 'recruit' ? [newBtn('opening')] : tab === 'appraisal' ? [newBtn('appraisal')] : [])]} />
      <div className="p-6 space-y-6">
        <div className="flex gap-1 border-b border-[#e1dfdd] flex-wrap">
          {TABS.map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)} className={`px-4 py-2 text-sm border-b-2 -mb-px ${tab === id ? 'border-[#0078d4] text-[#0078d4] font-medium' : 'border-transparent text-[#605e5c]'}`}>{label}</button>
          ))}
        </div>

        {tab === 'claims' && (
          <FluentTable title="مطالبات المصاريف" subtitle={`${claims.length} مطالبة`}
            columns={[
              { key: 'employee_name', label: 'الموظف' }, { key: 'date', label: 'التاريخ' }, { key: 'category', label: 'الفئة' },
              { key: 'amount', label: 'المبلغ', render: (v: any) => fmt(v) },
              { key: 'status', label: 'الحالة', render: (v: string) => { const m = claimStatus[v]; return <FluentBadge label={m[1]} variant={m[0]} size="small" />; } },
              { key: '__act', label: '', render: (_: any, r: any) => r.status === 'pending' ? <div className="flex gap-1"><button onClick={(e) => { e.stopPropagation(); approve(r.id, 'approved'); }} className="text-xs text-white bg-[#107c10] px-2 py-1 rounded">اعتماد</button><button onClick={(e) => { e.stopPropagation(); approve(r.id, 'rejected'); }} className="text-xs text-[#a4262c]">رفض</button></div> : r.status === 'approved' ? <button onClick={(e) => { e.stopPropagation(); approve(r.id, 'paid'); }} className="text-xs text-white bg-[#0078d4] px-2 py-1 rounded">صرف</button> : null },
            ]} data={claims} />
        )}
        {tab === 'loans' && (
          <FluentTable title="سلف الموظفين" subtitle={`${loans.length} سلفة`}
            columns={[
              { key: 'employee_name', label: 'الموظف' }, { key: 'amount', label: 'المبلغ', render: (v: any) => fmt(v) },
              { key: 'monthly', label: 'القسط الشهري', render: (v: any) => fmt(v) },
              { key: 'paid_installments', label: 'المدفوع', render: (v: any, r: any) => `${v}/${r.installments}` },
              { key: 'remaining', label: 'المتبقّي', render: (v: any) => <span className="font-semibold">{fmt(v)}</span> },
              { key: 'status', label: 'الحالة', render: (v: string) => <FluentBadge label={v === 'active' ? 'نشطة' : 'مسدّدة'} variant={v === 'active' ? 'info' : 'success'} size="small" /> },
              { key: '__pay', label: '', render: (_: any, r: any) => r.status === 'active' ? <button onClick={(e) => { e.stopPropagation(); pay(r.id); }} className="flex items-center gap-1 text-xs text-white bg-[#0078d4] px-2 py-1 rounded"><Check size={12} /> سداد قسط</button> : <span className="text-xs text-[#107c10]">✓</span> },
            ]} data={loans} />
        )}
        {tab === 'eos' && (
          <FluentCard>
            <h3 className="text-sm font-semibold text-[#323130] mb-3 flex items-center gap-2"><Calculator size={16} /> حاسبة مكافأة نهاية الخدمة (نظام العمل السعودي)</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
              <FluentFormField label="آخر راتب"><FluentInput type="number" value={eos.last_wage} onChange={(e) => setEos((s: any) => ({ ...s, last_wage: e.target.value }))} /></FluentFormField>
              <FluentFormField label="سنوات الخدمة"><FluentInput type="number" value={eos.years} onChange={(e) => setEos((s: any) => ({ ...s, years: e.target.value }))} /></FluentFormField>
              <FluentFormField label="سبب انتهاء العقد">
                <FluentSelect value={eos.reason} onChange={(e) => setEos((s: any) => ({ ...s, reason: e.target.value }))}>
                  <option value="termination">إنهاء من صاحب العمل</option><option value="resignation">استقالة</option>
                </FluentSelect>
              </FluentFormField>
              <div className="rounded-md bg-[#eff6fc] p-3 text-center">
                <div className="text-xs text-[#605e5c]">المكافأة المستحقّة</div>
                <div className="text-xl font-bold text-[#0078d4]">{eosResult !== null ? fmt(eosResult) : '—'}</div>
                <div className="text-[10px] text-[#605e5c]">ر.س</div>
              </div>
            </div>
            <p className="text-xs text-[#605e5c] mt-3">نصف شهر عن كل سنة من أول 5 سنوات، وشهر كامل عمّا زاد. الاستقالة تُخفّض المكافأة حسب مدة الخدمة.</p>
          </FluentCard>
        )}
        {tab === 'recruit' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <FluentCard>
              <h3 className="text-sm font-semibold text-[#605e5c] mb-3">الوظائف الشاغرة</h3>
              <div className="space-y-1">
                {openings.map((o) => (
                  <button key={o.id} onClick={() => pickOpening(o)} className={`w-full text-right px-3 py-2 rounded-md text-sm ${selOpening?.id === o.id ? 'bg-[#eff6fc] text-[#0078d4] font-medium' : 'hover:bg-[#f3f2f1]'}`}>
                    <div className="flex items-center gap-1"><Briefcase size={13} /> {o.title}</div>
                    <div className="text-xs text-[#605e5c]">{o.department} — {o.applicant_count} متقدّم</div>
                  </button>
                ))}
              </div>
            </FluentCard>
            <div className="lg:col-span-2">
              <FluentTable title={`المتقدّمون${selOpening ? ` — ${selOpening.title}` : ''}`} subtitle={`${applicants.length} متقدّم`}
                commands={selOpening ? [{ id: 'add', label: 'متقدّم', icon: <Plus size={14} />, onClick: () => { setForm({}); setPanel('applicant'); } }] : []}
                columns={[
                  { key: 'name', label: 'الاسم' }, { key: 'email', label: 'البريد' },
                  { key: 'stage', label: 'المرحلة', render: (v: string) => <FluentBadge label={v} variant="info" size="small" /> },
                  { key: 'rating', label: 'التقييم', render: (v: number) => '★'.repeat(v) + '☆'.repeat(5 - v) },
                ]} data={applicants} />
            </div>
          </div>
        )}
        {tab === 'appraisal' && (
          <FluentTable title="تقييمات الأداء" subtitle={`${appraisals.length} تقييم`}
            columns={[
              { key: 'employee_name', label: 'الموظف' }, { key: 'period', label: 'الفترة' },
              { key: 'score', label: 'الدرجة', render: (v: any) => <span className="flex items-center gap-1"><Star size={12} className="text-[#ffb900]" /> {v}/5</span> },
              { key: 'goals', label: 'الأهداف' },
            ]} data={appraisals} />
        )}
      </div>

      <FluentPanel isOpen={!!panel} onClose={() => setPanel(null)} title="إضافة"
        footer={<div className="flex gap-2 justify-end"><button onClick={() => setPanel(null)} className="px-4 py-2 text-sm border border-[#8a8886] rounded-sm">إلغاء</button><button onClick={save} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm">حفظ</button></div>}>
        <div className="space-y-3">
          {panel === 'claim' && <>
            <FluentFormField label="الموظف"><FluentInput value={form.employee_name || ''} onChange={(e) => set('employee_name', e.target.value)} /></FluentFormField>
            <FluentFormField label="التاريخ"><FluentInput type="date" value={form.date || ''} onChange={(e) => set('date', e.target.value)} /></FluentFormField>
            <FluentFormField label="الفئة"><FluentInput value={form.category || ''} onChange={(e) => set('category', e.target.value)} /></FluentFormField>
            <FluentFormField label="المبلغ"><FluentInput type="number" value={form.amount || ''} onChange={(e) => set('amount', e.target.value)} /></FluentFormField>
          </>}
          {panel === 'loan' && <>
            <FluentFormField label="الموظف"><FluentInput value={form.employee_name || ''} onChange={(e) => set('employee_name', e.target.value)} /></FluentFormField>
            <FluentFormField label="المبلغ"><FluentInput type="number" value={form.amount || ''} onChange={(e) => set('amount', e.target.value)} /></FluentFormField>
            <FluentFormField label="عدد الأقساط"><FluentInput type="number" value={form.installments || ''} onChange={(e) => set('installments', e.target.value)} /></FluentFormField>
            <FluentFormField label="تاريخ البدء"><FluentInput type="date" value={form.start_date || ''} onChange={(e) => set('start_date', e.target.value)} /></FluentFormField>
          </>}
          {panel === 'opening' && <>
            <FluentFormField label="المسمّى الوظيفي"><FluentInput value={form.title || ''} onChange={(e) => set('title', e.target.value)} /></FluentFormField>
            <FluentFormField label="القسم"><FluentInput value={form.department || ''} onChange={(e) => set('department', e.target.value)} /></FluentFormField>
            <FluentFormField label="الموقع"><FluentInput value={form.location || ''} onChange={(e) => set('location', e.target.value)} /></FluentFormField>
            <FluentFormField label="عدد الشواغر"><FluentInput type="number" value={form.openings || ''} onChange={(e) => set('openings', e.target.value)} /></FluentFormField>
          </>}
          {panel === 'applicant' && <>
            <FluentFormField label="اسم المتقدّم"><FluentInput value={form.name || ''} onChange={(e) => set('name', e.target.value)} /></FluentFormField>
            <FluentFormField label="البريد"><FluentInput value={form.email || ''} onChange={(e) => set('email', e.target.value)} /></FluentFormField>
            <FluentFormField label="الهاتف"><FluentInput value={form.phone || ''} onChange={(e) => set('phone', e.target.value)} /></FluentFormField>
          </>}
          {panel === 'appraisal' && <>
            <FluentFormField label="الموظف"><FluentInput value={form.employee_name || ''} onChange={(e) => set('employee_name', e.target.value)} /></FluentFormField>
            <FluentFormField label="الفترة"><FluentInput value={form.period || ''} onChange={(e) => set('period', e.target.value)} placeholder="2025-H2" /></FluentFormField>
            <FluentFormField label="الدرجة (0-5)"><FluentInput type="number" value={form.score || ''} onChange={(e) => set('score', e.target.value)} /></FluentFormField>
            <FluentFormField label="الأهداف"><FluentInput value={form.goals || ''} onChange={(e) => set('goals', e.target.value)} /></FluentFormField>
          </>}
        </div>
      </FluentPanel>
    </div>
  );
}
