// pages/Reorder/ReorderPage.tsx
import { useEffect, useState } from 'react';
import { AlertTriangle, RefreshCw, PackageCheck } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { recordsApi } from '../../services/api';

export default function ReorderPage() {
  const [data, setData] = useState<any>({ count: 0, alerts: [] });
  const [loading, setLoading] = useState(true);
  const reload = () => { setLoading(true); recordsApi.lowStock().then(setData).catch(() => {}).finally(() => setLoading(false)); };
  useEffect(reload, []);

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="إعادة الطلب" subtitle="Auto-Reorder — أصناف وصلت حد إعادة الطلب"
        commands={[{ id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload }]} />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <FluentStatsCard title="أصناف تحتاج طلب" value={data.count} icon={<AlertTriangle size={20} />} color={data.count > 0 ? 'red' : 'green'} />
          <FluentStatsCard title="إجمالي الكمية المقترحة" value={data.alerts.reduce((s: number, a: any) => s + Number(a.suggested_order_qty || 0), 0)} icon={<PackageCheck size={20} />} color="blue" />
        </div>

        {data.count === 0 && !loading ? (
          <FluentCard>
            <div className="text-center text-[#107c10] py-8 flex flex-col items-center gap-2">
              <PackageCheck size={32} /> جميع الأصناف فوق حد إعادة الطلب — لا حاجة لطلب.
            </div>
          </FluentCard>
        ) : (
          <FluentTable
            title="تنبيهات إعادة الطلب"
            subtitle={loading ? 'جارٍ التحميل…' : `${data.count} صنف`}
            columns={[
              { key: 'item_code', label: 'رمز الصنف', sortable: true },
              { key: 'name', label: 'الاسم' },
              { key: 'warehouse', label: 'المستودع' },
              { key: 'current_stock', label: 'المخزون الحالي', render: (v: any) => <span className="text-[#a4262c] font-semibold">{v}</span> },
              { key: 'reorder_level', label: 'حد إعادة الطلب' },
              { key: 'suggested_order_qty', label: 'الكمية المقترحة', render: (v: any) => <FluentBadge label={`اطلب ${v}`} variant="warning" size="small" /> },
            ]}
            data={data.alerts}
          />
        )}
      </div>
    </div>
  );
}
