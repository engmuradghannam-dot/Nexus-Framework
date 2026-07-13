// pages/CustomFields/CustomFieldsPage.tsx
import { useEffect, useState } from 'react';
import { SlidersHorizontal, Plus, RefreshCw, Trash2 } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { customFieldsApi } from '../../services/api';

const MODULES = [
  ['inventory', 'المخزون'], ['crm', 'العملاء'], ['selling', 'المبيعات'], ['buying', 'المشتريات'],
  ['hr', 'الموارد البشرية'], ['assets', 'الأصول'], ['warehouses', 'المستودعات'],
];
const TYPES = [['text', 'نص'], ['number', 'رقم'], ['date', 'تاريخ'], ['select', 'قائمة'], ['boolean', 'نعم/لا'], ['textarea', 'نص طويل']];

export default function CustomFieldsPage() {
  const [module, setModule] = useState('inventory');
  const [fields, setFields] = useState<any[]>([]);
  const [showPanel, setShowPanel] = useState(false);
  const [form, setForm] = useState<any>({ field_type: 'text' });

  const reload = () => customFieldsApi.list(module).then(setFields).catch(() => setFields([]));
  useEffect(() => { reload(); /* eslint-disable-next-line */ }, [module]);
  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));

  const save = async () => {
    try {
      const payload: any = { ...form, module, field_key: (form.field_key || '').trim().replace(/\s+/g, '_').toLowerCase() };
      if (form.field_type === 'select' && typeof form.options === 'string') payload.options = form.options.split(',').map((x: string) => x.trim()).filter(Boolean);
      await customFieldsApi.create(payload);
      setShowPanel(false); setForm({ field_type: 'text' }); reload();
    } catch { alert('تعذّر الحفظ — تأكد من المعرّف (فريد لكل وحدة).'); }
  };
  const del = async (id: number) => { if (confirm('حذف الحقل؟')) { await customFieldsApi.remove(id); reload(); } };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="الحقول المخصّصة" subtitle="Custom Fields — أضف حقولاً لأي وحدة بدون برمجة"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new', label: 'حقل جديد', icon: <Plus size={16} />, variant: 'primary', onClick: () => { setForm({ field_type: 'text' }); setShowPanel(true); } },
        ]} />
      <div className="p-6 space-y-6">
        <FluentCard>
          <FluentFormField label="الوحدة">
            <FluentSelect value={module} onChange={(e) => setModule(e.target.value)}>
              {MODULES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </FluentSelect>
          </FluentFormField>
        </FluentCard>

        <FluentTable
          title={`حقول وحدة «${MODULES.find((m) => m[0] === module)?.[1]}»`}
          subtitle={`${fields.length} حقل مخصّص — يظهر تلقائياً في النموذج والجدول`}
          columns={[
            { key: 'label_ar', label: 'التسمية', render: (v: string, r: any) => v || r.label },
            { key: 'field_key', label: 'المعرّف' },
            { key: 'field_type', label: 'النوع', render: (v: string) => <FluentBadge label={TYPES.find((t) => t[0] === v)?.[1] || v} variant="info" size="small" /> },
            { key: 'required', label: 'إلزامي', render: (v: boolean) => (v ? 'نعم' : '—') },
            { key: 'options', label: 'الخيارات', render: (v: any) => Array.isArray(v) && v.length ? v.join('، ') : '—' },
            { key: '__del', label: '', render: (_: any, r: any) => <button onClick={(e) => { e.stopPropagation(); del(r.id); }} className="text-[#a4262c] hover:bg-[#fdf2f2] p-1 rounded"><Trash2 size={14} /></button> },
          ]}
          data={fields}
          emptyMessage="لا حقول مخصّصة لهذه الوحدة بعد"
        />
      </div>

      <FluentPanel isOpen={showPanel} onClose={() => setShowPanel(false)} title="حقل مخصّص جديد"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={save} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        <div className="space-y-3">
          <FluentFormField label="التسمية (عربي)"><FluentInput value={form.label_ar || ''} onChange={(e) => set('label_ar', e.target.value)} /></FluentFormField>
          <FluentFormField label="التسمية (إنجليزي)"><FluentInput value={form.label || ''} onChange={(e) => set('label', e.target.value)} /></FluentFormField>
          <FluentFormField label="المعرّف (key)"><FluentInput value={form.field_key || ''} onChange={(e) => set('field_key', e.target.value)} placeholder="supplier_ref" /></FluentFormField>
          <FluentFormField label="النوع">
            <FluentSelect value={form.field_type} onChange={(e) => set('field_type', e.target.value)}>
              {TYPES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </FluentSelect>
          </FluentFormField>
          {form.field_type === 'select' && (
            <FluentFormField label="الخيارات (مفصولة بفاصلة)"><FluentInput value={form.options || ''} onChange={(e) => set('options', e.target.value)} placeholder="A, B, C" /></FluentFormField>
          )}
          <label className="flex items-center gap-2 text-sm text-[#323130]">
            <input type="checkbox" checked={!!form.required} onChange={(e) => set('required', e.target.checked)} className="h-4 w-4 accent-[#0078d4]" /> حقل إلزامي
          </label>
        </div>
      </FluentPanel>
    </div>
  );
}
