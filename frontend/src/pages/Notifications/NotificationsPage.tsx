// pages/Notifications/NotificationsPage.tsx
import { useEffect, useMemo, useState } from 'react';
import { Mail, Plus, RefreshCw, Send, Trash2, CheckCircle, MessageSquare } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect, FluentTextArea } from '../../components/FluentUI';
import { notificationsApi } from '../../services/api';

const statusMeta: Record<string, any> = { sent: ['success', 'أُرسل'], queued: ['warning', 'في الانتظار'], failed: ['error', 'فشل'] };

export default function NotificationsPage() {
  const [tab, setTab] = useState<'templates' | 'log'>('templates');
  const [templates, setTemplates] = useState<any[]>([]);
  const [log, setLog] = useState<any[]>([]);
  const [showNew, setShowNew] = useState(false);
  const [showSend, setShowSend] = useState<any>(null);
  const [form, setForm] = useState<any>({ channel: 'email' });
  const [sendForm, setSendForm] = useState<any>({ recipient: '', context: {} });
  const [msg, setMsg] = useState('');

  const reload = () => { notificationsApi.templates().then(setTemplates).catch(() => {}); notificationsApi.log().then(setLog).catch(() => {}); };
  useEffect(reload, []);
  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));

  const placeholders = useMemo(() => {
    if (!showSend) return [];
    const text = `${showSend.subject || ''} ${showSend.body || ''}`;
    return Array.from(new Set((text.match(/\{(\w+)\}/g) || []).map((x: string) => x.slice(1, -1))));
  }, [showSend]);

  const saveTpl = async () => { try { await notificationsApi.createTemplate({ ...form, name: form.name || 'قالب' }); setShowNew(false); setForm({ channel: 'email' }); reload(); } catch { alert('تعذّر الحفظ'); } };
  const delTpl = async (id: number) => { if (confirm('حذف القالب؟')) { await notificationsApi.removeTemplate(id); reload(); } };
  const openSend = (t: any) => { setSendForm({ recipient: '', context: {} }); setShowSend(t); };
  const doSend = async () => {
    try { const r = await notificationsApi.send(showSend.id, sendForm); setShowSend(null); setMsg(`${statusMeta[r.status]?.[1] || r.status} — ${sendForm.recipient}`); setTab('log'); reload(); setTimeout(() => setMsg(''), 5000); }
    catch { alert('تعذّر الإرسال'); }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="البريد والرسائل" subtitle="Email & SMS — قوالب وإرسال وسجل"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new', label: 'قالب جديد', icon: <Plus size={16} />, variant: 'primary', onClick: () => setShowNew(true) },
        ]} />
      <div className="p-6 space-y-6">
        {msg && <div className="flex items-center gap-2 rounded-md border border-[#107c10]/30 bg-[#f3faf3] px-4 py-2 text-sm text-[#107c10]"><CheckCircle size={16} /> {msg}</div>}
        <div className="flex gap-1 border-b border-[#e1dfdd]">
          {[['templates', 'القوالب'], ['log', 'سجل الإرسال']].map(([id, label]) => (
            <button key={id} onClick={() => setTab(id as any)} className={`px-4 py-2 text-sm border-b-2 -mb-px ${tab === id ? 'border-[#0078d4] text-[#0078d4] font-medium' : 'border-transparent text-[#605e5c]'}`}>{label}</button>
          ))}
        </div>

        {tab === 'templates' ? (
          <FluentTable
            title="قوالب الرسائل" subtitle={`${templates.length} قالب`}
            columns={[
              { key: 'name', label: 'الاسم' },
              { key: 'channel', label: 'القناة', render: (v: string) => <FluentBadge label={v === 'email' ? 'بريد' : 'SMS'} variant="info" size="small" /> },
              { key: 'subject', label: 'الموضوع', render: (v: string) => v || '—' },
              { key: 'body', label: 'النص', render: (v: string) => <span className="text-xs text-[#605e5c]">{(v || '').slice(0, 50)}…</span> },
              { key: '__send', label: '', render: (_: any, r: any) => <button onClick={(e) => { e.stopPropagation(); openSend(r); }} className="flex items-center gap-1 text-xs text-white bg-[#0078d4] px-2 py-1 rounded hover:bg-[#106ebe]"><Send size={12} /> إرسال</button> },
              { key: '__del', label: '', render: (_: any, r: any) => <button onClick={(e) => { e.stopPropagation(); delTpl(r.id); }} className="text-[#a4262c] p-1"><Trash2 size={14} /></button> },
            ]}
            data={templates}
          />
        ) : (
          <FluentTable
            title="سجل الإرسال" subtitle={`${log.length} رسالة`}
            columns={[
              { key: 'created_at', label: 'التاريخ', render: (v: string) => new Date(v).toLocaleString('en-GB') },
              { key: 'channel', label: 'القناة', render: (v: string) => v === 'email' ? <Mail size={14} /> : <MessageSquare size={14} /> },
              { key: 'recipient', label: 'المستلم' },
              { key: 'subject', label: 'الموضوع', render: (v: string) => v || '—' },
              { key: 'status', label: 'الحالة', render: (v: string) => { const m = statusMeta[v] || ['default', v]; return <FluentBadge label={m[1]} variant={m[0]} size="small" />; } },
            ]}
            data={log}
          />
        )}
      </div>

      <FluentPanel isOpen={showNew} onClose={() => setShowNew(false)} title="قالب جديد"
        footer={<div className="flex gap-2 justify-end"><button onClick={() => setShowNew(false)} className="px-4 py-2 text-sm border border-[#8a8886] rounded-sm">إلغاء</button><button onClick={saveTpl} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm">حفظ</button></div>}>
        <div className="space-y-3">
          <FluentFormField label="اسم القالب"><FluentInput value={form.name || ''} onChange={(e) => set('name', e.target.value)} /></FluentFormField>
          <FluentFormField label="القناة"><FluentSelect value={form.channel} onChange={(e) => set('channel', e.target.value)}><option value="email">بريد إلكتروني</option><option value="sms">رسالة SMS</option></FluentSelect></FluentFormField>
          {form.channel === 'email' && <FluentFormField label="الموضوع"><FluentInput value={form.subject || ''} onChange={(e) => set('subject', e.target.value)} /></FluentFormField>}
          <FluentFormField label="النص (استخدم {name} {invoice} …)"><FluentTextArea value={form.body || ''} onChange={(e) => set('body', e.target.value)} rows={5} /></FluentFormField>
        </div>
      </FluentPanel>

      <FluentPanel isOpen={!!showSend} onClose={() => setShowSend(null)} title={`إرسال: ${showSend?.name || ''}`}
        footer={<div className="flex gap-2 justify-end"><button onClick={() => setShowSend(null)} className="px-4 py-2 text-sm border border-[#8a8886] rounded-sm">إلغاء</button><button onClick={doSend} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm">إرسال</button></div>}>
        <div className="space-y-3">
          <FluentFormField label={showSend?.channel === 'sms' ? 'رقم الجوال' : 'البريد الإلكتروني'}><FluentInput value={sendForm.recipient} onChange={(e) => setSendForm((s: any) => ({ ...s, recipient: e.target.value }))} /></FluentFormField>
          {placeholders.map((ph: string) => (
            <FluentFormField key={ph} label={`قيمة {${ph}}`}><FluentInput value={sendForm.context[ph] || ''} onChange={(e) => setSendForm((s: any) => ({ ...s, context: { ...s.context, [ph]: e.target.value } }))} /></FluentFormField>
          ))}
          <p className="text-xs text-[#605e5c]">البريد يُرسَل عبر إعدادات SMTP للنظام. الرسائل النصية تُدرَج في قائمة الانتظار حتى ربط بوابة SMS.</p>
        </div>
      </FluentPanel>
    </div>
  );
}
