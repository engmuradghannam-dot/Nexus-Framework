// pages/Automation/AutomatedActionsPage.tsx
import { useEffect, useState } from 'react';
import { Zap, Plus, RefreshCw, Trash2 } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { automationApi } from '../../services/api';

const TRIGGERS = [['on_create', 'عند الإنشاء'], ['on_update', 'عند التعديل'], ['on_create_or_update', 'إنشاء أو تعديل']];
const STEP_TYPES = [['set_field', 'تعيين حقل'], ['notify', 'إشعار'], ['webhook', 'Webhook']];
const OPS = ['==', '!=', '>', '>=', '<', '<='];

export default function AutomatedActionsPage() {
  const [actions, setActions] = useState<any[]>([]);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState<any>({ trigger: 'on_create', steps: [{ step_type: 'set_field', order: 1 }] });
  const [msg, setMsg] = useState('');

  const reload = () => automationApi.actions().then(setActions).catch(() => setActions([]));
  useEffect(reload, []);

  const setF = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));
  const addStep = () => setForm((f: any) => ({ ...f, steps: [...f.steps, { step_type: 'set_field', order: f.steps.length + 1 }] }));
  const setStep = (i: number, k: string, v: any) => setForm((f: any) => { const s = [...f.steps]; s[i] = { ...s[i], [k]: v }; return { ...f, steps: s }; });

  const save = async () => {
    try {
      await automationApi.createAction({
        name: form.name, model_label: form.model_label, trigger: form.trigger,
        condition_field: form.condition_field || '', condition_operator: form.condition_operator || '',
        condition_value: form.condition_value || '',
        steps: form.steps.filter((s: any) => s.step_type).map((s: any, i: number) => ({
          order: i + 1, step_type: s.step_type,
          target_field: s.target_field || '', target_value: s.target_value || '', message: s.message || '',
        })),
      });
      setShow(false); setForm({ trigger: 'on_create', steps: [{ step_type: 'set_field', order: 1 }] });
      setMsg('تم حفظ الإجراء التلقائي'); reload();
    } catch { setMsg('تعذّر الحفظ — تأكد من الاسم والنموذج'); }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="الإجراءات التلقائية" subtitle="عند حدث، بشرط، نفّذ — بلا برمجة"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new', label: 'إجراء جديد', icon: <Plus size={16} />, variant: 'primary', onClick: () => { setForm({ trigger: 'on_create', steps: [{ step_type: 'set_field', order: 1 }] }); setShow(true); } },
        ]} />

      <div className="p-6 space-y-3">
        {msg && <div className="bg-[#dff6dd] text-[#0b6a0b] text-sm px-4 py-2 rounded-sm">{msg}</div>}
        {actions.length === 0 && <FluentCard><p className="text-sm text-[#605e5c]">لا إجراءات تلقائية بعد — أنشئ قاعدة «عند حدث على مستند، بشرط، نفّذ إجراءً».</p></FluentCard>}
        {actions.map((a) => (
          <FluentCard key={a.id}>
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Zap size={15} className="text-[#0078d4]" />
                  <span className="font-medium text-sm">{a.name}</span>
                  <FluentBadge label={TRIGGERS.find((t) => t[0] === a.trigger)?.[1] || a.trigger} variant="info" size="small" />
                  {!a.is_active && <FluentBadge label="معطّل" variant="neutral" size="small" />}
                </div>
                <div className="text-xs text-[#605e5c] mt-1">
                  <span className="font-mono">{a.model_label}</span>
                  {a.condition_field && <span> · شرط: {a.condition_field} {a.condition_operator} {a.condition_value}</span>}
                  {' · '}{a.steps?.length || 0} خطوة · نُفّذ {a.run_count || 0} مرة
                </div>
              </div>
              <button onClick={() => { if (confirm('حذف الإجراء؟')) automationApi.removeAction(a.id).then(reload); }} className="text-[#a4262c] hover:bg-[#fdf2f2] p-1 rounded"><Trash2 size={14} /></button>
            </div>
          </FluentCard>
        ))}
      </div>

      <FluentPanel isOpen={show} onClose={() => setShow(false)} title="إجراء تلقائي جديد"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setShow(false)} className="px-4 py-2 text-sm border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={save} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        <div className="space-y-3">
          <FluentFormField label="الاسم"><FluentInput value={form.name || ''} onChange={(e) => setF('name', e.target.value)} placeholder="مراجعة الأوامر الكبيرة" /></FluentFormField>
          <FluentFormField label="النموذج (app.Model)"><FluentInput value={form.model_label || ''} onChange={(e) => setF('model_label', e.target.value)} placeholder="buying.PurchaseOrder" /></FluentFormField>
          <FluentFormField label="المُشغِّل">
            <FluentSelect value={form.trigger} onChange={(e) => setF('trigger', e.target.value)}>
              {TRIGGERS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </FluentSelect>
          </FluentFormField>
          <div className="rounded-sm border border-[#e1dfdd] p-3 space-y-2">
            <span className="text-xs font-medium text-[#605e5c]">الشرط (اختياري)</span>
            <div className="flex gap-2">
              <FluentInput value={form.condition_field || ''} onChange={(e) => setF('condition_field', e.target.value)} placeholder="grand_total" className="flex-1" />
              <FluentSelect value={form.condition_operator || ''} onChange={(e) => setF('condition_operator', e.target.value)} className="w-20">
                <option value="">—</option>
                {OPS.map((o) => <option key={o} value={o}>{o}</option>)}
              </FluentSelect>
              <FluentInput value={form.condition_value || ''} onChange={(e) => setF('condition_value', e.target.value)} placeholder="10000" className="w-24" />
            </div>
          </div>
          <div className="border-t border-[#e1dfdd] pt-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">الخطوات</span>
              <button onClick={addStep} className="text-xs text-[#0078d4] hover:underline flex items-center gap-1"><Plus size={12} /> خطوة</button>
            </div>
            {form.steps.map((s: any, i: number) => (
              <div key={i} className="rounded-sm bg-[#faf9f8] p-2 mb-2 space-y-1.5">
                <FluentSelect value={s.step_type} onChange={(e) => setStep(i, 'step_type', e.target.value)}>
                  {STEP_TYPES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                </FluentSelect>
                {s.step_type === 'set_field' && (
                  <div className="flex gap-2">
                    <FluentInput value={s.target_field || ''} onChange={(e) => setStep(i, 'target_field', e.target.value)} placeholder="الحقل" className="flex-1" />
                    <FluentInput value={s.target_value || ''} onChange={(e) => setStep(i, 'target_value', e.target.value)} placeholder="القيمة" className="flex-1" />
                  </div>
                )}
                {s.step_type === 'notify' && (
                  <FluentInput value={s.message || ''} onChange={(e) => setStep(i, 'message', e.target.value)} placeholder="نص الإشعار — {id} يُستبدل بالمعرّف" />
                )}
              </div>
            ))}
          </div>
        </div>
      </FluentPanel>
    </div>
  );
}
