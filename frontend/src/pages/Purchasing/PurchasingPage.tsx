// pages/Purchasing/PurchasingPage.tsx
import { useEffect, useState } from 'react';
import { ShoppingBag, Plus, RefreshCw, Award, BarChart3, Trash2 } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { buyingApi } from '../../services/api';

const fmt = (n: any) => n == null ? '—' : Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const STATUS: Record<string, any> = {
  Draft: 'default', Sent: 'info', Quoted: 'warning', Awarded: 'success', Cancelled: 'danger',
};

export default function PurchasingPage() {
  const [rfqs, setRfqs] = useState<any[]>([]);
  const [items, setItems] = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [showRfq, setShowRfq] = useState(false);
  const [rfqForm, setRfqForm] = useState<any>({ lines: [{}] });
  const [selected, setSelected] = useState<any>(null);
  const [comparison, setComparison] = useState<any>(null);
  const [showQuote, setShowQuote] = useState(false);
  const [quoteForm, setQuoteForm] = useState<any>({});
  const [msg, setMsg] = useState('');

  const reload = () => buyingApi.rfqs().then(setRfqs).catch(() => setRfqs([]));
  useEffect(() => {
    reload();
    buyingApi.itemsList().then(setItems).catch(() => {});
    buyingApi.suppliers().then(setSuppliers).catch(() => {});
  }, []);

  const addLine = () => setRfqForm((f: any) => ({ ...f, lines: [...(f.lines || []), {}] }));
  const setLine = (i: number, k: string, v: any) => setRfqForm((f: any) => {
    const lines = [...f.lines]; lines[i] = { ...lines[i], [k]: v }; return { ...f, lines };
  });

  const saveRfq = async () => {
    try {
      const payload = {
        rfq_number: rfqForm.rfq_number, transaction_date: rfqForm.transaction_date,
        response_deadline: rfqForm.response_deadline || null,
        items: (rfqForm.lines || []).filter((l: any) => l.item && l.qty)
          .map((l: any) => ({ item: Number(l.item), qty: l.qty, target_rate: l.target_rate || null })),
      };
      await buyingApi.createRfq(payload);
      setShowRfq(false); setRfqForm({ lines: [{}] }); setMsg('تم إنشاء طلب عرض الأسعار'); reload();
    } catch { setMsg('تعذّر الحفظ — تأكد من الرقم والبنود'); }
  };

  const openCompare = async (rfq: any) => {
    setSelected(rfq);
    const c = await buyingApi.compareRfq(rfq.id).catch(() => null);
    setComparison(c);
  };

  const award = async (quotationId: number) => {
    if (!selected) return;
    try {
      const r = await buyingApi.awardRfq(selected.id, quotationId);
      setMsg(`تمت الترسية → أمر شراء ${r.po_number} بإجمالي ${fmt(r.total)}`);
      setComparison(null); setSelected(null); reload();
    } catch { setMsg('تعذّرت الترسية'); }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="دورة الشراء" subtitle="Purchasing — طلب عرض أسعار (RFQ) ← مقارنة الموردين ← ترسية ← أمر شراء ← استلام"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new', label: 'طلب عرض أسعار', icon: <Plus size={16} />, variant: 'primary', onClick: () => { setRfqForm({ lines: [{}], transaction_date: new Date().toISOString().slice(0, 10) }); setShowRfq(true); } },
        ]} />

      <div className="p-6 space-y-6">
        {msg && <div className="bg-[#dff6dd] text-[#0b6a0b] text-sm px-4 py-2 rounded-sm">{msg}</div>}

        <FluentTable
          title="طلبات عروض الأسعار"
          subtitle="أرسل الطلب لعدة موردين، قارن عروضهم على الإجمالي وآجال التسليم، ثم رسِّ الأفضل"
          columns={[
            { key: 'rfq_number', label: 'الرقم' },
            { key: 'transaction_date', label: 'التاريخ' },
            { key: 'quotation_count', label: 'عروض', render: (v: number) => <FluentBadge label={`${v || 0}`} variant="info" size="small" /> },
            { key: 'status', label: 'الحالة', render: (v: string) => <FluentBadge label={v} variant={STATUS[v] || 'default'} size="small" /> },
            { key: '__cmp', label: '', render: (_: any, r: any) => (
              <button onClick={(e) => { e.stopPropagation(); openCompare(r); }} className="flex items-center gap-1 text-[#0078d4] hover:bg-[#eff6fc] px-2 py-1 rounded text-xs">
                <BarChart3 size={14} /> قارن ورسِّ
              </button>
            ) },
          ]}
          data={rfqs}
          emptyMessage="لا طلبات عروض أسعار بعد — ابدأ بإنشاء طلب"
        />

        {selected && comparison && (
          <FluentCard>
            <div className="flex items-center justify-between mb-3">
              <div className="font-semibold text-sm text-[#323130]">مقارنة عروض {selected.rfq_number}</div>
              <button onClick={() => { setSelected(null); setComparison(null); }} className="text-xs text-[#605e5c] hover:underline">إغلاق</button>
            </div>
            {comparison.quotes?.length ? (
              <div className="space-y-2">
                <p className="text-xs text-[#605e5c]">مرتّبة بالإجمalي. الأرخص ليس دائماً الأفضل — انظر آجال التسليم وشروط الدفع.</p>
                {comparison.quotes.map((q: any) => (
                  <div key={q.quotation_id} className={`flex items-center justify-between border rounded-sm p-3 ${q.is_lowest_total ? 'border-[#0b6a0b]/40 bg-[#f3faf3]' : 'border-[#e1dfdd]'}`}>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{q.supplier}</span>
                        {q.is_lowest_total && <FluentBadge label="الأقل إجمالاً" variant="success" size="small" />}
                      </div>
                      <div className="text-xs text-[#605e5c] mt-0.5">
                        تسليم {q.lead_time_days ?? '—'} يوم · {q.payment_terms || '—'}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="font-semibold text-sm">{fmt(q.total)}</span>
                      {selected.status !== 'Awarded' && (
                        <button onClick={() => award(q.quotation_id)} className="flex items-center gap-1 bg-[#0078d4] text-white text-xs px-3 py-1.5 rounded hover:bg-[#106ebe]">
                          <Award size={14} /> رسِّ
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-[#605e5c]">لا عروض مستلمة بعد لهذا الطلب.</p>}
          </FluentCard>
        )}
      </div>

      <FluentPanel isOpen={showRfq} onClose={() => setShowRfq(false)} title="طلب عرض أسعار جديد"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setShowRfq(false)} className="px-4 py-2 text-sm border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={saveRfq} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        <div className="space-y-3">
          <FluentFormField label="رقم الطلب"><FluentInput value={rfqForm.rfq_number || ''} onChange={(e) => setRfqForm((f: any) => ({ ...f, rfq_number: e.target.value }))} placeholder="RFQ-0001" /></FluentFormField>
          <FluentFormField label="التاريخ"><FluentInput type="date" value={rfqForm.transaction_date || ''} onChange={(e) => setRfqForm((f: any) => ({ ...f, transaction_date: e.target.value }))} /></FluentFormField>
          <FluentFormField label="آخر موعد للردود"><FluentInput type="date" value={rfqForm.response_deadline || ''} onChange={(e) => setRfqForm((f: any) => ({ ...f, response_deadline: e.target.value }))} /></FluentFormField>
          <div className="border-t border-[#e1dfdd] pt-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">البنود المطلوبة</span>
              <button onClick={addLine} className="text-xs text-[#0078d4] hover:underline flex items-center gap-1"><Plus size={12} /> بند</button>
            </div>
            {(rfqForm.lines || []).map((l: any, i: number) => (
              <div key={i} className="flex gap-2 mb-2">
                <FluentSelect value={l.item || ''} onChange={(e) => setLine(i, 'item', e.target.value)} className="flex-1">
                  <option value="">— الصنف —</option>
                  {items.map((it) => <option key={it.id} value={it.id}>{it.item_name}</option>)}
                </FluentSelect>
                <FluentInput type="number" value={l.qty || ''} onChange={(e) => setLine(i, 'qty', e.target.value)} placeholder="كمية" className="w-24" />
              </div>
            ))}
          </div>
        </div>
      </FluentPanel>
    </div>
  );
}
