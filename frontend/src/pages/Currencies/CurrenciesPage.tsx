// pages/Currencies/CurrenciesPage.tsx
import { useEffect, useState } from 'react';
import { Coins, RefreshCw, ArrowLeftRight } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { currenciesApi } from '../../services/api';

export default function CurrenciesPage() {
  const [currencies, setCurrencies] = useState<any[]>([]);
  const [amount, setAmount] = useState('100');
  const [from, setFrom] = useState('USD');
  const [to, setTo] = useState('SAR');
  const [result, setResult] = useState<number | null>(null);

  const reload = () => currenciesApi.list().then(setCurrencies).catch(() => {});
  useEffect(reload, []);
  useEffect(() => {
    if (!amount) { setResult(null); return; }
    currenciesApi.convert(amount, from, to).then((r) => setResult(r.result)).catch(() => setResult(null));
  }, [amount, from, to]);

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="العملات وأسعار الصرف" subtitle="Multi-currency — العملة الأساسية: الريال السعودي"
        commands={[{ id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload }]} />
      <div className="p-6 space-y-6">
        <FluentCard>
          <h3 className="text-sm font-semibold text-[#323130] mb-3 flex items-center gap-2"><ArrowLeftRight size={16} /> محوّل العملات</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
            <FluentFormField label="المبلغ"><FluentInput type="number" value={amount} onChange={(e) => setAmount(e.target.value)} /></FluentFormField>
            <FluentFormField label="من">
              <FluentSelect value={from} onChange={(e) => setFrom(e.target.value)}>
                {currencies.map((c) => <option key={c.code} value={c.code}>{c.code} — {c.name_ar || c.name}</option>)}
              </FluentSelect>
            </FluentFormField>
            <FluentFormField label="إلى">
              <FluentSelect value={to} onChange={(e) => setTo(e.target.value)}>
                {currencies.map((c) => <option key={c.code} value={c.code}>{c.code} — {c.name_ar || c.name}</option>)}
              </FluentSelect>
            </FluentFormField>
            <div className="rounded-md bg-[#eff6fc] p-3 text-center">
              <div className="text-xs text-[#605e5c]">النتيجة</div>
              <div className="text-lg font-bold text-[#0078d4]">{result !== null ? result.toLocaleString('en-US', { minimumFractionDigits: 2 }) : '—'} {to}</div>
            </div>
          </div>
        </FluentCard>

        <FluentTable
          title="العملات المدعومة"
          subtitle={`${currencies.length} عملة — السعر مقابل الريال`}
          columns={[
            { key: 'code', label: 'الرمز', sortable: true },
            { key: 'name_ar', label: 'الاسم' },
            { key: 'symbol', label: 'الرمز المختصر' },
            { key: 'rate_to_base', label: '1 وحدة = (ريال)', render: (v: any) => Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 }) },
            { key: 'is_base', label: 'أساسية', render: (v: boolean) => v ? <FluentBadge label="أساسية" variant="success" size="small" /> : '' },
          ]}
          data={currencies}
        />
      </div>
    </div>
  );
}
