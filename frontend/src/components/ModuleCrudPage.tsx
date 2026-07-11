// components/ModuleCrudPage.tsx
import { ReactNode, useMemo, useState } from 'react';
import { Plus, RefreshCw, Download, Trash2, Boxes, CheckCircle } from 'lucide-react';
import { FluentCommandBar } from './FluentUI/FluentCommandBar';
import { FluentCard } from './FluentUI/FluentCard';
import { FluentTable } from './FluentUI/FluentTable';
import { FluentSearchBox } from './FluentUI/FluentSearchBox';
import { FluentStatsCard } from './FluentUI/FluentStatsCard';
import { FluentPanel } from './FluentUI/FluentPanel';
import { FluentBadge } from './FluentUI/FluentBadge';
import { ModuleForm } from './ModuleForm';
import { useModuleRecords } from '../hooks/useModuleRecords';
import { exportToCsv } from '../utils/exportCsv';
import type { FieldDef } from '../config/moduleFields';

interface Props {
  module: string;
  fields: FieldDef[];
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  newLabel?: string;
}

export function ModuleCrudPage({ module, fields, title, subtitle, icon, newLabel = 'إضافة' }: Props) {
  const { records, loading, save, remove } = useModuleRecords(module);
  const [query, setQuery] = useState('');
  const [showPanel, setShowPanel] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [saving, setSaving] = useState(false);

  const nameKey = fields[1]?.key || fields[0]?.key;
  const codeKey = fields[0]?.key;
  const hasStatus = fields.some((f) => f.key === 'status');

  const filtered = useMemo(() => {
    if (!query) return records;
    const q = query.toLowerCase();
    return records.filter((r) =>
      Object.values(r).some((v) => String(v ?? '').toLowerCase().includes(q))
    );
  }, [records, query]);

  const columns = useMemo(() => {
    const cols: any[] = fields.slice(0, 6).map((f) => ({
      key: f.key,
      label: f.label,
      sortable: true,
      render: f.key === 'status'
        ? (v: string) => (v ? <FluentBadge label={v} variant={v === 'Active' || v === 'Approved' ? 'success' : v === 'Inactive' || v === 'Closed' ? 'error' : 'warning'} size="small" /> : null)
        : f.type === 'checkbox'
        ? (v: any) => (v ? '✓' : '—')
        : undefined,
    }));
    cols.push({
      key: '__actions',
      label: '',
      render: (_: any, row: any) => (
        <button
          onClick={(e) => { e.stopPropagation(); if (row.id) remove(row.id); }}
          className="text-[#a4262c] hover:bg-[#fdf2f2] p-1 rounded"
          title="حذف"
        >
          <Trash2 size={14} />
        </button>
      ),
    });
    return cols;
  }, [fields, remove]);

  const openNew = () => { setEditing({}); setShowPanel(true); };
  const openEdit = (row: any) => { setEditing(row); setShowPanel(true); };

  const doSave = async () => {
    setSaving(true);
    try {
      await save(editing);
      setShowPanel(false);
      setEditing(null);
    } catch {
      alert('تعذّر الحفظ');
    } finally {
      setSaving(false);
    }
  };

  const activeCount = hasStatus ? records.filter((r) => r.status === 'Active' || r.status === 'Approved').length : 0;

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar
        title={title}
        subtitle={subtitle}
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: () => window.location.reload() },
          { id: 'export', label: 'تصدير', icon: <Download size={16} />, variant: 'secondary', onClick: () => exportToCsv(records, `${module}.csv`) },
          { id: 'new', label: newLabel, icon: <Plus size={16} />, variant: 'primary', onClick: openNew },
        ]}
      />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <FluentStatsCard title="إجمالي السجلات" value={records.length} icon={icon || <Boxes size={20} />} color="blue" />
          {hasStatus && <FluentStatsCard title="نشط" value={activeCount} icon={<CheckCircle size={20} />} color="green" />}
          <FluentStatsCard title="المعروضة" value={filtered.length} icon={<Boxes size={20} />} color="purple" />
        </div>

        <FluentCard padding="small">
          <FluentSearchBox value={query} onChange={setQuery} placeholder={`بحث في ${title}...`} className="w-80" />
        </FluentCard>

        <FluentTable
          title={title}
          subtitle={loading ? 'جارٍ التحميل…' : `${filtered.length} سجل`}
          columns={columns}
          data={filtered}
          onRowClick={openEdit}
        />

        {records.length === 0 && !loading && (
          <div className="text-center text-[#605e5c] py-8">
            لا توجد سجلات بعد — اضغط «{newLabel}» لإضافة أول سجل.
          </div>
        )}
      </div>

      <FluentPanel
        isOpen={showPanel}
        onClose={() => setShowPanel(false)}
        title={editing?.id ? (editing[nameKey] || 'تعديل السجل') : `${newLabel} جديد`}
        footer={
          <div className="flex gap-2 justify-end">
            <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
            <button onClick={doSave} disabled={saving} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe] disabled:opacity-60">
              {saving ? 'جارٍ الحفظ…' : 'حفظ'}
            </button>
          </div>
        }
      >
        {editing && <ModuleForm fields={fields} value={editing} onChange={setEditing} />}
      </FluentPanel>
    </div>
  );
}

export default ModuleCrudPage;
