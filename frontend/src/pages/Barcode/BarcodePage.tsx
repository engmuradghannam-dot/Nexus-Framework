// pages/Barcode/BarcodePage.tsx
import { useEffect, useRef, useState } from 'react';
import JsBarcode from 'jsbarcode';
import { Barcode as BarcodeIcon, RefreshCw, Printer, Search } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { recordsApi } from '../../services/api';

function Label({ code, name, price }: { code: string; name: string; price?: any }) {
  const ref = useRef<SVGSVGElement>(null);
  useEffect(() => {
    if (ref.current && code) {
      try { JsBarcode(ref.current, code, { format: 'CODE128', width: 1.6, height: 48, fontSize: 12, margin: 4 }); } catch { /* invalid code */ }
    }
  }, [code]);
  return (
    <div className="border border-[#e1dfdd] rounded-md p-3 text-center bg-white break-inside-avoid">
      <div className="text-sm font-semibold text-[#323130] truncate">{name}</div>
      <svg ref={ref} className="mx-auto" />
      {price != null && price !== '' && <div className="text-sm font-bold text-[#0078d4]">{Number(price).toLocaleString('en-US')} ر.س</div>}
    </div>
  );
}

export default function BarcodePage() {
  const [items, setItems] = useState<any[]>([]);
  const [query, setQuery] = useState('');

  const reload = () => recordsApi.list('inventory').then((rows: any[]) => setItems(rows.map((r) => r.data || r))).catch(() => setItems([]));
  useEffect(reload, []);

  const filtered = items.filter((it) => {
    const s = `${it.item_code || ''} ${it.arabic_name || ''} ${it.english_name || ''}`.toLowerCase();
    return s.includes(query.toLowerCase());
  });

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="الباركود" subtitle="Barcode Labels — ملصقات الأصناف (Code 128)"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'print', label: 'طباعة الملصقات', icon: <Printer size={16} />, variant: 'primary', onClick: () => window.print() },
        ]} />
      <div className="p-6 space-y-4">
        <FluentCard>
          <div className="flex items-center gap-2">
            <Search size={16} className="text-[#605e5c]" />
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="بحث عن صنف…"
              className="flex-1 bg-transparent text-sm outline-none py-1" />
            <span className="text-xs text-[#605e5c]">{filtered.length} صنف</span>
          </div>
        </FluentCard>

        {filtered.length === 0 ? (
          <FluentCard><div className="text-center text-[#605e5c] py-8 flex flex-col items-center gap-2"><BarcodeIcon size={28} /> لا أصناف — أضف أصنافاً في المخزون أولاً.</div></FluentCard>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {filtered.map((it, i) => (
              <Label key={i} code={it.item_code || it.sku || `ITEM-${i}`} name={it.arabic_name || it.english_name || 'صنف'} price={it.selling_price} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
