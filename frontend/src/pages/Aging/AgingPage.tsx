// pages/Aging/AgingPage.tsx
import { useEffect, useState } from 'react';
import { RefreshCw, TrendingDown, Wallet } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { invoicingApi } from '../../services/api';

const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const BUCKETS = [
  { key: 'current', label: 'غير مستحق' },
  { key: 'd1_30', label: '1–30 يوم' },
  { key: 'd31_60', label: '31–60 يوم' },
  { key: 'd61_90', label: '61–90 يوم' },
  { key: 'd90_plus', label: '+90 يوم' },
];

export default function AgingPage() {
  const [type, setType] = useState<'sales' | 'purchase'>('sales');
  const [data, setData] = useState<any>({ buckets: {}, parties: [], total_outstanding: 0 });
  const [loading, setLoading] = useState(true);
  const reload = (t = type) => { setLoading(true); invoicingApi.aging(t).then(setData).catch(() => {}).finally(() => setLoading(false)); };
  useEffect(() => { reload(type); /* eslint-disable-next-line */ }, [type]);

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="تقادم الذمم" subtitle="Aging — أعمار الذمم المدينة والدائنة"
        commands={[{ id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: () => reload() }]} />
      <div className="p-6 space-y-6">
        <div className="flex gap-1 border-b border-[#e1dfdd]">
          {[['sales', 'ذمم مدينة (A/R)'], ['purchase', 'ذمم دائنة (A/P)']].map(([id, label]) => (
            <button key={id} onClick={() => setType(id as any)}
              className={`px-4 py-2 text-sm border-b-2 -mb-px ${type === id ? 'border-[#0078d4] text-[#0078d4] font-medium' : 'border-transparent text-[#605e5c]'}`}>{label}</button>
          ))}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
          <FluentStatsCard title="الإجمالي المستحق" value={fmt(data.total_outstanding)} icon={<Wallet size={18} />} color="blue" />
          {BUCKETS.map((b) => (
            <FluentStatsCard key={b.key} title={b.label} value={fmt(data.buckets[b.key])} icon={<TrendingDown size={18} />}
              color={b.key === 'd90_plus' ? 'red' : b.key === 'd61_90' ? 'orange' : 'green'} />
          ))}
        </div>

        <FluentTable
          title={type === 'sales' ? 'الذمم المدينة حسب العميل' : 'الذمم الدائنة حسب المورّد'}
          subtitle={loading ? 'جارٍ التحميل…' : `${data.parties.length} طرف — حتى ${data.as_of || ''}`}
          columns={[
            { key: 'party', label: 'الطرف', sortable: true },
            { key: 'current', label: 'غير مستحق', render: (v: any) => fmt(v) },
            { key: 'd1_30', label: '1–30', render: (v: any) => fmt(v) },
            { key: 'd31_60', label: '31–60', render: (v: any) => fmt(v) },
            { key: 'd61_90', label: '61–90', render: (v: any) => fmt(v) },
            { key: 'd90_plus', label: '+90', render: (v: any) => <span className="text-[#a4262c] font-semibold">{fmt(v)}</span> },
            { key: 'total', label: 'الإجمالي', render: (v: any) => <span className="font-semibold">{fmt(v)}</span> },
          ]}
          data={data.parties}
          emptyMessage="لا توجد ذمم مستحقة"
        />
      </div>
    </div>
  );
}
