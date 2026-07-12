// pages/Valuation/ValuationPage.tsx
import { useEffect, useState } from 'react';
import { Calculator, RefreshCw, Layers } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { stockApi } from '../../services/api';

const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function ValuationPage() {
  const [data, setData] = useState<any>({ rows: [], totals: {} });
  const [loading, setLoading] = useState(true);
  const reload = () => { setLoading(true); stockApi.valuation().then(setData).catch(() => {}).finally(() => setLoading(false)); };
  useEffect(reload, []);

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="تقييم المخزون" subtitle="Inventory Valuation — FIFO / LIFO / المتوسط المتحرك"
        commands={[{ id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload }]} />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <FluentStatsCard title="القيمة (FIFO)" value={`${fmt(data.totals.fifo_value)} ر.س`} icon={<Layers size={20} />} color="blue" />
          <FluentStatsCard title="القيمة (LIFO)" value={`${fmt(data.totals.lifo_value)} ر.س`} icon={<Layers size={20} />} color="purple" />
          <FluentStatsCard title="القيمة (المتوسط المتحرك)" value={`${fmt(data.totals.moving_avg_value)} ر.س`} icon={<Calculator size={20} />} color="green" />
        </div>

        <FluentCard>
          <p className="text-sm text-[#605e5c] mb-2">
            تُحتسب القيمة من دفتر حركات المخزون (استلام/صرف). كل طريقة تعطي قيمة مختلفة للمخزون المتبقّي — اختر ما يناسب سياستك المحاسبية.
          </p>
        </FluentCard>

        <FluentTable
          title="التقييم حسب الصنف"
          subtitle={loading ? 'جارٍ التحميل…' : `${data.rows.length} صنف`}
          columns={[
            { key: 'item_code', label: 'رمز الصنف', sortable: true },
            { key: 'item_name', label: 'الاسم' },
            { key: 'closing_qty', label: 'الرصيد', sortable: true },
            { key: 'fifo_value', label: 'FIFO', render: (v: any) => fmt(v) },
            { key: 'lifo_value', label: 'LIFO', render: (v: any) => fmt(v) },
            { key: 'moving_avg_value', label: 'متوسط متحرك', render: (v: any) => fmt(v) },
            { key: 'moving_avg_cost', label: 'متوسط التكلفة', render: (v: any) => fmt(v) },
          ]}
          data={data.rows}
        />
      </div>
    </div>
  );
}
