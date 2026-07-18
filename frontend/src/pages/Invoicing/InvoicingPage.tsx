// pages/Invoicing/InvoicingPage.tsx
import { useEffect, useMemo, useState } from 'react';
import { Receipt, Plus, RefreshCw, CheckCircle, Send, Printer, Ban, Wallet, Trash2 } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { invoicingApi, taxApi, buyingApi } from '../../services/api';
import { printInvoice } from '../../utils/printInvoice';

const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function InvoicingPage() {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showPanel, setShowPanel] = useState(false);
  const [form, setForm] = useState<any>({});
  const [msg, setMsg] = useState('');
  const [templates, setTemplates] = useState<any[]>([]);
  const [payInvoice, setPayInvoice] = useState<any>(null);
  const [payForm, setPayForm] = useState<any>({ method: 'bank' });
  const [payHistory, setPayHistory] = useState<any[]>([]);
  const [items, setItems] = useState<any[]>([]);
  const [lineItems, setLineItems] = useState<any[]>([]);

  const reload = () => {
    setLoading(true);
    invoicingApi.list().then(setInvoices).catch(() => {}).finally(() => setLoading(false));
  };
  useEffect(reload, []);
  useEffect(() => { taxApi.templates().then(setTemplates).catch(() => {}); }, []);
  useEffect(() => { buyingApi.itemsList().then(setItems).catch(() => {}); }, []);

  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));

  // Line-item grid: the subtotal and tax are derived from the lines, not typed.
  const addLine = () => setLineItems((ls) => [...ls, { item: '', qty: '1', rate: '', tax_rate: form.tax_rate ?? 15 }]);
  const setLine = (i: number, k: string, v: any) => setLineItems((ls) => { const n = [...ls]; n[i] = { ...n[i], [k]: v }; return n; });
  const delLine = (i: number) => setLineItems((ls) => ls.filter((_, x) => x !== i));
  const lineAmount = (l: any) => Number(l.qty || 0) * Number(l.rate || 0);
  const sub = lineItems.length ? lineItems.reduce((s, l) => s + lineAmount(l), 0) : Number(form.subtotal || 0);
  const tax = lineItems.length
    ? lineItems.reduce((s, l) => s + lineAmount(l) * Number(l.tax_rate || 0) / 100, 0)
    : (sub * Number(form.tax_rate ?? 15)) / 100;

  const openNew = () => { setForm({ invoice_type: 'sales', tax_rate: 15, invoice_date: new Date().toISOString().slice(0, 10) }); setLineItems([]); setShowPanel(true); };

  const save = async () => {
    try {
      const payload: any = { ...form };
      if (lineItems.length) {
        // Real line items → sent atomically; subtotal/tax are derived server-side.
        payload.line_items = lineItems
          .filter((l) => l.item && l.qty && l.rate)
          .map((l) => ({ item: Number(l.item), qty: l.qty, rate: l.rate, tax_rate: l.tax_rate || 0 }));
        delete payload.subtotal;
      }
      await invoicingApi.create(payload);
      setShowPanel(false); setLineItems([]); reload();
    } catch { alert('تعذّر الحفظ — تأكد من رقم الفاتورة والبنود.'); }
  };

  const doPrint = async (id: number) => { try { const d = await invoicingApi.zatcaQr(id); await printInvoice(d); } catch { alert('تعذّرت الطباعة'); } };
  const doVoid = async (id: number) => {
    if (!confirm('إلغاء الفاتورة وعكس ترحيلها المحاسبي؟')) return;
    try { const r = await invoicingApi.void(id); if (!r.success) alert(r.message); reload(); }
    catch (e) { alert('تعذّر الإلغاء'); }
  };
  const openPay = (inv: any) => {
    setPayInvoice(inv); setPayForm({ method: 'bank', payment_date: new Date().toISOString().slice(0, 10) });
    invoicingApi.payments(inv.id).then(setPayHistory).catch(() => setPayHistory([]));
  };
  const doPay = async () => {
    if (!payForm.amount) return alert('أدخل المبلغ');
    try {
      const r = await invoicingApi.recordPayment(payInvoice.id, payForm);
      if (!r.success) { alert(r.message); return; }
      setMsg(r.message); setTimeout(() => setMsg(''), 4000);
      setPayInvoice(null); reload();
    } catch (e: any) { alert(e?.response?.data?.message || 'تعذّر تسجيل الدفعة'); }
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
              key: '__post', label: '', render: (_: any, row: any) => (
                <div className="flex items-center gap-1 justify-end">
                  <button onClick={(e) => { e.stopPropagation(); doPrint(row.id); }} title="طباعة / PDF" className="flex items-center gap-1 text-xs text-[#0078d4] border border-[#0078d4] px-2 py-1 rounded hover:bg-[#eff6fc]"><Printer size={12} /> طباعة</button>
                  {row.status === 'draft'
                    ? <button onClick={(e) => { e.stopPropagation(); postLedger(row.id); }} className="flex items-center gap-1 text-xs text-white bg-[#0078d4] px-2 py-1 rounded hover:bg-[#106ebe]"><Send size={12} /> ترحيل</button>
                    : row.status === 'posted'
                    ? <>
                      {Number(row.outstanding ?? (row.total - (row.paid_amount || 0))) > 0.01 &&
                        <button onClick={(e) => { e.stopPropagation(); openPay(row); }} title="تسجيل دفعة" className="flex items-center gap-1 text-xs text-[#107c10] border border-[#107c10] px-2 py-1 rounded hover:bg-[#f3faf3]"><Wallet size={12} /> دفعة</button>}
                      <button onClick={(e) => { e.stopPropagation(); doVoid(row.id); }} title="إلغاء وعكس الترحيل" className="flex items-center gap-1 text-xs text-[#a4262c] border border-[#a4262c] px-2 py-1 rounded hover:bg-[#fdf3f4]"><Ban size={12} /> إلغاء</button>
                    </>
                    : <span className="text-xs text-[#a19f9d]">ملغاة</span>}
                </div>
              )
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
          <div className="border-t border-[#e1dfdd] pt-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-[#323130]">بنود الفاتورة</span>
              <button onClick={addLine} className="text-xs text-[#0078d4] hover:underline flex items-center gap-1"><Plus size={12} /> إضافة سطر</button>
            </div>
            {lineItems.length === 0 && (
              <div className="text-xs text-[#605e5c] bg-[#faf9f8] rounded-sm p-2 mb-2">
                لا بنود بعد — أضف سطراً، أو اترك البنود فارغة وأدخل المبلغ الأساسي يدوياً بالأسفل.
              </div>
            )}
            {lineItems.map((l, i) => (
              <div key={i} className="flex items-center gap-1.5 mb-1.5">
                <FluentSelect value={l.item} onChange={(e) => setLine(i, 'item', e.target.value)} className="flex-1">
                  <option value="">— الصنف —</option>
                  {items.map((it) => <option key={it.id} value={it.id}>{it.item_code} — {it.item_name}</option>)}
                </FluentSelect>
                <FluentInput type="number" value={l.qty} onChange={(e) => setLine(i, 'qty', e.target.value)} placeholder="كمية" className="w-16" />
                <FluentInput type="number" value={l.rate} onChange={(e) => setLine(i, 'rate', e.target.value)} placeholder="سعر" className="w-20" />
                <FluentInput type="number" value={l.tax_rate} onChange={(e) => setLine(i, 'tax_rate', e.target.value)} placeholder="ض%" className="w-14" />
                <span className="w-20 text-xs text-left font-mono text-[#605e5c]">{fmt(lineAmount(l))}</span>
                <button onClick={() => delLine(i)} className="text-[#a4262c] hover:bg-[#fdf2f2] p-1 rounded"><Trash2 size={14} /></button>
              </div>
            ))}
          </div>
          {lineItems.length === 0 && (
            <FluentFormField label="المبلغ الأساسي (إن لم تُضف بنوداً)"><FluentInput type="number" value={form.subtotal || ''} onChange={(e) => set('subtotal', e.target.value)} /></FluentFormField>
          )}
          <FluentFormField label="العملة">
            <FluentSelect value={form.currency || 'SAR'} onChange={(e) => set('currency', e.target.value)}>
              <option value="SAR">ريال سعودي (SAR)</option><option value="USD">دولار (USD)</option>
              <option value="EUR">يورو (EUR)</option><option value="AED">درهم (AED)</option>
              <option value="KWD">دينار كويتي (KWD)</option><option value="GBP">جنيه (GBP)</option>
            </FluentSelect>
          </FluentFormField>
          {form.currency && form.currency !== 'SAR' &&
            <FluentFormField label="سعر الصرف (مقابل الريال)"><FluentInput type="number" value={form.exchange_rate || ''} onChange={(e) => set('exchange_rate', e.target.value)} placeholder="مثال: 3.75" /></FluentFormField>}
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

      <FluentPanel isOpen={!!payInvoice} onClose={() => setPayInvoice(null)} title={`تسجيل دفعة — ${payInvoice?.invoice_number || ''}`}
        footer={<div className="flex gap-2 justify-end"><button onClick={() => setPayInvoice(null)} className="px-4 py-2 text-sm border border-[#8a8886] rounded-sm">إلغاء</button><button onClick={doPay} className="px-4 py-2 text-sm text-white bg-[#107c10] rounded-sm">تسجيل وترحيل</button></div>}>
        {payInvoice && <div className="space-y-3">
          <div className="rounded-md bg-[#eff6fc] p-3 text-sm">
            <div className="flex justify-between"><span className="text-[#605e5c]">الإجمالي</span><span className="font-semibold">{fmt(payInvoice.total)}</span></div>
            <div className="flex justify-between"><span className="text-[#605e5c]">المدفوع</span><span>{fmt(payInvoice.paid_amount)}</span></div>
            <div className="flex justify-between text-[#0078d4]"><span>المتبقّي</span><span className="font-bold">{fmt(payInvoice.outstanding ?? (payInvoice.total - (payInvoice.paid_amount || 0)))}</span></div>
          </div>
          <FluentFormField label="المبلغ"><FluentInput type="number" value={payForm.amount || ''} onChange={(e) => setPayForm((f: any) => ({ ...f, amount: e.target.value }))} /></FluentFormField>
          <FluentFormField label="طريقة الدفع">
            <FluentSelect value={payForm.method} onChange={(e) => setPayForm((f: any) => ({ ...f, method: e.target.value }))}>
              <option value="bank">تحويل بنكي</option><option value="cash">نقدي</option><option value="card">بطاقة</option><option value="cheque">شيك</option>
            </FluentSelect>
          </FluentFormField>
          <FluentFormField label="التاريخ"><FluentInput type="date" value={payForm.payment_date || ''} onChange={(e) => setPayForm((f: any) => ({ ...f, payment_date: e.target.value }))} /></FluentFormField>
          {payInvoice && payInvoice.currency && payInvoice.currency !== 'SAR' &&
            <FluentFormField label={`سعر الصرف يوم الدفع (${payInvoice.currency})`}><FluentInput type="number" value={payForm.exchange_rate || ''} onChange={(e) => setPayForm((f: any) => ({ ...f, exchange_rate: e.target.value }))} placeholder={String(payInvoice.exchange_rate || '')} /></FluentFormField>}
          <FluentFormField label="مرجع (اختياري)"><FluentInput value={payForm.reference || ''} onChange={(e) => setPayForm((f: any) => ({ ...f, reference: e.target.value }))} /></FluentFormField>
          {payHistory.length > 0 && <div>
            <div className="text-xs font-semibold text-[#605e5c] mt-2 mb-1">سجل الدفعات ({payHistory.length})</div>
            <div className="space-y-1 max-h-40 overflow-auto">
              {payHistory.map((p: any) => (
                <div key={p.id} className="flex justify-between text-xs bg-[#f3f2f1] rounded px-2 py-1">
                  <span>{p.payment_date} · {p.method_display}</span><span className="font-semibold">{fmt(p.amount)}</span>
                </div>
              ))}
            </div>
          </div>}
        </div>}
      </FluentPanel>
    </div>
  );
}
