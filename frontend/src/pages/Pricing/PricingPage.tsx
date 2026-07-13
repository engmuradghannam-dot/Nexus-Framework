// pages/Pricing/PricingPage.tsx
import { useEffect, useState } from 'react';
import { Tag, Plus, RefreshCw, Trash2, Calculator } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { pricingApi } from '../../services/api';

const SCOPES: Record<string, string> = { all: 'كل الأصناف', item: 'صنف محدّد', category: 'فئة' };
const DTYPES: Record<string, string> = { percent: 'نسبة %', fixed_amount: 'مبلغ خصم', fixed_price: 'سعر ثابت' };
const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function PricingPage() {
  const [rules, setRules] = useState<any[]>([]);
  const [showPanel, setShowPanel] = useState(false);
  const [form, setForm] = useState<any>({ scope: 'all', discount_type: 'percent', min_quantity: 1, priority: 1 });
  const [calc, setCalc] = useState<any>({ item_code: '', category: '', quantity: 1, base_price: 1000 });
  const [quote, setQuote] = useState<any>(null);

  const reload = () => pricingApi.list().then(setRules).catch(() => setRules([]));
  useEffect(reload, []);
  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));
  const setC = (k: string, v: any) => setCalc((c: any) => ({ ...c, [k]: v }));

  useEffect(() => {
    if (!calc.base_price) { setQuote(null); return; }
    pricingApi.quote(calc).then(setQuote).catch(() => setQuote(null));
  }, [calc]);

  const save = async () => {
    try { await pricingApi.create(form); setShowPanel(false); setForm({ scope: 'all', discount_type: 'percent', min_quantity: 1, priority: 1 }); reload(); }
    catch { alert('تعذّر الحفظ'); }
  };
  const del = async (id: number) => { if (confirm('حذف القاعدة؟')) { await pricingApi.remove(id); reload(); } };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="قواعد التسعير" subtitle="Pricing Rules — خصومات وعروض حسب الصنف/الفئة/الكمية"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new', label: 'قاعدة جديدة', icon: <Plus size={16} />, variant: 'primary', onClick: () => setShowPanel(true) },
        ]} />
      <div className="p-6 space-y-6">
        <FluentCard>
          <h3 className="text-sm font-semibold text-[#323130] mb-3 flex items-center gap-2"><Calculator size={16} /> حاسبة السعر</h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
            <FluentFormField label="رمز الصنف"><FluentInput value={calc.item_code} onChange={(e) => setC('item_code', e.target.value)} placeholder="IT-1001" /></FluentFormField>
            <FluentFormField label="الفئة"><FluentInput value={calc.category} onChange={(e) => setC('category', e.target.value)} placeholder="إلكترونيات" /></FluentFormField>
            <FluentFormField label="الكمية"><FluentInput type="number" value={calc.quantity} onChange={(e) => setC('quantity', e.target.value)} /></FluentFormField>
            <FluentFormField label="السعر الأساسي"><FluentInput type="number" value={calc.base_price} onChange={(e) => setC('base_price', e.target.value)} /></FluentFormField>
            <div className="rounded-md bg-[#eff6fc] p-3 text-center">
              <div className="text-xs text-[#605e5c]">السعر النهائي</div>
              <div className="text-lg font-bold text-[#0078d4]">{quote ? fmt(quote.final_price) : '—'}</div>
              {quote?.applied_rule && <div className="text-[10px] text-[#107c10]">{quote.applied_rule} (-{fmt(quote.discount)})</div>}
            </div>
          </div>
        </FluentCard>

        <FluentTable
          title="القواعد"
          subtitle={`${rules.length} قاعدة`}
          columns={[
            { key: 'name_ar', label: 'الاسم', render: (v: string, r: any) => v || r.name },
            { key: 'scope', label: 'النطاق', render: (v: string, r: any) => `${SCOPES[v]}${r.target ? ` (${r.target})` : ''}` },
            { key: 'min_quantity', label: 'أدنى كمية' },
            { key: 'discount_type', label: 'نوع الخصم', render: (v: string) => <FluentBadge label={DTYPES[v] || v} variant="info" size="small" /> },
            { key: 'discount_value', label: 'القيمة', render: (v: any) => fmt(v) },
            { key: 'priority', label: 'الأولوية' },
            { key: 'valid_to', label: 'ساري حتى', render: (v: string) => v || '—' },
            { key: '__del', label: '', render: (_: any, r: any) => <button onClick={(e) => { e.stopPropagation(); del(r.id); }} className="text-[#a4262c] hover:bg-[#fdf2f2] p-1 rounded"><Trash2 size={14} /></button> },
          ]}
          data={rules}
          emptyMessage="لا قواعد تسعير بعد"
        />
      </div>

      <FluentPanel isOpen={showPanel} onClose={() => setShowPanel(false)} title="قاعدة تسعير جديدة"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={save} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        <div className="space-y-3">
          <FluentFormField label="اسم القاعدة"><FluentInput value={form.name_ar || ''} onChange={(e) => { set('name_ar', e.target.value); set('name', e.target.value); }} /></FluentFormField>
          <FluentFormField label="النطاق">
            <FluentSelect value={form.scope} onChange={(e) => set('scope', e.target.value)}>
              <option value="all">كل الأصناف</option><option value="item">صنف محدّد</option><option value="category">فئة</option>
            </FluentSelect>
          </FluentFormField>
          {form.scope !== 'all' && <FluentFormField label={form.scope === 'item' ? 'رمز الصنف' : 'اسم الفئة'}><FluentInput value={form.target || ''} onChange={(e) => set('target', e.target.value)} /></FluentFormField>}
          <FluentFormField label="أدنى كمية"><FluentInput type="number" value={form.min_quantity} onChange={(e) => set('min_quantity', e.target.value)} /></FluentFormField>
          <FluentFormField label="نوع الخصم">
            <FluentSelect value={form.discount_type} onChange={(e) => set('discount_type', e.target.value)}>
              <option value="percent">نسبة مئوية %</option><option value="fixed_amount">مبلغ خصم ثابت</option><option value="fixed_price">سعر ثابت</option>
            </FluentSelect>
          </FluentFormField>
          <FluentFormField label="قيمة الخصم/السعر"><FluentInput type="number" value={form.discount_value || ''} onChange={(e) => set('discount_value', e.target.value)} /></FluentFormField>
          <FluentFormField label="الأولوية (الأعلى يُطبّق أولاً)"><FluentInput type="number" value={form.priority} onChange={(e) => set('priority', e.target.value)} /></FluentFormField>
          <FluentFormField label="ساري حتى"><FluentInput type="date" value={form.valid_to || ''} onChange={(e) => set('valid_to', e.target.value)} /></FluentFormField>
        </div>
      </FluentPanel>
    </div>
  );
}
