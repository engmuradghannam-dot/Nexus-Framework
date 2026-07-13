// pages/Selling/SellingPage.tsx
import { useEffect, useMemo, useState } from 'react';
import { ShoppingCart, Plus, RefreshCw, Send, Truck, XCircle, Trash2, AlertTriangle, CheckCircle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { sellingApi, customersApi, itemsApi, getWarehouses } from '../../services/api';

const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const STATUS_LABEL: Record<string, string> = { Draft: 'مسودة', Submitted: 'مُعتمد', Delivered: 'تم التسليم', Cancelled: 'ملغى' };
const STATUS_VARIANT: Record<string, any> = { Draft: 'warning', Submitted: 'info', Delivered: 'success', Cancelled: 'error' };

export default function SellingPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [customers, setCustomers] = useState<any[]>([]);
  const [items, setItems] = useState<any[]>([]);
  const [warehouses, setWarehouses] = useState<any[]>([]);

  const [panelOpen, setPanelOpen] = useState(false);
  const [order, setOrder] = useState<any>(null);
  const [lines, setLines] = useState<any[]>([]);
  const [newLine, setNewLine] = useState<any>({ item: '', qty: 1, rate: 0 });
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const reload = () => {
    setLoading(true);
    sellingApi.orders().then(setOrders).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(() => {
    reload();
    customersApi.list().then(setCustomers).catch(() => {});
    itemsApi.list().then(setItems).catch(() => {});
    getWarehouses().then((r: any) => setWarehouses(r.data?.results || r.data || [])).catch(() => {});
  }, []);

  const itemsById = useMemo(() => Object.fromEntries(items.map((i) => [i.id, i])), [items]);

  const stats = useMemo(() => ({
    total: orders.length,
    open: orders.filter((o) => o.status === 'Draft' || o.status === 'Submitted').length,
    value: orders.reduce((s, o) => s + Number(o.grand_total || 0), 0),
  }), [orders]);

  const loadLines = (soId: number) => sellingApi.items(soId).then(setLines).catch(() => setLines([]));

  const openNew = () => {
    setOrder({ customer: '', so_number: '', transaction_date: new Date().toISOString().slice(0, 10), warehouse: '' });
    setLines([]);
    setError(''); setNotice('');
    setPanelOpen(true);
  };

  const openOrder = async (row: any) => {
    const full = await sellingApi.getOrder(row.id);
    setOrder(full);
    setError(''); setNotice('');
    setPanelOpen(true);
    loadLines(row.id);
  };

  const createDraft = async () => {
    try {
      const created = await sellingApi.createOrder(order);
      setOrder(created);
      setNotice('تم إنشاء المسودة — أضف بنود الأمر بالأسفل.');
      reload();
    } catch (e: any) {
      setError(formatApiError(e));
    }
  };

  const addLine = async () => {
    if (!newLine.item || !newLine.qty) return;
    try {
      await sellingApi.addItem({ sales_order: order.id, item: newLine.item, qty: newLine.qty, rate: newLine.rate });
      setNewLine({ item: '', qty: 1, rate: 0 });
      await loadLines(order.id);
      const refreshed = await sellingApi.getOrder(order.id);
      setOrder(refreshed);
      reload();
    } catch (e: any) {
      setError(formatApiError(e));
    }
  };

  const removeLine = async (id: number) => {
    await sellingApi.removeItem(id);
    await loadLines(order.id);
    const refreshed = await sellingApi.getOrder(order.id);
    setOrder(refreshed);
    reload();
  };

  const transition = async (status: string) => {
    setError(''); setNotice('');
    try {
      const updated = await sellingApi.updateOrder(order.id, { status });
      setOrder(updated);
      setNotice(status === 'Delivered' ? 'تم تسليم المخزون وتحديث الأمر.' : `تم تحويل الحالة إلى ${STATUS_LABEL[status]}.`);
      reload();
    } catch (e: any) {
      setError(formatApiError(e));
    }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar
        title="أوامر البيع" subtitle="Sales Orders — دورة كاملة من المسودة حتى التسليم"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new', label: 'أمر بيع جديد', icon: <Plus size={16} />, variant: 'primary', onClick: openNew },
        ]}
      />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-3 gap-4">
          <FluentStatsCard title="عدد الأوامر" value={stats.total} icon={<ShoppingCart size={20} />} color="blue" />
          <FluentStatsCard title="مفتوحة" value={stats.open} icon={<ShoppingCart size={20} />} color="orange" />
          <FluentStatsCard title="إجمالي القيمة" value={fmt(stats.value)} icon={<ShoppingCart size={20} />} color="purple" />
        </div>

        <FluentTable
          title="أوامر البيع"
          subtitle={loading ? 'جارٍ التحميل…' : `${orders.length} أمر`}
          onRowClick={openOrder}
          columns={[
            { key: 'so_number', label: 'رقم الأمر', sortable: true },
            { key: 'customer_name', label: 'العميل' },
            { key: 'transaction_date', label: 'التاريخ', sortable: true },
            { key: 'status', label: 'الحالة', render: (v: string) => <FluentBadge label={STATUS_LABEL[v] || v} variant={STATUS_VARIANT[v] || 'info'} size="small" /> },
            { key: 'grand_total', label: 'الإجمالي', render: (v: any) => fmt(v) },
            { key: 'outstanding_amount', label: 'المتبقي', render: (v: any) => fmt(v) },
          ]}
          data={orders}
        />
      </div>

      <FluentPanel
        isOpen={panelOpen} onClose={() => setPanelOpen(false)} width="large"
        title={order?.id ? `أمر بيع ${order.so_number}` : 'أمر بيع جديد'}
        subtitle={order?.id ? STATUS_LABEL[order.status] : 'الخطوة 1: بيانات الأمر'}
        footer={
          <div className="flex items-center justify-between">
            <button onClick={() => setPanelOpen(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إغلاق</button>
            {!order?.id && (
              <button onClick={createDraft} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">إنشاء المسودة</button>
            )}
            {order?.id && order.status === 'Draft' && (
              <button onClick={() => transition('Submitted')} className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]"><Send size={14} /> اعتماد الأمر</button>
            )}
            {order?.id && order.status === 'Submitted' && (
              <div className="flex gap-2">
                <button onClick={() => transition('Cancelled')} className="flex items-center gap-2 px-4 py-2 text-sm text-[#a4262c] border border-[#a4262c] rounded-sm hover:bg-[#fdf2f2]"><XCircle size={14} /> إلغاء</button>
                <button onClick={() => transition('Delivered')} className="flex items-center gap-2 px-4 py-2 text-sm text-white bg-[#107c10] rounded-sm hover:bg-[#0e6e0e]"><Truck size={14} /> تسليم المخزون</button>
              </div>
            )}
          </div>
        }
      >
        {error && <div className="mb-4 flex items-start gap-2 rounded-md border border-[#a4262c]/30 bg-[#fdf2f2] px-3 py-2 text-sm text-[#a4262c]"><AlertTriangle size={16} className="mt-0.5 shrink-0" /> {error}</div>}
        {notice && <div className="mb-4 flex items-center gap-2 rounded-md border border-[#107c10]/30 bg-[#f3faf3] px-3 py-2 text-sm text-[#107c10]"><CheckCircle size={16} /> {notice}</div>}

        {order && !order.id && (
          <div className="space-y-3">
            <FluentFormField label="العميل" required>
              <FluentSelect value={order.customer || ''} onChange={(e) => setOrder({ ...order, customer: e.target.value })}>
                <option value="">— اختر عميلاً —</option>
                {customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </FluentSelect>
            </FluentFormField>
            <FluentFormField label="رقم أمر البيع" required>
              <FluentInput value={order.so_number || ''} onChange={(e) => setOrder({ ...order, so_number: e.target.value })} placeholder="SO-2026-001" />
            </FluentFormField>
            <FluentFormField label="تاريخ الأمر">
              <FluentInput type="date" value={order.transaction_date || ''} onChange={(e) => setOrder({ ...order, transaction_date: e.target.value })} />
            </FluentFormField>
            <FluentFormField label="المستودع" hint="مطلوب قبل التسليم">
              <FluentSelect value={order.warehouse || ''} onChange={(e) => setOrder({ ...order, warehouse: e.target.value })}>
                <option value="">— بلا —</option>
                {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
              </FluentSelect>
            </FluentFormField>
          </div>
        )}

        {order?.id && (
          <div className="space-y-5">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><span className="text-[#605e5c]">العميل: </span><span className="font-medium">{order.customer_name}</span></div>
              <div><span className="text-[#605e5c]">المستودع: </span><span className="font-medium">{order.warehouse_name || '—'}</span></div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-[#323130] mb-2">بنود الأمر</h3>
              <table className="w-full text-sm border border-[#e1dfdd] rounded-sm overflow-hidden">
                <thead className="bg-[#faf9f8] text-[#605e5c]">
                  <tr>
                    <th className="text-right px-2 py-1.5 font-medium">الصنف</th>
                    <th className="text-right px-2 py-1.5 font-medium">الكمية</th>
                    <th className="text-right px-2 py-1.5 font-medium">السعر</th>
                    <th className="text-right px-2 py-1.5 font-medium">الإجمالي</th>
                    {order.status === 'Draft' && <th className="w-8"></th>}
                  </tr>
                </thead>
                <tbody>
                  {lines.map((l) => (
                    <tr key={l.id} className="border-t border-[#e1dfdd]">
                      <td className="px-2 py-1.5">{l.item_name || itemsById[l.item]?.item_name}</td>
                      <td className="px-2 py-1.5">{l.qty}</td>
                      <td className="px-2 py-1.5">{fmt(l.rate)}</td>
                      <td className="px-2 py-1.5 font-mono">{fmt(l.amount)}</td>
                      {order.status === 'Draft' && (
                        <td className="px-2 py-1.5">
                          <button onClick={() => removeLine(l.id)} className="text-[#a4262c] hover:bg-[#fdf2f2] p-1 rounded"><Trash2 size={14} /></button>
                        </td>
                      )}
                    </tr>
                  ))}
                  {lines.length === 0 && (
                    <tr><td colSpan={5} className="px-2 py-3 text-center text-[#605e5c]">لا توجد بنود بعد</td></tr>
                  )}
                </tbody>
              </table>

              {order.status === 'Draft' && (
                <div className="flex items-end gap-2 mt-2">
                  <div className="flex-1">
                    <FluentSelect value={newLine.item} onChange={(e) => setNewLine({ ...newLine, item: e.target.value })}>
                      <option value="">— اختر صنفاً —</option>
                      {items.map((i) => <option key={i.id} value={i.id}>{i.item_code} — {i.item_name}</option>)}
                    </FluentSelect>
                  </div>
                  <FluentInput type="number" step="0.01" className="w-24" placeholder="الكمية" value={newLine.qty} onChange={(e) => setNewLine({ ...newLine, qty: e.target.value })} />
                  <FluentInput type="number" step="0.01" className="w-28" placeholder="السعر" value={newLine.rate} onChange={(e) => setNewLine({ ...newLine, rate: e.target.value })} />
                  <button onClick={addLine} className="px-3 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe] whitespace-nowrap">إضافة</button>
                </div>
              )}
            </div>

            <div className="rounded-md bg-[#f3f2f1] p-3 text-sm space-y-1">
              <div className="flex justify-between text-[#605e5c]"><span>الكمية الإجمالية</span><span className="font-mono">{fmt(order.total_qty)}</span></div>
              <div className="flex justify-between text-[#605e5c]"><span>المجموع قبل الضريبة</span><span className="font-mono">{fmt(order.total_amount)}</span></div>
              <div className="flex justify-between font-bold text-[#323130] border-t border-[#e1dfdd] pt-1"><span>الإجمالي الكلي</span><span className="font-mono">{fmt(order.grand_total)}</span></div>
              <div className="flex justify-between text-[#605e5c]"><span>المدفوع</span><span className="font-mono">{fmt(order.total_paid)}</span></div>
              <div className="flex justify-between text-[#a4262c]"><span>المتبقي</span><span className="font-mono">{fmt(order.outstanding_amount)}</span></div>
            </div>
          </div>
        )}
      </FluentPanel>
    </div>
  );
}

function formatApiError(e: any): string {
  const data = e?.response?.data;
  if (!data) return 'حدث خطأ غير متوقع.';
  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  const parts: string[] = [];
  for (const [k, v] of Object.entries(data)) {
    parts.push(Array.isArray(v) ? v.join(' ') : String(v));
  }
  return parts.join(' — ') || 'حدث خطأ غير متوقع.';
}
