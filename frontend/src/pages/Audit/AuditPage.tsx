// pages/Audit/AuditPage.tsx
import { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { auditApi } from '../../services/api';

const actionMeta: Record<string, { label: string; variant: any }> = {
  create: { label: 'إنشاء', variant: 'success' },
  update: { label: 'تعديل', variant: 'warning' },
  delete: { label: 'حذف', variant: 'error' },
};

export default function AuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => { auditApi.logs().then(setLogs).catch(() => {}).finally(() => setLoading(false)); }, []);

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="سجل التدقيق" subtitle="Audit Trail — من عدّل ماذا ومتى"
        commands={[{ id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: () => window.location.reload() }]} />
      <div className="p-6">
        <FluentTable
          title="آخر العمليات"
          subtitle={loading ? 'جارٍ التحميل…' : `${logs.length} عملية`}
          columns={[
            { key: 'timestamp', label: 'الوقت', sortable: true, render: (v: string) => new Date(v).toLocaleString('ar-SA') },
            { key: 'user_email', label: 'المستخدم' },
            { key: 'action', label: 'العملية', render: (v: string) => { const m = actionMeta[v]; return m ? <FluentBadge label={m.label} variant={m.variant} size="small" /> : v; } },
            { key: 'module', label: 'الوحدة' },
            { key: 'object_ref', label: 'المرجع' },
            { key: 'ip_address', label: 'IP' },
          ]}
          data={logs}
          emptyMessage="لا توجد عمليات مسجّلة بعد"
        />
      </div>
    </div>
  );
}
