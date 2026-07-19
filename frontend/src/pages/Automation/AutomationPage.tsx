// pages/Automation/AutomationPage.tsx
import { useEffect, useState } from 'react';
import { Clock, Plus, RefreshCw, Play, Webhook as WebhookIcon, Zap, CheckCircle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { automationApi } from '../../services/api';

const freqLabel: Record<string, string> = { hourly: 'كل ساعة', daily: 'يومي', weekly: 'أسبوعي', monthly: 'شهري' };
const jobTypeLabel: Record<string, string> = { report: 'تقرير', notification: 'إشعار', cleanup: 'أرشفة', sync: 'مزامنة', custom: 'مخصّص' };
const dt = (v: string) => v ? new Date(v).toLocaleString('en-GB') : '—';

export default function AutomationPage() {
  const [tab, setTab] = useState<'jobs' | 'webhooks' | 'deliveries'>('jobs');
  const [jobs, setJobs] = useState<any[]>([]);
  const [webhooks, setWebhooks] = useState<any[]>([]);
  const [deliveries, setDeliveries] = useState<any[]>([]);
  const [panel, setPanel] = useState<string | null>(null);
  const [form, setForm] = useState<any>({});
  const [msg, setMsg] = useState('');

  const reload = () => {
    automationApi.jobs().then(setJobs).catch(() => {});
    automationApi.webhooks().then(setWebhooks).catch(() => {});
    automationApi.deliveries().then(setDeliveries).catch(() => {});
  };
  useEffect(reload, []);
  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));
  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(''), 4500); };

  const runJob = async (id: number) => { const r = await automationApi.runJob(id); flash(r.message); reload(); };
  const triggerWebhook = async (id: number) => { const r = await automationApi.triggerWebhook(id, { event: 'manual.test', ts: Date.now() }); flash(r.status === 'success' ? `تم الإرسال (${r.status_code})` : `فشل الإرسال: ${r.error || ''}`.slice(0, 80)); setTab('deliveries'); reload(); };
  const save = async () => {
    try {
      if (panel === 'job') await automationApi.createJob({ ...form, job_type: form.job_type || 'custom', frequency: form.frequency || 'daily' });
      else await automationApi.createWebhook(form);
      setPanel(null); setForm({}); reload();
    } catch { alert('تعذّر الحفظ'); }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="الأتمتة" subtitle="Automation — مهام مجدولة و Webhooks"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          ...(tab === 'jobs' ? [{ id: 'nj', label: 'مهمة جديدة', icon: <Plus size={16} />, variant: 'primary' as const, onClick: () => { setForm({}); setPanel('job'); } }]
            : tab === 'webhooks' ? [{ id: 'nw', label: 'Webhook جديد', icon: <Plus size={16} />, variant: 'primary' as const, onClick: () => { setForm({}); setPanel('webhook'); } }] : []),
        ]} />
      <div className="p-6 space-y-6">
        {msg && <div className="flex items-center gap-2 rounded-md border border-[#107c10]/30 bg-[#f3faf3] px-4 py-2 text-sm text-[#107c10]"><CheckCircle size={16} /> {msg}</div>}
        <div className="flex gap-1 border-b border-[#e1dfdd]">
          {[['jobs', 'المهام المجدولة'], ['webhooks', 'Webhooks'], ['deliveries', 'سجل الإرسال']].map(([id, label]) => (
            <button key={id} onClick={() => setTab(id as any)} className={`px-4 py-2 text-sm border-b-2 -mb-px ${tab === id ? 'border-[#0078d4] text-[#0078d4] font-medium' : 'border-transparent text-[#605e5c]'}`}>{label}</button>
          ))}
        </div>

        {tab === 'jobs' && (
          <FluentTable title="المهام المجدولة" subtitle={`${jobs.length} مهمة`}
            columns={[
              { key: 'name', label: 'المهمة' },
              { key: 'job_type', label: 'النوع', render: (v: string) => <FluentBadge label={jobTypeLabel[v] || v} variant="info" size="small" /> },
              { key: 'frequency', label: 'التكرار', render: (v: string) => freqLabel[v] || v },
              { key: 'last_run', label: 'آخر تشغيل', render: dt },
              { key: 'next_run', label: 'التشغيل القادم', render: dt },
              { key: 'run_count', label: 'مرات التشغيل' },
              { key: 'is_active', label: 'الحالة', render: (v: boolean) => <FluentBadge label={v ? 'نشطة' : 'متوقّفة'} variant={v ? 'success' : 'neutral'} size="small" /> },
              { key: '__run', label: '', render: (_: any, r: any) => <button onClick={(e) => { e.stopPropagation(); runJob(r.id); }} className="flex items-center gap-1 text-xs text-white bg-[#0078d4] px-2 py-1 rounded hover:bg-[#106ebe]"><Play size={12} /> شغّل الآن</button> },
            ]} data={jobs} />
        )}
        {tab === 'webhooks' && (
          <FluentTable title="Webhooks" subtitle={`${webhooks.length} خطّاف`}
            columns={[
              { key: 'name', label: 'الاسم' },
              { key: 'event', label: 'الحدث', render: (v: string) => <code className="text-xs bg-[#f3f2f1] px-1.5 py-0.5 rounded">{v}</code> },
              { key: 'target_url', label: 'الوجهة', render: (v: string) => <span className="text-xs text-[#605e5c]">{(v || '').slice(0, 40)}</span> },
              { key: 'delivery_count', label: 'الإرساليات' },
              { key: 'is_active', label: 'الحالة', render: (v: boolean) => <FluentBadge label={v ? 'نشط' : 'متوقّف'} variant={v ? 'success' : 'neutral'} size="small" /> },
              { key: '__t', label: '', render: (_: any, r: any) => <button onClick={(e) => { e.stopPropagation(); triggerWebhook(r.id); }} className="flex items-center gap-1 text-xs text-white bg-[#0078d4] px-2 py-1 rounded hover:bg-[#106ebe]"><Zap size={12} /> اختبار</button> },
            ]} data={webhooks} />
        )}
        {tab === 'deliveries' && (
          <FluentTable title="سجل إرسال Webhooks" subtitle={`${deliveries.length} محاولة`}
            columns={[
              { key: 'created_at', label: 'التاريخ', render: dt },
              { key: 'webhook_name', label: 'الخطّاف' },
              { key: 'event', label: 'الحدث', render: (v: string) => <code className="text-xs">{v}</code> },
              { key: 'status', label: 'النتيجة', render: (v: string) => <FluentBadge label={v === 'success' ? 'نجح' : v === 'failed' ? 'فشل' : 'معلّق'} variant={v === 'success' ? 'success' : v === 'failed' ? 'error' : 'warning'} size="small" /> },
              { key: 'status_code', label: 'الرمز', render: (v: any) => v || '—' },
              { key: 'error', label: 'الخطأ', render: (v: string) => <span className="text-xs text-[#a4262c]">{(v || '').slice(0, 40)}</span> },
            ]} data={deliveries} />
        )}
      </div>

      <FluentPanel isOpen={!!panel} onClose={() => setPanel(null)} title={panel === 'job' ? 'مهمة مجدولة جديدة' : 'Webhook جديد'}
        footer={<div className="flex gap-2 justify-end"><button onClick={() => setPanel(null)} className="px-4 py-2 text-sm border border-[#8a8886] rounded-sm">إلغاء</button><button onClick={save} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm">حفظ</button></div>}>
        <div className="space-y-3">
          {panel === 'job' ? <>
            <FluentFormField label="اسم المهمة"><FluentInput value={form.name || ''} onChange={(e) => set('name', e.target.value)} /></FluentFormField>
            <FluentFormField label="النوع"><FluentSelect value={form.job_type || 'custom'} onChange={(e) => set('job_type', e.target.value)}>{Object.entries(jobTypeLabel).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</FluentSelect></FluentFormField>
            <FluentFormField label="التكرار"><FluentSelect value={form.frequency || 'daily'} onChange={(e) => set('frequency', e.target.value)}>{Object.entries(freqLabel).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</FluentSelect></FluentFormField>
          </> : <>
            <FluentFormField label="الاسم"><FluentInput value={form.name || ''} onChange={(e) => set('name', e.target.value)} /></FluentFormField>
            <FluentFormField label="الحدث"><FluentInput value={form.event || ''} onChange={(e) => set('event', e.target.value)} placeholder="invoice.created" /></FluentFormField>
            <FluentFormField label="رابط الوجهة"><FluentInput value={form.target_url || ''} onChange={(e) => set('target_url', e.target.value)} placeholder="https://..." /></FluentFormField>
            <FluentFormField label="المفتاح السرّي (اختياري)"><FluentInput value={form.secret || ''} onChange={(e) => set('secret', e.target.value)} /></FluentFormField>
          </>}
        </div>
      </FluentPanel>
    </div>
  );
}
