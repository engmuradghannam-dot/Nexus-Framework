// pages/StockMovements/StockMovementsPage.tsx
import { useEffect, useState } from 'react';
import { ArrowLeftRight, RefreshCw, Plus, CheckCircle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput } from '../../components/FluentUI';
import { stockApi } from '../../services/api';

export default function StockMovementsPage() {
  const [movements, setMovements] = useState<any[]>([]);
  const [showPanel, setShowPanel] = useState(false);
  const [form, setForm] = useState<any>({});
  const [msg, setMsg] = useState('');

  const reload = () => stockApi.movements().then(setMovements).catch(() => {});
  useEffect(reload, []);
  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));

  const doTransfer = async () => {
    try {
      const r = await stockApi.transfer(form);
      setMsg(r.message); setShowPanel(false); setForm({}); reload();
      setTimeout(() => setMsg(''), 4000);
    } catch (e: any) { alert(e?.response?.data?.message || 'تعذّر النقل'); }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="حركات المخزون" subtitle="Stock Ledger — استلام / صرف / نقل بين المستودعات"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'transfer', label: 'نقل بين المستودعات', icon: <ArrowLeftRight size={16} />, variant: 'primary', onClick: () => { setForm({ date: new Date().toISOString().slice(0, 10) }); setShowPanel(true); } },
        ]} />
      <div className="p-6 space-y-6">
        {msg && <div className="flex items-center gap-2 rounded-md border border-[#107c10]/30 bg-[#f3faf3] px-4 py-2 text-sm text-[#107c10]"><CheckCircle size={16} /> {msg}</div>}
        <FluentTable
          title="دفتر الحركات"
          subtitle={`${movements.length} حركة`}
          columns={[
            { key: 'date', label: 'التاريخ', sortable: true },
            { key: 'item_code', label: 'رمز الصنف', sortable: true },
            { key: 'item_name', label: 'الاسم' },
            { key: 'warehouse', label: 'المستودع' },
            { key: 'movement_type', label: 'النوع', render: (v: string) => <FluentBadge label={v === 'in' ? 'داخل' : 'خارج'} variant={v === 'in' ? 'success' : 'warning'} size="small" /> },
            { key: 'quantity', label: 'الكمية' },
            { key: 'unit_cost', label: 'تكلفة الوحدة' },
            { key: 'reference', label: 'المرجع' },
          ]}
          data={movements}
        />
      </div>

      <FluentPanel isOpen={showPanel} onClose={() => setShowPanel(false)} title="نقل بين المستودعات"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={doTransfer} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">تنفيذ النقل</button>
        </div>}>
        <div className="space-y-3">
          <FluentFormField label="رمز الصنف"><FluentInput value={form.item_code || ''} onChange={(e) => set('item_code', e.target.value)} placeholder="IT-1001" /></FluentFormField>
          <FluentFormField label="اسم الصنف"><FluentInput value={form.item_name || ''} onChange={(e) => set('item_name', e.target.value)} /></FluentFormField>
          <FluentFormField label="الكمية"><FluentInput type="number" value={form.quantity || ''} onChange={(e) => set('quantity', e.target.value)} /></FluentFormField>
          <FluentFormField label="تكلفة الوحدة"><FluentInput type="number" value={form.unit_cost || ''} onChange={(e) => set('unit_cost', e.target.value)} /></FluentFormField>
          <FluentFormField label="من مستودع"><FluentInput value={form.from_warehouse || ''} onChange={(e) => set('from_warehouse', e.target.value)} placeholder="الرياض" /></FluentFormField>
          <FluentFormField label="إلى مستودع"><FluentInput value={form.to_warehouse || ''} onChange={(e) => set('to_warehouse', e.target.value)} placeholder="جدة" /></FluentFormField>
          <p className="text-xs text-[#605e5c]">يُنشئ حركة صرف من المصدر وحركة استلام في الوجهة تلقائياً.</p>
        </div>
      </FluentPanel>
    </div>
  );
}
