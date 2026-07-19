// pages/Audit/AuditPage.tsx
import { useEffect, useState } from 'react';
import { RefreshCw, FileClock, Search } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentInput } from '../../components/FluentUI';
import { auditApi } from '../../services/api';

const actionMeta: Record<string, { label: string; variant: any }> = {
  create: { label: 'إنشاء', variant: 'success' },
  update: { label: 'تعديل', variant: 'warning' },
  delete: { label: 'حذف', variant: 'error' },
};
const opMeta: Record<string, { label: string; variant: any }> = {
  create: { label: 'إنشاء', variant: 'success' },
  update: { label: 'تعديل', variant: 'warning' },
  delete: { label: 'حذف', variant: 'danger' },
};

export default function AuditPage() {
  const [tab, setTab] = useState<'logs' | 'changes'>('logs');
  const [logs, setLogs] = useState<any[]>([]);
  const [changes, setChanges] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [fieldFilter, setFieldFilter] = useState('');
  const [detail, setDetail] = useState<any>(null);

  const load = () => {
    setLoading(true);
    auditApi.logs().then(setLogs).catch(() => {}).finally(() => setLoading(false));
    auditApi.changeDocs().then(setChanges).catch(() => {});
  };
  useEffect(load, []);

  // Field-level query — the whole point of CDPOS: find every change to a field.
  const filteredChanges = fieldFilter.trim()
    ? changes.filter((c) => (c.items || []).some((i: any) => i.field_name?.toLowerCase().includes(fieldFilter.trim().toLowerCase())))
    : changes;

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="سجل التدقيق" subtitle="Audit Trail — من عدّل ماذا ومتى (CDPOS/CDHDR)"
        commands={[{ id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: load }]} />

      <div className="p-6 space-y-4">
        <div className="flex gap-1 border-b border-[#e1dfdd]">
          {[['logs', 'العمليات'], ['changes', 'وثائق التغيير (حقلاً حقلاً)']].map(([k, label]: any) => (
            <button key={k} onClick={() => setTab(k)}
              className={`px-4 py-2 text-sm border-b-2 -mb-px ${tab === k ? 'border-[#0078d4] text-[#0078d4] font-medium' : 'border-transparent text-[#605e5c]'}`}>
              {label}
            </button>
          ))}
        </div>

        {tab === 'logs' && (
          <FluentTable
            title="آخر العمليات"
            subtitle={loading ? 'جارٍ التحميل…' : `${logs.length} عملية`}
            columns={[
              { key: 'timestamp', label: 'الوقت', sortable: true, render: (v: string) => new Date(v).toLocaleString('en-GB') },
              { key: 'user_email', label: 'المستخدم' },
              { key: 'action', label: 'العملية', render: (v: string) => { const m = actionMeta[v]; return m ? <FluentBadge label={m.label} variant={m.variant} size="small" /> : v; } },
              { key: 'module', label: 'الوحدة' },
              { key: 'object_ref', label: 'المرجع' },
              { key: 'ip_address', label: 'IP' },
            ]}
            data={logs}
            emptyMessage="لا توجد عمليات مسجّلة بعد"
          />
        )}

        {tab === 'changes' && (
          <div className="space-y-3">
            <FluentCard>
              <div className="flex items-center gap-2">
                <Search size={16} className="text-[#605e5c]" />
                <FluentInput value={fieldFilter} onChange={(e) => setFieldFilter(e.target.value)} placeholder="ابحث بالحقل — مثال: standard_rate، status" className="flex-1" />
              </div>
              <p className="text-xs text-[#605e5c] mt-2">
                جوهر CDPOS: كل تغيير مسجّل حقلاً حقلاً بقيمته القديمة والجديدة، فيمكن تتبّع «من غيّر هذا الحقل ومتى». الحقول الحسّاسة (الرواتب) تُتتبّع مع إخفاء قيمتها.
              </p>
            </FluentCard>
            <FluentTable
              title="وثائق التغيير"
              subtitle={`${filteredChanges.length} وثيقة${fieldFilter ? ' (مُصفّاة بالحقل)' : ''}`}
              columns={[
                { key: 'timestamp', label: 'الوقت', sortable: true, render: (v: string) => new Date(v).toLocaleString('en-GB') },
                { key: 'user_email', label: 'المستخدم' },
                { key: 'operation', label: 'العملية', render: (v: string) => { const m = opMeta[v]; return m ? <FluentBadge label={m.label} variant={m.variant} size="small" /> : v; } },
                { key: 'object_repr', label: 'الكائن' },
                { key: 'items', label: 'حقول متغيّرة', render: (v: any[]) => <FluentBadge label={`${v?.length || 0}`} variant="info" size="small" /> },
              ]}
              data={filteredChanges}
              onRowClick={(r: any) => setDetail(r)}
              emptyMessage={fieldFilter ? 'لا وثائق تطابق هذا الحقل' : 'لا وثائق تغيير بعد'}
            />
          </div>
        )}
      </div>

      {detail && (
        <FluentPanel isOpen={!!detail} onClose={() => setDetail(null)} title={detail.object_repr || 'وثيقة تغيير'}>
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm text-[#605e5c]">
              <FileClock size={15} />
              {new Date(detail.timestamp).toLocaleString('en-GB')} · {detail.user_email || 'نظام'}
            </div>
            <div className="text-sm font-medium text-[#323130]">الحقول المتغيّرة</div>
            <table className="w-full text-sm">
              <thead><tr className="text-[#605e5c] text-xs border-b border-[#e1dfdd]"><th className="text-right py-1">الحقل</th><th className="text-right py-1">قبل</th><th className="text-right py-1">بعد</th></tr></thead>
              <tbody>
                {(detail.items || []).map((i: any) => (
                  <tr key={i.id} className="border-b border-[#f3f2f1]">
                    <td className="py-1.5 font-mono text-xs">{i.field_name}</td>
                    <td className="py-1.5 text-[#a4262c]">{i.old_value ?? '—'}</td>
                    <td className="py-1.5 text-[#0b6a0b]">{i.new_value ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </FluentPanel>
      )}
    </div>
  );
}
