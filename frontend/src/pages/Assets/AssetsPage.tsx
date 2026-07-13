// pages/Assets/AssetsPage.tsx
import { useEffect, useMemo, useState } from 'react';
import { Briefcase, Plus, RefreshCw, Send, Wrench, Trash, AlertTriangle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { assetsApi } from '../../services/api';

const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const STATUS_LABEL: Record<string, string> = { Draft: 'مسودة', Submitted: 'قيد الخدمة', 'In Maintenance': 'تحت الصيانة', Disposed: 'مستبعد' };
const STATUS_VARIANT: Record<string, any> = { Draft: 'warning', Submitted: 'success', 'In Maintenance': 'warning', Disposed: 'error' };
const NEXT_ACTIONS: Record<string, { status: string; label: string; icon: any }[]> = {
  Draft: [{ status: 'Submitted', label: 'تفعيل', icon: Send }],
  Submitted: [{ status: 'In Maintenance', label: 'إرسال للصيانة', icon: Wrench }, { status: 'Disposed', label: 'استبعاد', icon: Trash }],
  'In Maintenance': [{ status: 'Submitted', label: 'إعادة للخدمة', icon: Send }, { status: 'Disposed', label: 'استبعاد', icon: Trash }],
  Disposed: [],
};

export default function AssetsPage() {
  const [assets, setAssets] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [panel, setPanel] = useState(false);
  const [newAsset, setNewAsset] = useState<any>({});

  const reload = () => {
    setLoading(true);
    assetsApi.list().then(setAssets).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(() => {
    reload();
    assetsApi.categories().then(setCategories).catch(() => {});
  }, []);

  const stats = useMemo(() => ({
    total: assets.length,
    inService: assets.filter((a) => a.status === 'Submitted').length,
    bookValue: assets.reduce((s, a) => s + Number(a.book_value || 0), 0),
  }), [assets]);

  const openNew = () => {
    setNewAsset({ asset_name: '', asset_code: '', asset_type: 'Fixed', purchase_value: 0, salvage_value: 0, depreciation_method: 'Straight Line', depreciation_rate: 10 });
    setError('');
    setPanel(true);
  };
  const save = async () => {
    try { await assetsApi.create(newAsset); setPanel(false); reload(); }
    catch (e: any) { setError(formatApiError(e)); }
  };

  const transition = async (id: number, newStatus: string) => {
    try { await assetsApi.update(id, { status: newStatus }); reload(); }
    catch (e: any) { setError(formatApiError(e)); }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar
        title="الأصول الثابتة" subtitle="Fixed Assets — السجل والإهلاك"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new', label: 'أصل جديد', icon: <Plus size={16} />, variant: 'primary', onClick: openNew },
        ]}
      />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-3 gap-4">
          <FluentStatsCard title="عدد الأصول" value={stats.total} icon={<Briefcase size={20} />} color="blue" />
          <FluentStatsCard title="قيد الخدمة" value={stats.inService} icon={<Briefcase size={20} />} color="green" />
          <FluentStatsCard title="القيمة الدفترية الإجمالية" value={fmt(stats.bookValue)} icon={<Briefcase size={20} />} color="purple" />
        </div>

        {error && <div className="flex items-start gap-2 rounded-md border border-[#a4262c]/30 bg-[#fdf2f2] px-3 py-2 text-sm text-[#a4262c]"><AlertTriangle size={16} className="mt-0.5 shrink-0" /> {error}</div>}

        <FluentTable
          title="سجل الأصول"
          subtitle={loading ? 'جارٍ التحميل…' : `${assets.length} أصل`}
          columns={[
            { key: 'asset_code', label: 'الرمز', sortable: true },
            { key: 'asset_name', label: 'اسم الأصل', sortable: true },
            { key: 'category_name', label: 'الفئة' },
            { key: 'purchase_value', label: 'قيمة الشراء', render: (v: any) => fmt(v) },
            { key: 'accumulated_depreciation', label: 'الإهلاك المتراكم', render: (v: any) => fmt(v) },
            { key: 'book_value', label: 'القيمة الدفترية', render: (v: any) => fmt(v) },
            { key: 'status', label: 'الحالة', render: (v: string) => <FluentBadge label={STATUS_LABEL[v] || v} variant={STATUS_VARIANT[v] || 'info'} size="small" /> },
            {
              key: '__actions', label: '', render: (_: any, row: any) => (
                <div className="flex items-center gap-1 justify-end">
                  {(NEXT_ACTIONS[row.status] || []).map((a) => (
                    <button key={a.status} onClick={(e) => { e.stopPropagation(); transition(row.id, a.status); }}
                      className="flex items-center gap-1 text-xs text-[#0078d4] border border-[#0078d4] px-2 py-1 rounded hover:bg-[#eff6fc]">
                      <a.icon size={12} /> {a.label}
                    </button>
                  ))}
                </div>
              ),
            },
          ]}
          data={assets}
        />
      </div>

      <FluentPanel isOpen={panel} onClose={() => setPanel(false)} title="أصل جديد"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={save} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        <div className="space-y-3">
          <FluentFormField label="اسم الأصل" required><FluentInput value={newAsset.asset_name || ''} onChange={(e) => setNewAsset({ ...newAsset, asset_name: e.target.value })} /></FluentFormField>
          <FluentFormField label="رمز الأصل" required><FluentInput value={newAsset.asset_code || ''} onChange={(e) => setNewAsset({ ...newAsset, asset_code: e.target.value })} placeholder="AST-001" /></FluentFormField>
          <FluentFormField label="الفئة">
            <FluentSelect value={newAsset.category || ''} onChange={(e) => setNewAsset({ ...newAsset, category: e.target.value })}>
              <option value="">— بلا —</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </FluentSelect>
          </FluentFormField>
          <FluentFormField label="تاريخ الشراء"><FluentInput type="date" value={newAsset.purchase_date || ''} onChange={(e) => setNewAsset({ ...newAsset, purchase_date: e.target.value })} /></FluentFormField>
          <FluentFormField label="قيمة الشراء"><FluentInput type="number" step="0.01" value={newAsset.purchase_value || 0} onChange={(e) => setNewAsset({ ...newAsset, purchase_value: e.target.value })} /></FluentFormField>
          <FluentFormField label="القيمة التخريدية"><FluentInput type="number" step="0.01" value={newAsset.salvage_value || 0} onChange={(e) => setNewAsset({ ...newAsset, salvage_value: e.target.value })} /></FluentFormField>
          <FluentFormField label="طريقة الإهلاك">
            <FluentSelect value={newAsset.depreciation_method || 'Straight Line'} onChange={(e) => setNewAsset({ ...newAsset, depreciation_method: e.target.value })}>
              <option value="Straight Line">القسط الثابت</option>
              <option value="Declining Balance">الرصيد المتناقص</option>
              <option value="None">بدون إهلاك</option>
            </FluentSelect>
          </FluentFormField>
          <FluentFormField label="نسبة الإهلاك السنوية %"><FluentInput type="number" step="0.01" value={newAsset.depreciation_rate ?? 10} onChange={(e) => setNewAsset({ ...newAsset, depreciation_rate: e.target.value })} /></FluentFormField>
        </div>
      </FluentPanel>
    </div>
  );
}

function formatApiError(e: any): string {
  const data = e?.response?.data;
  if (!data) return 'حدث خطأ غير متوقع.';
  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  const parts: string[] = [];
  for (const [k, v] of Object.entries(data)) {
    parts.push(Array.isArray(v) ? v.join(' ') : String(v));
  }
  return parts.join(' — ') || 'حدث خطأ غير متوقع.';
}
