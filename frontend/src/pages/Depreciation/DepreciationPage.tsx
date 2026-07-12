// pages/Depreciation/DepreciationPage.tsx
import { useEffect, useState } from 'react';
import { TrendingDown, RefreshCw } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { depreciationApi } from '../../services/api';

const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function DepreciationPage() {
  const [assets, setAssets] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [schedule, setSchedule] = useState<any[]>([]);

  useEffect(() => { depreciationApi.assets().then((a) => { setAssets(a); if (a[0]) pick(a[0]); }).catch(() => {}); }, []);
  const pick = (a: any) => { setSelected(a); depreciationApi.schedule(a.id).then((r) => setSchedule(r.schedule)).catch(() => setSchedule([])); };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="إهلاك الأصول" subtitle="Depreciation — جدول الإهلاك (قسط ثابت / متناقص)"
        commands={[{ id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: () => depreciationApi.assets().then(setAssets) }]} />
      <div className="p-6 grid grid-cols-1 lg:grid-cols-4 gap-6">
        <FluentCard>
          <h3 className="text-sm font-semibold text-[#605e5c] mb-3">الأصول ({assets.length})</h3>
          <div className="space-y-1">
            {assets.map((a) => (
              <button key={a.id} onClick={() => pick(a)}
                className={`w-full text-right px-3 py-2 rounded-md text-sm ${selected?.id === a.id ? 'bg-[#eff6fc] text-[#0078d4] font-medium' : 'text-[#323130] hover:bg-[#f3f2f1]'}`}>
                <div>{a.name}</div>
                <div className="text-xs text-[#605e5c]">{fmt(a.cost)} ر.س — {a.useful_life_years} سنوات</div>
              </button>
            ))}
          </div>
        </FluentCard>

        <div className="lg:col-span-3 space-y-4">
          {selected && (
            <FluentCard>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-semibold text-[#323130]">{selected.name}</h3>
                  <p className="text-sm text-[#605e5c]">التكلفة {fmt(selected.cost)} — القيمة المتبقية {fmt(selected.salvage_value)} — {selected.useful_life_years} سنوات</p>
                </div>
                <FluentBadge label={selected.method === 'declining' ? 'قسط متناقص' : 'قسط ثابت'} variant="info" size="small" />
              </div>
            </FluentCard>
          )}
          <FluentTable
            title="جدول الإهلاك السنوي"
            subtitle={`${schedule.length} سنوات`}
            columns={[
              { key: 'year', label: 'السنة', sortable: true },
              { key: 'depreciation', label: 'إهلاك السنة', render: (v: any) => fmt(v) },
              { key: 'accumulated', label: 'مجمّع الإهلاك', render: (v: any) => fmt(v) },
              { key: 'book_value', label: 'القيمة الدفترية', render: (v: any) => <span className="font-semibold">{fmt(v)}</span> },
            ]}
            data={schedule}
          />
        </div>
      </div>
    </div>
  );
}
