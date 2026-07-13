// pages/CreditNotes/CreditNotesPage.tsx
import { useEffect, useMemo, useState } from 'react';
import { Undo2, Plus, RefreshCw, Send, CheckCircle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect, FluentTextArea } from '../../components/FluentUI';
import { invoicingApi, creditNotesApi } from '../../services/api';

const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function CreditNotesPage() {
  const [notes, setNotes] = useState<any[]>([]);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [showPanel, setShowPanel] = useState(false);
  const [form, setForm] = useState<any>({ credit_date: new Date().toISOString().slice(0, 10) });
  const [msg, setMsg] = useState('');

  const reload = () => {
    creditNotesApi.list().then(setNotes).catch(() => {});
    invoicingApi.list().then((r) => setInvoices((r || []).filter((i: any) => i.status === 'posted'))).catch(() => {});
  };
  useEffect(reload, []);
  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));
  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(''), 5000); };

  const selectedInv = useMemo(() => invoices.find((i) => String(i.id) === String(form.original_invoice)), [invoices, form.original_invoice]);
  const taxRate = selectedInv ? Number(selectedInv.tax_rate || 0) : 15;
  const computedTax = form.subtotal ? (Number(form.subtotal) * taxRate / 100) : 0;
  const computedTotal = (Number(form.subtotal || 0) + computedTax);

  const posted = notes.filter((n) => n.status === 'posted');
  const totalCredited = posted.reduce((s, n) => s + Number(n.total || 0), 0);

  const save = async () => {
    if (!form.original_invoice || !form.subtotal || !form.credit_number) return alert('أكمل الفاتورة والرقم والمبلغ');
    try {
      const cn = await creditNotesApi.create({ ...form, tax_amount: computedTax });
      const r = await creditNotesApi.post(cn.id);
      flash(r.success ? r.message : `لم يُرحّل: ${r.message}`);
      setShowPanel(false); setForm({ credit_date: new Date().toISOString().slice(0, 10) }); reload();
    } catch (e: any) { alert(e?.response?.data?.message || 'تعذّر الحفظ'); }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="الإشعارات الدائنة والمرتجعات" subtitle="Credit Notes — عكس محاسبي متوازن لمرتجعات البيع والشراء"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new', label: 'إشعار دائن', icon: <Plus size={16} />, variant: 'primary', onClick: () => { setForm({ credit_date: new Date().toISOString().slice(0, 10) }); setShowPanel(true); } },
        ]} />
      <div className="p-6 space-y-6">
        {msg && <div className="flex items-center gap-2 rounded-md border border-[#107c10]/30 bg-[#f3faf3] px-4 py-2 text-sm text-[#107c10]"><CheckCircle size={16} /> {msg}</div>}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <FluentStatsCard title="إجمالي الإشعارات" value={notes.length} icon={<Undo2 size={20} />} color="blue" />
          <FluentStatsCard title="مُرحّلة" value={posted.length} icon={<CheckCircle size={20} />} color="green" />
          <FluentStatsCard title="قيمة المرتجعات" value={fmt(totalCredited)} icon={<Undo2 size={20} />} color="orange" />
        </div>
        <FluentTable
          title="الإشعارات الدائنة" subtitle={`${notes.length} إشعار`}
          columns={[
            { key: 'credit_number', label: 'الرقم' },
            { key: 'original_invoice_number', label: 'الفاتورة الأصلية' },
            { key: 'return_type', label: 'النوع', render: (v: string) => <FluentBadge label={v === 'sales_return' ? 'مرتجع بيع' : 'مرتجع شراء'} variant={v === 'sales_return' ? 'info' : 'warning'} size="small" /> },
            { key: 'credit_date', label: 'التاريخ' },
            { key: 'subtotal', label: 'الصافي', render: (v: any) => fmt(v) },
            { key: 'tax_amount', label: 'الضريبة', render: (v: any) => fmt(v) },
            { key: 'total', label: 'الإجمالي', render: (v: any) => <span className="font-semibold">{fmt(v)}</span> },
            { key: 'reason', label: 'السبب', render: (v: string) => v || '—' },
            { key: 'status', label: 'الحالة', render: (v: string) => <FluentBadge label={v === 'posted' ? 'مُرحّل' : 'مسودة'} variant={v === 'posted' ? 'success' : 'warning'} size="small" /> },
          ]}
          data={notes}
          emptyMessage="لا إشعارات دائنة بعد — أنشئ واحداً مقابل فاتورة مُرحّلة"
        />
      </div>

      <FluentPanel isOpen={showPanel} onClose={() => setShowPanel(false)} title="إشعار دائن / مرتجع جديد"
        footer={<div className="flex gap-2 justify-end"><button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm border border-[#8a8886] rounded-sm">إلغاء</button><button onClick={save} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm flex items-center gap-1"><Send size={14} /> إنشاء وترحيل</button></div>}>
        <div className="space-y-3">
          <FluentFormField label="الفاتورة الأصلية (المُرحّلة فقط)">
            <FluentSelect value={form.original_invoice || ''} onChange={(e) => set('original_invoice', e.target.value)}>
              <option value="">— اختر فاتورة —</option>
              {invoices.map((i) => <option key={i.id} value={i.id}>{i.invoice_number} — {i.party_name} ({fmt(i.total)})</option>)}
            </FluentSelect>
          </FluentFormField>
          {selectedInv && <div className="text-xs bg-[#eff6fc] rounded p-2 text-[#0078d4]">القابل للإشعار: {fmt(selectedInv.creditable_remaining ?? selectedInv.total)} ر.س · نوع: {selectedInv.invoice_type === 'sales' ? 'بيع' : 'شراء'}</div>}
          <FluentFormField label="رقم الإشعار"><FluentInput value={form.credit_number || ''} onChange={(e) => set('credit_number', e.target.value)} placeholder="CN-0001" /></FluentFormField>
          <FluentFormField label="التاريخ"><FluentInput type="date" value={form.credit_date || ''} onChange={(e) => set('credit_date', e.target.value)} /></FluentFormField>
          <FluentFormField label="المبلغ الصافي المرتجع"><FluentInput type="number" value={form.subtotal || ''} onChange={(e) => set('subtotal', e.target.value)} /></FluentFormField>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-[#f3f2f1] rounded p-2">الضريبة ({taxRate}%): <span className="font-semibold">{fmt(computedTax)}</span></div>
            <div className="bg-[#f3f2f1] rounded p-2">الإجمالي: <span className="font-semibold">{fmt(computedTotal)}</span></div>
          </div>
          <FluentFormField label="السبب"><FluentTextArea value={form.reason || ''} onChange={(e) => set('reason', e.target.value)} rows={2} placeholder="مرتجع بضاعة تالفة…" /></FluentFormField>
          <p className="text-xs text-[#605e5c]">سيُنشئ قيداً محاسبياً عكسياً متوازناً تلقائياً (يعكس المبيعات/المشتريات والضريبة).</p>
        </div>
      </FluentPanel>
    </div>
  );
}
