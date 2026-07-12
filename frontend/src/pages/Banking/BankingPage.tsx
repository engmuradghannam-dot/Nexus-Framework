// pages/Banking/BankingPage.tsx
import { useEffect, useState } from 'react';
import { Landmark, RefreshCw, CheckCircle2, Circle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { bankingApi } from '../../services/api';

const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function BankingPage() {
  const [accounts, setAccounts] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [txns, setTxns] = useState<any[]>([]);

  const loadAccounts = () => bankingApi.accounts().then((a) => { setAccounts(a); if (a[0] && !selected) pick(a[0]); else if (selected) { const u = a.find((x: any) => x.id === selected.id); if (u) setSelected(u); } }).catch(() => {});
  const pick = (a: any) => { setSelected(a); bankingApi.transactions(a.id).then(setTxns).catch(() => {}); };
  useEffect(() => { loadAccounts(); /* eslint-disable-next-line */ }, []);

  const toggle = async (id: number) => {
    await bankingApi.toggleReconcile(id);
    if (selected) { bankingApi.transactions(selected.id).then(setTxns); loadAccounts(); }
  };

  const bal = selected?.balances || {};

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="التسوية البنكية" subtitle="Bank Reconciliation — مطابقة كشف البنك مع الدفاتر"
        commands={[{ id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: loadAccounts }]} />
      <div className="p-6 space-y-6">
        <div className="flex gap-2 flex-wrap">
          {accounts.map((a) => (
            <button key={a.id} onClick={() => pick(a)}
              className={`px-4 py-2 rounded-md text-sm border ${selected?.id === a.id ? 'border-[#0078d4] bg-[#eff6fc] text-[#0078d4] font-medium' : 'border-[#e1dfdd] text-[#323130] hover:bg-[#f3f2f1]'}`}>
              <Landmark size={14} className="inline ml-1" /> {a.name}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <FluentStatsCard title="الرصيد الدفتري" value={fmt(bal.book_balance)} icon={<Landmark size={18} />} color="blue" />
          <FluentStatsCard title="الرصيد المسوّى" value={fmt(bal.reconciled_balance)} icon={<CheckCircle2 size={18} />} color="green" />
          <FluentStatsCard title="الفرق" value={fmt(bal.difference)} icon={<Circle size={18} />} color={Number(bal.difference) === 0 ? 'green' : 'orange'} />
          <FluentStatsCard title="حركات غير مسوّاة" value={bal.unreconciled_count ?? 0} icon={<Circle size={18} />} color={bal.unreconciled_count ? 'red' : 'green'} />
        </div>

        <FluentTable
          title="حركات كشف البنك"
          subtitle={`${txns.length} حركة — اضغط الحالة للتسوية`}
          columns={[
            { key: 'date', label: 'التاريخ', sortable: true },
            { key: 'description', label: 'الوصف' },
            { key: 'direction', label: 'النوع', render: (v: string) => <FluentBadge label={v === 'in' ? 'إيداع' : 'سحب'} variant={v === 'in' ? 'success' : 'warning'} size="small" /> },
            { key: 'amount', label: 'المبلغ', render: (v: any) => fmt(v) },
            { key: 'reconciled', label: 'التسوية', render: (v: boolean, row: any) => (
              <button onClick={(e) => { e.stopPropagation(); toggle(row.id); }}
                className={`flex items-center gap-1 text-xs px-2 py-1 rounded ${v ? 'text-[#107c10] bg-[#dff6dd]' : 'text-[#605e5c] bg-[#f3f2f1] hover:bg-[#edebe9]'}`}>
                {v ? <CheckCircle2 size={13} /> : <Circle size={13} />} {v ? 'مسوّاة' : 'غير مسوّاة'}
              </button>
            ) },
          ]}
          data={txns}
        />
      </div>
    </div>
  );
}
