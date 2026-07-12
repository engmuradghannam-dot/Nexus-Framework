// pages/Invoicing/InvoicingPage.tsx
import { useEffect, useMemo, useState } from 'react';
import { Receipt, Plus, RefreshCw, CheckCircle, Send } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { invoicingApi, taxApi } from '../../services/api';

const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function InvoicingPage() {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPanel, setShowPanel] = useState(false);
  const [form, setForm] = useState<any>({});
  const [msg, setMsg] = useState('');
  const [templates, setTemplates] = useState<any[]>([]);

  const reload = () => {
    setLoading(true);
    invoicingApi.list().then(setInvoices).catch(() => {}).finally(() => setLoading(false));
  };
  useEffect(reload, []);
  useEffect(() => { taxApi.templates().then(setTemplates).catch(() => {}); }, []);

  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));
  const sub = Number(form.subtotal || 0);
  const rate = Number(form.tax_rate ?? 15);
  const tax = (sub * rate) / 100;

  const openNew = () => { setForm({ invoice_type: 'sales', tax_rate: 15, invoice_date: new Date().toISOString().slice(0, 10) }); setShowPanel(true); };

  const save = async () => {
    try {
      await invoicingApi.create(form);
      setShowPanel(false); reload();
    } catch { alert('تعذّر الحفظ — تأكد من رقم الفاتورة والمبلغ.'); }
  };

  const postLedger = async (id: number) => {
    try {
      const res = await invoicingApi.post(id);
      setMsg(res.message || 'تم الترحيل'); reload();
      setTimeout(() => setMsg(''), 4000);
    } catch (e: any) { setMsg(e?.response?.data?.message || 'تعذّر الترحيل'); setTimeout(() => setMsg(''), 4000); }
  };

  const stats = useMemo(() => ({
    total: invoices.length,
    posted: invoices.filter((i) => i.status === 'posted').length,
    value: invoices.reduce((s, i) => s + Number(i.total || 0), 0),
  }), [invoices]);

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="الفواتير" subtitle="Invoicing — فواتير البيع والشراء مع الترحيل المحاسبي"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new', label: 'فاتورة جديدة', icon: <Plus size={16} />, variant: 'primary', onClick: openNew },
        ]} />
      <div className="p-6 space-y-6">
        {msg && <div className="flex items-center gap-2 rounded-md border border-[#107c10]/30 bg-[#f3faf3] px-4 py-2 text-sm text-[#107c10]"><CheckCircle size={16} /> {msg}</div>}
        <div className="grid grid-cols-3 gap-4">
          <FluentStatsCard title="عدد الفواتير" value={stats.total} icon={<Receipt size={20} />} color="blue" />
          <FluentStatsCard title="مُرحّلة" value={stats.posted} icon={<CheckCircle size={20} />} color="green" />
          <FluentStatsCard title="إجمالي القيمة" value={fmt(stats.value)} icon={<Receipt size={20} />} color="purple" />
        </div>

        <FluentTable
          title="الفواتير"
          subtitle={loading ? 'جارٍ التحميل…' : `${invoices.length} فاتورة`}
          columns={[
            { key: 'invoice_number', label: 'رقم الفاتورة', sortable: true },
            { key: 'invoice_type', label: 'النوع', render: (v: string) => <FluentBadge label={v === 'sales' ? 'بيع' : 'شراء'} variant={v === 'sales' ? 'success' : 'info'} size="small" /> },
            { key: 'party_name', label: 'الطرف' },
            { key: 'invoice_date', label: 'التاريخ', sortable: true },
            { key: 'subtotal', label: 'الأساسي', render: (v: any) => fmt(v) },
            { key: 'tax_amount', label: 'الضريبة', render: (v: any) => fmt(v) },
            { key: 'total', label: 'الإجمالي', render: (v: any) => fmt(v) },
            { key: 'status', label: 'الحالة', render: (v: string) => <FluentBadge label={v === 'posted' ? 'مُرحّلة' : v === 'draft' ? 'مسودة' : 'ملغاة'} variant={v === 'posted' ? 'success' : 'warning'} size="small" /> },
            {
              key: '__post', label: '', render: (_: any, row: any) => row.status === 'draft'
                ? <button onClick={(e) => { e.stopPropagation(); postLedger(row.id); }} className="flex items-center gap-1 text-xs text-white bg-[#0078d4] px-2 py-1 rounded hover:bg-[#106ebe]"><Send size={12} /> ترحيل</button>
                : <span className="text-xs text-[#107c10]">✓ مُرحّلة</span>
            },
          ]}
          data={invoices}
        />
      </div>

      <FluentPanel isOpen={showPanel} onClose={() => setShowPanel(false)} title="فاتورة جديدة"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={save} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        <div className="space-y-3">
          <FluentFormField label="نوع الفاتورة"><FluentSelect value={form.invoice_type || 'sales'} onChange={(e) => set('invoice_type', e.target.value)}><option value="sales">فاتورة بيع</option><option value="purchase">فاتورة شراء</option></FluentSelect></FluentFormField>
          <FluentFormField label="رقم الفاتورة"><FluentInput value={form.invoice_number || ''} onChange={(e) => set('invoice_number', e.target.value)} placeholder="SINV-0003" /></FluentFormField>
          <FluentFormField label="الطرف (عميل/مورّد)"><FluentInput value={form.party_name || ''} onChange={(e) => set('party_name', e.target.value)} /></FluentFormField>
          <FluentFormField label="التاريخ"><FluentInput type="date" value={form.invoice_date || ''} onChange={(e) => set('invoice_date', e.target.value)} /></FluentFormField>
          <FluentFormField label="المبلغ الأساسي"><FluentInput type="number" value={form.subtotal || ''} onChange={(e) => set('subtotal', e.target.value)} /></FluentFormField>
          <FluentFormField label="قالب الضريبة (ZATCA)">
            <FluentSelect value={form.tax_template || ''} onChange={(e) => {
              const t = templates.find((x) => String(x.id) === e.target.value);
              if (t) { set('tax_template', e.target.value); set('tax_rate', t.rate); set('zatca_category', t.zatca_category); }
            }}>
              <option value="">— اختر قالباً —</option>
              {templates.map((t) => <option key={t.id} value={t.id}>{t.name_ar || t.name} — {t.rate}% ({t.zatca_category})</option>)}
            </FluentSelect>
          </FluentFormField>
          <FluentFormField label="نسبة الضريبة %"><FluentInput type="number" value={form.tax_rate ?? 15} onChange={(e) => set('tax_rate', e.target.value)} /></FluentFormField>
          <div className="rounded-md bg-[#f3f2f1] p-3 text-sm space-y-1">
            <div className="flex justify-between text-[#605e5c]"><span>الضريبة ({rate}%)</span><span className="font-mono">{fmt(tax)}</span></div>
            <div className="flex justify-between font-bold text-[#323130] border-t border-[#e1dfdd] pt-1"><span>الإجمالي</span><span className="font-mono">{fmt(sub + tax)}</span></div>
          </div>
          <p className="text-xs text-[#605e5c]">بعد الحفظ، اضغط «ترحيل» لإنشاء القيود المحاسبية تلقائياً في دفتر الأستاذ.</p>
        </div>
      </FluentPanel>
    </div>
  );
}
