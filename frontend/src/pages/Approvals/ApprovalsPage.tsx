// pages/Approvals/ApprovalsPage.tsx
import { useEffect, useState } from 'react';
import { CheckCircle, XCircle, Plus, RefreshCw, ShieldCheck, GitBranch, Trash2 } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { approvalsApi } from '../../services/api';

const fmt = (n: any) => n == null ? '—' : Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const STATUS: Record<string, any> = { pending: 'warning', approved: 'success', rejected: 'danger' };
const STATUS_AR: Record<string, string> = { pending: 'قيد الاعتماد', approved: 'معتمد', rejected: 'مرفوض' };

export default function ApprovalsPage() {
  const [tab, setTab] = useState<'pending' | 'strategies'>('pending');
  const [pending, setPending] = useState<any[]>([]);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [showStrategy, setShowStrategy] = useState(false);
  const [form, setForm] = useState<any>({ levels: [{ sequence: 1 }] });
  const [detail, setDetail] = useState<any>(null);
  const [msg, setMsg] = useState('');

  const reload = () => {
    approvalsApi.pending().then(setPending).catch(() => setPending([]));
    approvalsApi.strategies().then(setStrategies).catch(() => setStrategies([]));
  };
  useEffect(() => { reload(); approvalsApi.roles().then(setRoles).catch(() => {}); }, []);

  const act = async (id: number, approve: boolean) => {
    const comment = approve ? '' : (prompt('سبب الرفض (اختياري):') || '');
    try {
      await approvalsApi.act(id, approve, comment);
      setMsg(approve ? 'تم الاعتماد' : 'تم الرفض');
      setDetail(null); reload();
    } catch (e: any) {
      setMsg(e?.response?.data?.detail || 'تعذّر تنفيذ الإجراء');
    }
  };

  const addLevel = () => setForm((f: any) => ({ ...f, levels: [...f.levels, { sequence: f.levels.length + 1 }] }));
  const setLevel = (i: number, k: string, v: any) => setForm((f: any) => {
    const levels = [...f.levels]; levels[i] = { ...levels[i], [k]: v }; return { ...f, levels };
  });

  const saveStrategy = async () => {
    try {
      await approvalsApi.createStrategy({
        name: form.name, document_type: form.document_type, min_amount: form.min_amount || '0',
        levels: form.levels.filter((l: any) => l.role).map((l: any) => ({
          sequence: Number(l.sequence), role: Number(l.role), label: l.label || '',
        })),
      });
      setShowStrategy(false); setForm({ levels: [{ sequence: 1 }] }); setMsg('تم حفظ الاستراتيجية'); reload();
    } catch { setMsg('تعذّر الحفظ — تأكد من الاسم والمستويات'); }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="الموافقات" subtitle="اعتماد متعدّد المستويات — استراتيجيات الإطلاق"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          ...(tab === 'strategies' ? [{ id: 'new', label: 'استراتيجية جديدة', icon: <Plus size={16} />, variant: 'primary' as const, onClick: () => { setForm({ levels: [{ sequence: 1 }] }); setShowStrategy(true); } }] : []),
        ]} />

      <div className="p-6 space-y-4">
        {msg && <div className="bg-[#dff6dd] text-[#0b6a0b] text-sm px-4 py-2 rounded-sm">{msg}</div>}

        <div className="flex gap-1 border-b border-[#e1dfdd]">
          {[['pending', 'موافقاتي المعلّقة', <ShieldCheck size={15} />], ['strategies', 'الاستراتيجيات', <GitBranch size={15} />]].map(([k, label, icon]: any) => (
            <button key={k} onClick={() => setTab(k)}
              className={`flex items-center gap-1.5 px-4 py-2 text-sm border-b-2 -mb-px ${tab === k ? 'border-[#0078d4] text-[#0078d4] font-medium' : 'border-transparent text-[#605e5c]'}`}>
              {icon} {label}
            </button>
          ))}
        </div>

        {tab === 'pending' && (
          <FluentTable
            title="بانتظار اعتمادك"
            subtitle="المستندات التي وصلت مستوى يتطلّب دورك — اعتمد أو ارفض"
            columns={[
              { key: 'document_type', label: 'المستند' },
              { key: 'object_id', label: 'المرجع', render: (v: any) => `#${v}` },
              { key: 'amount', label: 'المبلغ', render: (v: any) => fmt(v) },
              { key: 'current_sequence', label: 'المستوى', render: (v: any) => <FluentBadge label={`L${v}`} variant="info" size="small" /> },
              { key: 'strategy_name', label: 'الاستراتيجية' },
              { key: '__act', label: '', render: (_: any, r: any) => (
                <div className="flex items-center gap-1">
                  <button onClick={(e) => { e.stopPropagation(); act(r.id, true); }} className="flex items-center gap-1 text-[#0b6a0b] hover:bg-[#f3faf3] px-2 py-1 rounded text-xs"><CheckCircle size={14} /> اعتماد</button>
                  <button onClick={(e) => { e.stopPropagation(); act(r.id, false); }} className="flex items-center gap-1 text-[#a4262c] hover:bg-[#fdf2f2] px-2 py-1 rounded text-xs"><XCircle size={14} /> رفض</button>
                </div>
              ) },
            ]}
            data={pending}
            onRowClick={(r: any) => { approvalsApi.getRequest(r.id).then(setDetail); }}
            emptyMessage="لا مستندات بانتظار اعتمادك"
          />
        )}

        {tab === 'strategies' && (
          <div className="space-y-3">
            {strategies.length === 0 && <FluentCard><p className="text-sm text-[#605e5c]">لا استراتيجيات بعد — أنشئ واحدة لتوجيه المستندات عبر مستويات اعتماد.</p></FluentCard>}
            {strategies.map((s) => (
              <FluentCard key={s.id}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm">{s.name}</span>
                      <FluentBadge label={s.document_type} variant="info" size="small" />
                      <span className="text-xs text-[#605e5c]">≥ {fmt(s.min_amount)}</span>
                    </div>
                    <div className="text-xs text-[#605e5c] mt-1">
                      {s.levels?.map((l: any, i: number) => (
                        <span key={l.id}>{i > 0 && ' ← '}L{l.sequence}: {l.role_name}</span>
                      ))}
                    </div>
                  </div>
                  <button onClick={() => { if (confirm('حذف الاستراتيجية؟')) approvalsApi.removeStrategy(s.id).then(reload); }} className="text-[#a4262c] hover:bg-[#fdf2f2] p-1 rounded"><Trash2 size={14} /></button>
                </div>
              </FluentCard>
            ))}
          </div>
        )}
      </div>

      {detail && (
        <FluentPanel isOpen={!!detail} onClose={() => setDetail(null)} title={`${detail.document_type} #${detail.object_id}`}>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <FluentBadge label={STATUS_AR[detail.status]} variant={STATUS[detail.status]} size="small" />
              <span className="text-sm text-[#605e5c]">المبلغ: {fmt(detail.amount)}</span>
            </div>
            <div className="text-sm font-medium text-[#323130]">سلسلة الاعتماد</div>
            {detail.steps?.map((st: any) => (
              <div key={st.id} className="flex items-center justify-between border border-[#e1dfdd] rounded-sm p-2">
                <span className="text-sm">L{st.sequence} — {st.role_name}</span>
                <FluentBadge label={STATUS_AR[st.decision] || st.decision} variant={STATUS[st.decision] || 'neutral'} size="small" />
              </div>
            ))}
          </div>
        </FluentPanel>
      )}

      <FluentPanel isOpen={showStrategy} onClose={() => setShowStrategy(false)} title="استراتيجية إطلاق جديدة"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setShowStrategy(false)} className="px-4 py-2 text-sm border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={saveStrategy} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        <div className="space-y-3">
          <FluentFormField label="الاسم"><FluentInput value={form.name || ''} onChange={(e) => setForm((f: any) => ({ ...f, name: e.target.value }))} placeholder="اعتماد أوامر الشراء الكبيرة" /></FluentFormField>
          <FluentFormField label="نوع المستند"><FluentInput value={form.document_type || ''} onChange={(e) => setForm((f: any) => ({ ...f, document_type: e.target.value }))} placeholder="purchase_order" /></FluentFormField>
          <FluentFormField label="الحد الأدنى للمبلغ"><FluentInput type="number" value={form.min_amount || ''} onChange={(e) => setForm((f: any) => ({ ...f, min_amount: e.target.value }))} placeholder="100000" /></FluentFormField>
          <div className="border-t border-[#e1dfdd] pt-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">مستويات الاعتماد (بالترتيب)</span>
              <button onClick={addLevel} className="text-xs text-[#0078d4] hover:underline flex items-center gap-1"><Plus size={12} /> مستوى</button>
            </div>
            {form.levels.map((l: any, i: number) => (
              <div key={i} className="flex gap-2 mb-2 items-center">
                <span className="text-xs text-[#605e5c] w-6">L{i + 1}</span>
                <FluentSelect value={l.role || ''} onChange={(e) => setLevel(i, 'role', e.target.value)} className="flex-1">
                  <option value="">— الدور —</option>
                  {roles.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
                </FluentSelect>
                <FluentInput value={l.label || ''} onChange={(e) => setLevel(i, 'label', e.target.value)} placeholder="وصف" className="w-28" />
              </div>
            ))}
          </div>
        </div>
      </FluentPanel>
    </div>
  );
}
