// pages/UOM/UOMPage.tsx
import { useEffect, useState } from 'react';
import { Ruler, Plus, RefreshCw, ArrowLeftRight, Boxes, Sparkles } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { uomApi } from '../../services/api';

const catLabel: Record<string, string> = { count: 'عدد', weight: 'وزن', length: 'طول', volume: 'حجم' };

export default function UOMPage() {
  const [tab, setTab] = useState<'units' | 'variants'>('units');
  const [units, setUnits] = useState<any[]>([]);
  const [conversions, setConversions] = useState<any[]>([]);
  const [conv, setConv] = useState<any>({ amount: 1, from: '', to: '' });
  const [convResult, setConvResult] = useState<any>(null);
  const [showUnit, setShowUnit] = useState(false);
  const [unitForm, setUnitForm] = useState<any>({ category: 'count' });
  // variants
  const [vTemplate, setVTemplate] = useState({ code: '', name: '' });
  const [attrs, setAttrs] = useState<any[]>([{ key: '', values: '' }]);
  const [variants, setVariants] = useState<any[]>([]);

  const reload = () => {
    uomApi.units().then((u) => { setUnits(u); if (u.length >= 2 && !conv.from) setConv((c: any) => ({ ...c, from: u[0].id, to: u[1].id })); }).catch(() => {});
    uomApi.conversions().then(setConversions).catch(() => {});
  };
  useEffect(reload, []);

  const doConvert = () => { if (conv.from && conv.to) uomApi.convert(conv.amount, conv.from, conv.to).then(setConvResult).catch(() => setConvResult({ success: false, message: 'تعذّر' })); };
  useEffect(() => { doConvert(); /* eslint-disable-next-line */ }, [conv]);
  const saveUnit = async () => { try { await uomApi.createUnit(unitForm); setShowUnit(false); setUnitForm({ category: 'count' }); reload(); } catch { alert('تعذّر الحفظ'); } };

  const addAttr = () => setAttrs((a) => [...a, { key: '', values: '' }]);
  const setAttr = (i: number, k: string, v: string) => setAttrs((a) => a.map((x, j) => j === i ? { ...x, [k]: v } : x));
  const generate = async () => {
    const attributes: any = {};
    attrs.forEach((a) => { if (a.key && a.values) attributes[a.key] = a.values.split(',').map((s: string) => s.trim()).filter(Boolean); });
    if (!vTemplate.code || !Object.keys(attributes).length) return alert('أدخل رمز الصنف وسمة واحدة على الأقل');
    try { const r = await uomApi.generate({ template_code: vTemplate.code, template_name: vTemplate.name, attributes }); setVariants(r.variants); }
    catch { alert('تعذّر التوليد'); }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="وحدات القياس والتباينات" subtitle="UOM & Variants — وحدات · تحويلات · توليد أصناف"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          ...(tab === 'units' ? [{ id: 'new', label: 'وحدة جديدة', icon: <Plus size={16} />, variant: 'primary' as const, onClick: () => setShowUnit(true) }] : []),
        ]} />
      <div className="p-6 space-y-6">
        <div className="flex gap-1 border-b border-[#e1dfdd]">
          {[['units', 'وحدات القياس'], ['variants', 'تباينات الصنف']].map(([id, label]) => (
            <button key={id} onClick={() => setTab(id as any)} className={`px-4 py-2 text-sm border-b-2 -mb-px ${tab === id ? 'border-[#0078d4] text-[#0078d4] font-medium' : 'border-transparent text-[#605e5c]'}`}>{label}</button>
          ))}
        </div>

        {tab === 'units' ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <FluentTable title="الوحدات" subtitle={`${units.length} وحدة`}
                columns={[
                  { key: 'code', label: 'الرمز' }, { key: 'name_ar', label: 'الاسم' }, { key: 'symbol', label: 'الرمز المختصر' },
                  { key: 'category', label: 'الفئة', render: (v: string) => <FluentBadge label={catLabel[v] || v} variant="info" size="small" /> },
                ]} data={units} />
              <FluentTable title="قواعد التحويل" subtitle={`${conversions.length} قاعدة`}
                columns={[
                  { key: 'from_code', label: 'من' }, { key: 'factor', label: 'المعامل', render: (v: any, r: any) => `1 ${r.from_code} = ${v} ${r.to_code}` },
                  { key: 'to_code', label: 'إلى' },
                ]} data={conversions} />
            </div>
            <FluentCard>
              <h3 className="text-sm font-semibold text-[#323130] mb-3 flex items-center gap-2"><ArrowLeftRight size={16} /> محوّل الوحدات</h3>
              <div className="space-y-3">
                <FluentFormField label="الكمية"><FluentInput type="number" value={conv.amount} onChange={(e) => setConv((c: any) => ({ ...c, amount: e.target.value }))} /></FluentFormField>
                <FluentFormField label="من"><FluentSelect value={conv.from} onChange={(e) => setConv((c: any) => ({ ...c, from: e.target.value }))}>{units.map((u) => <option key={u.id} value={u.id}>{u.name_ar} ({u.code})</option>)}</FluentSelect></FluentFormField>
                <FluentFormField label="إلى"><FluentSelect value={conv.to} onChange={(e) => setConv((c: any) => ({ ...c, to: e.target.value }))}>{units.map((u) => <option key={u.id} value={u.id}>{u.name_ar} ({u.code})</option>)}</FluentSelect></FluentFormField>
                <div className="rounded-md bg-[#eff6fc] p-3 text-center">
                  {convResult?.success ? <div className="text-lg font-bold text-[#0078d4]">{convResult.result} <span className="text-xs">{convResult.to}</span></div>
                    : <div className="text-xs text-[#a4262c]">{convResult?.message || 'لا توجد قاعدة تحويل بين الوحدتين'}</div>}
                </div>
              </div>
            </FluentCard>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <FluentCard>
              <h3 className="text-sm font-semibold text-[#323130] mb-3 flex items-center gap-2"><Sparkles size={16} /> مولّد التباينات</h3>
              <div className="space-y-3">
                <FluentFormField label="رمز الصنف الأساسي"><FluentInput value={vTemplate.code} onChange={(e) => setVTemplate((t) => ({ ...t, code: e.target.value }))} placeholder="TSHIRT" /></FluentFormField>
                <FluentFormField label="اسم الصنف"><FluentInput value={vTemplate.name} onChange={(e) => setVTemplate((t) => ({ ...t, name: e.target.value }))} placeholder="قميص قطني" /></FluentFormField>
                <div>
                  <div className="flex items-center justify-between mb-1"><span className="text-xs font-semibold text-[#605e5c]">السمات (القيم مفصولة بفاصلة)</span><button onClick={addAttr} className="text-[#0078d4]"><Plus size={14} /></button></div>
                  {attrs.map((a, i) => (
                    <div key={i} className="flex gap-1 mb-1">
                      <input value={a.key} onChange={(e) => setAttr(i, 'key', e.target.value)} placeholder="المقاس" className="text-xs border rounded p-1.5 w-24" />
                      <input value={a.values} onChange={(e) => setAttr(i, 'values', e.target.value)} placeholder="S, M, L" className="text-xs border rounded p-1.5 flex-1" />
                    </div>
                  ))}
                </div>
                <button onClick={generate} className="w-full flex items-center justify-center gap-1 text-sm text-white bg-[#0078d4] py-2 rounded hover:bg-[#106ebe]"><Boxes size={14} /> توليد الأصناف</button>
              </div>
            </FluentCard>
            <div className="lg:col-span-2">
              <FluentTable title="التباينات المُولّدة" subtitle={`${variants.length} صنف`}
                columns={[
                  { key: 'sku', label: 'SKU' }, { key: 'template_name', label: 'الصنف' },
                  { key: 'attributes', label: 'السمات', render: (v: any) => Object.entries(v || {}).map(([k, val]) => `${k}: ${val}`).join(' · ') },
                ]} data={variants} emptyMessage="أدخل السمات واضغط «توليد الأصناف»" />
            </div>
          </div>
        )}
      </div>

      <FluentPanel isOpen={showUnit} onClose={() => setShowUnit(false)} title="وحدة قياس جديدة"
        footer={<div className="flex gap-2 justify-end"><button onClick={() => setShowUnit(false)} className="px-4 py-2 text-sm border border-[#8a8886] rounded-sm">إلغاء</button><button onClick={saveUnit} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm">حفظ</button></div>}>
        <div className="space-y-3">
          <FluentFormField label="الرمز"><FluentInput value={unitForm.code || ''} onChange={(e) => setUnitForm((f: any) => ({ ...f, code: e.target.value }))} placeholder="PCS" /></FluentFormField>
          <FluentFormField label="الاسم"><FluentInput value={unitForm.name_ar || ''} onChange={(e) => setUnitForm((f: any) => ({ ...f, name_ar: e.target.value }))} /></FluentFormField>
          <FluentFormField label="الرمز المختصر"><FluentInput value={unitForm.symbol || ''} onChange={(e) => setUnitForm((f: any) => ({ ...f, symbol: e.target.value }))} /></FluentFormField>
          <FluentFormField label="الفئة"><FluentSelect value={unitForm.category} onChange={(e) => setUnitForm((f: any) => ({ ...f, category: e.target.value }))}><option value="count">عدد</option><option value="weight">وزن</option><option value="length">طول</option><option value="volume">حجم</option></FluentSelect></FluentFormField>
        </div>
      </FluentPanel>
    </div>
  );
}
