// pages/Purchasing/PurchasingPage.tsx
import { useEffect, useMemo, useState } from 'react';
import { ShoppingBag, Plus, RefreshCw, Send, CheckCircle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput } from '../../components/FluentUI';
import { purchasingApi } from '../../services/api';

const TABS = [
  { id: 'rfq', label: 'طلبات عروض الأسعار', action: 'تحويل لأمر شراء' },
  { id: 'po', label: 'أوامر الشراء', action: 'فاتورة + استلام' },
];
const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function PurchasingPage() {
  const [docs, setDocs] = useState<any[]>([]);
  const [tab, setTab] = useState('rfq');
  const [showPanel, setShowPanel] = useState(false);
  const [form, setForm] = useState<any>({});
  const [msg, setMsg] = useState('');

  const reload = () => purchasingApi.list().then(setDocs).catch(() => {});
  useEffect(reload, []);
  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));
  const rows = useMemo(() => docs.filter((d) => d.doc_type === tab), [docs, tab]);
  const meta = TABS.find((t) => t.id === tab)!;

  const openNew = () => { setForm({ doc_type: tab, date: new Date().toISOString().slice(0, 10) }); setShowPanel(true); };
  const save = async () => { try { await purchasingApi.create({ ...form, doc_type: tab }); setShowPanel(false); reload(); } catch { alert('تعذّر الحفظ.'); } };
  const process = async (id: number) => {
    try { const r = await purchasingApi.process(id); setMsg(r.message); reload(); setTimeout(() => setMsg(''), 4500); }
    catch (e: any) { setMsg(e?.response?.data?.message || 'تعذّر'); setTimeout(() => setMsg(''), 4000); }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="دورة الشراء" subtitle="Purchasing — RFQ → أمر شراء → فاتورة شراء + استلام"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new', label: 'مستند جديد', icon: <Plus size={16} />, variant: 'primary', onClick: openNew },
        ]} />
      <div className="p-6 space-y-6">
        {msg && <div className="flex items-center gap-2 rounded-md border border-[#107c10]/30 bg-[#f3faf3] px-4 py-2 text-sm text-[#107c10]"><CheckCircle size={16} /> {msg}</div>}
        <div className="grid grid-cols-2 gap-4">
          {TABS.map((t) => <FluentStatsCard key={t.id} title={t.label} value={docs.filter((d) => d.doc_type === t.id).length} icon={<ShoppingBag size={20} />} color="blue" />)}
        </div>
        <div className="flex gap-1 border-b border-[#e1dfdd]">
          {TABS.map((t) => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`px-4 py-2 text-sm border-b-2 -mb-px ${tab === t.id ? 'border-[#0078d4] text-[#0078d4] font-medium' : 'border-transparent text-[#605e5c]'}`}>{t.label}</button>
          ))}
        </div>
        <FluentTable
          title={meta.label}
          subtitle={`${rows.length} مستند`}
          columns={[
            { key: 'number', label: 'الرقم', sortable: true },
            { key: 'supplier_name', label: 'المورّد' },
            { key: 'date', label: 'التاريخ', sortable: true },
            { key: 'item_name', label: 'الصنف' },
            { key: 'quantity', label: 'الكمية' },
            { key: 'total', label: 'الإجمالي', render: (v: any) => fmt(v) },
            { key: 'status', label: 'الحالة', render: (v: string) => <FluentBadge label={v === 'draft' ? 'مسودة' : v === 'sent' ? 'مُرسل' : 'محوّل'} variant={v === 'draft' ? 'warning' : 'success'} size="small" /> },
            { key: '__act', label: '', render: (_: any, row: any) => row.status !== 'converted'
              ? <button onClick={(e) => { e.stopPropagation(); process(row.id); }} className="flex items-center gap-1 text-xs text-white bg-[#0078d4] px-2 py-1 rounded hover:bg-[#106ebe]"><Send size={12} /> {meta.action}</button>
              : <span className="text-xs text-[#107c10]">✓ {row.linked_ref}</span> },
          ]}
          data={rows}
        />
      </div>
      <FluentPanel isOpen={showPanel} onClose={() => setShowPanel(false)} title={`${meta.label} — مستند جديد`}
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={save} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        <div className="space-y-3">
          <FluentFormField label="رقم المستند"><FluentInput value={form.number || ''} onChange={(e) => set('number', e.target.value)} placeholder={tab === 'rfq' ? 'RFQ-0003' : 'PO-0003'} /></FluentFormField>
          <FluentFormField label="المورّد"><FluentInput value={form.supplier_name || ''} onChange={(e) => set('supplier_name', e.target.value)} /></FluentFormField>
          <FluentFormField label="التاريخ"><FluentInput type="date" value={form.date || ''} onChange={(e) => set('date', e.target.value)} /></FluentFormField>
          <FluentFormField label="رمز الصنف"><FluentInput value={form.item_code || ''} onChange={(e) => set('item_code', e.target.value)} placeholder="IT-1001" /></FluentFormField>
          <FluentFormField label="اسم الصنف"><FluentInput value={form.item_name || ''} onChange={(e) => set('item_name', e.target.value)} /></FluentFormField>
          <FluentFormField label="الكمية"><FluentInput type="number" value={form.quantity || ''} onChange={(e) => set('quantity', e.target.value)} /></FluentFormField>
          <FluentFormField label="سعر الوحدة"><FluentInput type="number" value={form.unit_price || ''} onChange={(e) => set('unit_price', e.target.value)} /></FluentFormField>
          <FluentFormField label="المستودع"><FluentInput value={form.warehouse || ''} onChange={(e) => set('warehouse', e.target.value)} /></FluentFormField>
          <p className="text-xs text-[#605e5c]">RFQ → يتحوّل لأمر شراء. أمر الشراء → ينشئ فاتورة شراء (ترحيل محاسبي) + استلام مخزني.</p>
        </div>
      </FluentPanel>
    </div>
  );
}
