// pages/Accounting/AccountingPage.tsx
import { useEffect, useState } from 'react';
import { Landmark, TrendingUp, Scale, BookOpen, FileText } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { accountingApi } from '../../services/api';

const TABS = [
  { id: 'statements', label: 'القوائم المالية', icon: TrendingUp },
  { id: 'trial', label: 'ميزان المراجعة', icon: Scale },
  { id: 'accounts', label: 'شجرة الحسابات', icon: BookOpen },
  { id: 'journal', label: 'القيود اليومية', icon: FileText },
];

const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function AccountingPage() {
  const [tab, setTab] = useState('statements');
  const [fs, setFs] = useState<any>(null);
  const [tb, setTb] = useState<any>(null);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [journal, setJournal] = useState<any[]>([]);

  useEffect(() => {
    accountingApi.financialStatements().then(setFs).catch(() => {});
    accountingApi.trialBalance().then(setTb).catch(() => {});
    accountingApi.accounts().then(setAccounts).catch(() => {});
    accountingApi.journalEntries().then(setJournal).catch(() => {});
  }, []);

  const is = fs?.income_statement;
  const bs = fs?.balance_sheet;

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="المحاسبة" subtitle="Accounting — القيد المزدوج والقوائم المالية"
        commands={[{ id: 'refresh', label: 'تحديث', icon: <TrendingUp size={16} />, variant: 'secondary', onClick: () => window.location.reload() }]} />

      <div className="p-6 space-y-6">
        {/* Tabs */}
        <div className="flex gap-1 border-b border-[#e1dfdd]">
          {TABS.map((t) => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2 text-sm border-b-2 -mb-px ${tab === t.id ? 'border-[#0078d4] text-[#0078d4] font-medium' : 'border-transparent text-[#605e5c] hover:text-[#323130]'}`}>
              <t.icon size={16} /> {t.label}
            </button>
          ))}
        </div>

        {/* Financial statements */}
        {tab === 'statements' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <FluentStatsCard title="الإيرادات" value={fmt(is?.total_income)} icon={<TrendingUp size={20} />} color="green" />
              <FluentStatsCard title="المصروفات" value={fmt(is?.total_expense)} icon={<TrendingUp size={20} />} color="red" />
              <FluentStatsCard title="صافي الدخل" value={fmt(is?.net_income)} icon={<TrendingUp size={20} />} color={Number(is?.net_income) >= 0 ? 'green' : 'red'} />
              <FluentStatsCard title="إجمالي الأصول" value={fmt(bs?.total_assets)} icon={<Landmark size={20} />} color="blue" />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <FluentCard>
                <h3 className="text-base font-semibold text-[#323130] mb-3">قائمة الدخل / Income Statement</h3>
                <Row label="إجمالي الإيرادات" value={fmt(is?.total_income)} />
                <Row label="إجمالي المصروفات" value={fmt(is?.total_expense)} />
                <div className="border-t border-[#e1dfdd] mt-2 pt-2">
                  <Row label="صافي الدخل" value={fmt(is?.net_income)} bold />
                </div>
              </FluentCard>
              <FluentCard>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-base font-semibold text-[#323130]">المركز المالي / Balance Sheet</h3>
                  {bs && <FluentBadge label={bs.balanced ? 'متوازن' : 'غير متوازن'} variant={bs.balanced ? 'success' : 'error'} size="small" />}
                </div>
                <Row label="إجمالي الأصول" value={fmt(bs?.total_assets)} />
                <Row label="إجمالي الخصوم" value={fmt(bs?.total_liabilities)} />
                <Row label="حقوق الملكية" value={fmt(bs?.total_equity)} />
                <div className="border-t border-[#e1dfdd] mt-2 pt-2">
                  <Row label="الخصوم + حقوق الملكية" value={fmt(Number(bs?.total_liabilities) + Number(bs?.total_equity))} bold />
                </div>
              </FluentCard>
            </div>
          </div>
        )}

        {/* Trial balance */}
        {tab === 'trial' && tb && (
          <FluentCard>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-semibold text-[#323130]">ميزان المراجعة</h3>
              <FluentBadge label={tb.balanced ? `متوازن: ${fmt(tb.total_debit)}` : 'غير متوازن'} variant={tb.balanced ? 'success' : 'error'} size="small" />
            </div>
            <FluentTable
              columns={[
                { key: 'account_number', label: 'رقم الحساب', sortable: true },
                { key: 'account_name', label: 'اسم الحساب', sortable: true },
                { key: 'root_type', label: 'النوع' },
                { key: 'debit_balance', label: 'مدين', render: (v: any) => fmt(v) },
                { key: 'credit_balance', label: 'دائن', render: (v: any) => fmt(v) },
              ]}
              data={tb.rows}
            />
          </FluentCard>
        )}

        {/* Chart of accounts */}
        {tab === 'accounts' && (
          <FluentTable
            title="شجرة الحسابات"
            subtitle={`${accounts.length} حساب`}
            columns={[
              { key: 'account_number', label: 'الرقم', sortable: true },
              { key: 'account_name', label: 'الاسم', sortable: true },
              { key: 'root_type', label: 'النوع', sortable: true },
              { key: 'is_group', label: 'مجموعة', render: (v: any) => (v ? '📁' : '') },
              { key: 'balance', label: 'الرصيد', render: (v: any) => fmt(v) },
            ]}
            data={accounts}
          />
        )}

        {/* Journal entries */}
        {tab === 'journal' && (
          <FluentTable
            title="القيود اليومية"
            subtitle={`${journal.length} قيد`}
            columns={[
              { key: 'entry_number', label: 'رقم القيد', sortable: true },
              { key: 'posting_date', label: 'التاريخ', sortable: true },
              { key: 'reference', label: 'البيان' },
              { key: 'amount', label: 'المبلغ', render: (v: any) => fmt(v) },
            ]}
            data={journal}
          />
        )}
      </div>
    </div>
  );
}

function Row({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <div className={`flex justify-between py-1.5 ${bold ? 'font-bold text-[#323130]' : 'text-[#605e5c]'}`}>
      <span>{label}</span>
      <span className="font-mono">{value}</span>
    </div>
  );
}
