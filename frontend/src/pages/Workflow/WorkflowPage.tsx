// pages/Workflow/WorkflowPage.tsx
import { useEffect, useState } from 'react';
import { GitBranch, Plus, RefreshCw, Trash2, ArrowLeft, Play } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput } from '../../components/FluentUI';
import { workflowApi } from '../../services/api';

export default function WorkflowPage() {
  const [tab, setTab] = useState<'instances' | 'definitions'>('instances');
  const [instances, setInstances] = useState<any[]>([]);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [detail, setDetail] = useState<any>(null);
  const [available, setAvailable] = useState<any[]>([]);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState<any>({ states: [{ key: 'draft', is_initial: true }, { key: 'done', is_final: true }] });
  const [msg, setMsg] = useState('');

  const reload = () => {
    workflowApi.instances().then(setInstances).catch(() => setInstances([]));
    workflowApi.workflows().then(setWorkflows).catch(() => setWorkflows([]));
  };
  useEffect(reload, []);

  const openInstance = async (inst: any) => {
    const [full, avail] = await Promise.all([
      workflowApi.getInstance(inst.id).catch(() => inst),
      workflowApi.available(inst.id).catch(() => []),
    ]);
    setDetail(full); setAvailable(avail);
  };

  const take = async (transitionId: number) => {
    if (!detail) return;
    try {
      await workflowApi.take(detail.id, transitionId, '');
      setMsg('تم نقل المستند'); setDetail(null); reload();
    } catch (e: any) { setMsg(e?.response?.data?.detail || 'تعذّر النقل'); }
  };

  const addState = () => setForm((f: any) => ({ ...f, states: [...f.states, { key: '' }] }));
  const setState = (i: number, k: string, v: any) => setForm((f: any) => { const s = [...f.states]; s[i] = { ...s[i], [k]: v }; return { ...f, states: s }; });

  const save = async () => {
    try {
      await workflowApi.createWorkflow({
        name: form.name, document_type: form.document_type,
        states: form.states.filter((s: any) => s.key).map((s: any) => ({
          key: s.key, label: s.label || s.key, is_initial: !!s.is_initial, is_final: !!s.is_final,
        })),
      });
      setShow(false); setMsg('تم حفظ سير العمل'); reload();
    } catch { setMsg('تعذّر الحفظ — تأكد من الاسم والحالات'); }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="سير العمل" subtitle="BPM — دورة حياة المستندات عبر حالات وانتقالات"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          ...(tab === 'definitions' ? [{ id: 'new', label: 'سير عمل جديد', icon: <Plus size={16} />, variant: 'primary' as const, onClick: () => { setForm({ states: [{ key: 'draft', is_initial: true }, { key: 'done', is_final: true }] }); setShow(true); } }] : []),
        ]} />

      <div className="p-6 space-y-4">
        {msg && <div className="bg-[#dff6dd] text-[#0b6a0b] text-sm px-4 py-2 rounded-sm">{msg}</div>}

        <div className="flex gap-1 border-b border-[#e1dfdd]">
          {[['instances', 'المستندات الجارية'], ['definitions', 'التعريفات']].map(([k, label]: any) => (
            <button key={k} onClick={() => setTab(k)}
              className={`px-4 py-2 text-sm border-b-2 -mb-px ${tab === k ? 'border-[#0078d4] text-[#0078d4] font-medium' : 'border-transparent text-[#605e5c]'}`}>{label}</button>
          ))}
        </div>

        {tab === 'instances' && (
          <FluentTable
            title="مستندات في سير العمل"
            subtitle={`${instances.length} مستند`}
            columns={[
              { key: 'workflow_name', label: 'سير العمل' },
              { key: 'object_id', label: 'المرجع', render: (v: any) => `#${v}` },
              { key: 'state_label', label: 'الحالة الحالية', render: (v: any, r: any) => <FluentBadge label={v || r.state_key} variant="info" size="small" /> },
              { key: 'updated_at', label: 'آخر تحديث', render: (v: string) => new Date(v).toLocaleString('en-GB') },
            ]}
            data={instances}
            onRowClick={openInstance}
            emptyMessage="لا مستندات في سير العمل بعد"
          />
        )}

        {tab === 'definitions' && (
          <div className="space-y-3">
            {workflows.length === 0 && <FluentCard><p className="text-sm text-[#605e5c]">لا تعريفات بعد — أنشئ سير عمل بحالاته.</p></FluentCard>}
            {workflows.map((w) => (
              <FluentCard key={w.id}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <GitBranch size={15} className="text-[#0078d4]" />
                      <span className="font-medium text-sm">{w.name}</span>
                      <FluentBadge label={w.document_type} variant="info" size="small" />
                    </div>
                    <div className="text-xs text-[#605e5c] mt-1 flex items-center gap-1 flex-wrap">
                      {w.states?.map((s: any, i: number) => (
                        <span key={s.id} className="flex items-center gap-1">
                          {i > 0 && <ArrowLeft size={11} />}
                          <span className={s.is_initial ? 'font-medium text-[#0078d4]' : s.is_final ? 'text-[#0b6a0b]' : ''}>{s.label || s.key}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                  <button onClick={() => { if (confirm('حذف سير العمل؟')) workflowApi.removeWorkflow(w.id).then(reload); }} className="text-[#a4262c] hover:bg-[#fdf2f2] p-1 rounded"><Trash2 size={14} /></button>
                </div>
              </FluentCard>
            ))}
          </div>
        )}
      </div>

      {detail && (
        <FluentPanel isOpen={!!detail} onClose={() => setDetail(null)} title={`${detail.workflow_name} #${detail.object_id}`}>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-sm text-[#605e5c]">الحالة الحالية:</span>
              <FluentBadge label={detail.state_label || detail.state_key} variant="info" size="small" />
            </div>

            {available.length > 0 ? (
              <div>
                <div className="text-sm font-medium text-[#323130] mb-2">الانتقالات المتاحة</div>
                <div className="space-y-1.5">
                  {available.map((t) => (
                    <button key={t.id} onClick={() => take(t.id)} className="w-full flex items-center justify-between border border-[#e1dfdd] rounded-sm p-2 hover:bg-[#eff6fc]">
                      <span className="flex items-center gap-2 text-sm"><Play size={13} className="text-[#0078d4]" /> {t.name}</span>
                      <span className="text-xs text-[#605e5c]">→ {t.to_key}{t.role_name ? ` (${t.role_name})` : ''}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : <p className="text-sm text-[#605e5c]">لا انتقالات متاحة لك من هذه الحالة (قد تكون نهائية أو تتطلّب دوراً آخر).</p>}

            {detail.history?.length > 0 && (
              <div className="border-t border-[#e1dfdd] pt-3">
                <div className="text-sm font-medium text-[#323130] mb-2">السجل</div>
                {detail.history.map((h: any) => (
                  <div key={h.id} className="text-xs text-[#605e5c] flex items-center gap-1 mb-1">
                    <span>{h.from_key || '—'}</span><ArrowLeft size={11} /><span className="text-[#323130]">{h.to_key}</span>
                    <span className="mr-2">· {h.actor_email || 'نظام'} · {new Date(h.timestamp).toLocaleString('en-GB')}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </FluentPanel>
      )}

      <FluentPanel isOpen={show} onClose={() => setShow(false)} title="سير عمل جديد"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setShow(false)} className="px-4 py-2 text-sm border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={save} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        <div className="space-y-3">
          <FluentFormField label="الاسم"><FluentInput value={form.name || ''} onChange={(e) => setForm((f: any) => ({ ...f, name: e.target.value }))} placeholder="اعتماد أمر الشراء" /></FluentFormField>
          <FluentFormField label="نوع المستند"><FluentInput value={form.document_type || ''} onChange={(e) => setForm((f: any) => ({ ...f, document_type: e.target.value }))} placeholder="purchase_order" /></FluentFormField>
          <div className="border-t border-[#e1dfdd] pt-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">الحالات</span>
              <button onClick={addState} className="text-xs text-[#0078d4] hover:underline flex items-center gap-1"><Plus size={12} /> حالة</button>
            </div>
            {form.states.map((s: any, i: number) => (
              <div key={i} className="flex items-center gap-2 mb-2">
                <FluentInput value={s.key || ''} onChange={(e) => setState(i, 'key', e.target.value)} placeholder="key" className="w-28" />
                <FluentInput value={s.label || ''} onChange={(e) => setState(i, 'label', e.target.value)} placeholder="التسمية" className="flex-1" />
                <label className="flex items-center gap-1 text-xs"><input type="checkbox" checked={!!s.is_initial} onChange={(e) => setState(i, 'is_initial', e.target.checked)} /> بداية</label>
                <label className="flex items-center gap-1 text-xs"><input type="checkbox" checked={!!s.is_final} onChange={(e) => setState(i, 'is_final', e.target.checked)} /> نهاية</label>
              </div>
            ))}
            <p className="text-xs text-[#605e5c]">بعد الحفظ، تُضاف الانتقالات بين الحالات (والأدوار المطلوبة) من الـAPI.</p>
          </div>
        </div>
      </FluentPanel>
    </div>
  );
}
