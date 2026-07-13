// pages/Warehouses/WarehousesPage.tsx
import { useEffect, useMemo, useState } from 'react';
import { Warehouse as WarehouseIcon, Building2, Plus, RefreshCw, AlertTriangle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { branchesApi, warehousesApi, companyProfilesApi } from '../../services/api';

export default function WarehousesPage() {
  const [branches, setBranches] = useState<any[]>([]);
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [companies, setCompanies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [branchPanel, setBranchPanel] = useState(false);
  const [newBranch, setNewBranch] = useState<any>({});
  const [whPanel, setWhPanel] = useState(false);
  const [newWh, setNewWh] = useState<any>({});

  const reload = () => {
    setLoading(true);
    Promise.all([branchesApi.list(), warehousesApi.list()])
      .then(([b, w]) => { setBranches(b); setWarehouses(w); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    reload();
    companyProfilesApi.list().then(setCompanies).catch(() => {});
  }, []);

  const stats = useMemo(() => ({
    branches: branches.length,
    warehouses: warehouses.length,
    capacity: warehouses.reduce((s, w) => s + Number(w.capacity || 0), 0),
  }), [branches, warehouses]);

  const openNewBranch = () => {
    setNewBranch({ company: companies.length === 1 ? companies[0].id : '', name: '', code: '', address: '' });
    setError('');
    setBranchPanel(true);
  };
  const saveBranch = async () => {
    try {
      await branchesApi.create(newBranch);
      setBranchPanel(false);
      reload();
    } catch (e: any) { setError(formatApiError(e)); }
  };

  const openNewWh = () => {
    setNewWh({ branch: branches.length === 1 ? branches[0].id : '', name: '', code: '', capacity: 0 });
    setError('');
    setWhPanel(true);
  };
  const saveWh = async () => {
    try {
      await warehousesApi.create(newWh);
      setWhPanel(false);
      reload();
    } catch (e: any) { setError(formatApiError(e)); }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar
        title="الفروع والمستودعات" subtitle="Branches & Warehouses — الهيكل التنظيمي والمخزني"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new-branch', label: 'فرع جديد', icon: <Plus size={16} />, variant: 'secondary', onClick: openNewBranch },
          { id: 'new-wh', label: 'مستودع جديد', icon: <Plus size={16} />, variant: 'primary', onClick: openNewWh },
        ]}
      />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-3 gap-4">
          <FluentStatsCard title="عدد الفروع" value={stats.branches} icon={<Building2 size={20} />} color="blue" />
          <FluentStatsCard title="عدد المستودعات" value={stats.warehouses} icon={<WarehouseIcon size={20} />} color="purple" />
          <FluentStatsCard title="إجمالي السعة" value={stats.capacity} icon={<WarehouseIcon size={20} />} color="green" />
        </div>

        <FluentTable
          title="الفروع"
          subtitle={loading ? 'جارٍ التحميل…' : `${branches.length} فرع`}
          columns={[
            { key: 'name', label: 'اسم الفرع', sortable: true },
            { key: 'code', label: 'الرمز' },
            { key: 'company_name', label: 'الشركة' },
            { key: 'address', label: 'العنوان' },
            { key: 'warehouse_count', label: 'عدد المستودعات' },
          ]}
          data={branches}
        />

        <FluentTable
          title="المستودعات"
          subtitle={loading ? 'جارٍ التحميل…' : `${warehouses.length} مستودع`}
          columns={[
            { key: 'name', label: 'اسم المستودع', sortable: true },
            { key: 'code', label: 'الرمز' },
            { key: 'branch_name', label: 'الفرع' },
            { key: 'capacity', label: 'السعة' },
            { key: 'current_occupancy', label: 'الإشغال الحالي' },
            { key: 'occupancy_rate', label: 'نسبة الإشغال', render: (v: any) => `${v}%` },
          ]}
          data={warehouses}
        />
      </div>

      <FluentPanel isOpen={branchPanel} onClose={() => setBranchPanel(false)} title="فرع جديد"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setBranchPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={saveBranch} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        {error && <div className="mb-4 flex items-start gap-2 rounded-md border border-[#a4262c]/30 bg-[#fdf2f2] px-3 py-2 text-sm text-[#a4262c]"><AlertTriangle size={16} className="mt-0.5 shrink-0" /> {error}</div>}
        <div className="space-y-3">
          <FluentFormField label="الشركة" required>
            <FluentSelect value={newBranch.company || ''} onChange={(e) => setNewBranch({ ...newBranch, company: e.target.value })}>
              <option value="">— اختر شركة —</option>
              {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </FluentSelect>
          </FluentFormField>
          <FluentFormField label="اسم الفرع" required><FluentInput value={newBranch.name || ''} onChange={(e) => setNewBranch({ ...newBranch, name: e.target.value })} /></FluentFormField>
          <FluentFormField label="رمز الفرع" required><FluentInput value={newBranch.code || ''} onChange={(e) => setNewBranch({ ...newBranch, code: e.target.value })} placeholder="BR-01" /></FluentFormField>
          <FluentFormField label="العنوان" required><FluentInput value={newBranch.address || ''} onChange={(e) => setNewBranch({ ...newBranch, address: e.target.value })} /></FluentFormField>
        </div>
      </FluentPanel>

      <FluentPanel isOpen={whPanel} onClose={() => setWhPanel(false)} title="مستودع جديد"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setWhPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={saveWh} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        {error && <div className="mb-4 flex items-start gap-2 rounded-md border border-[#a4262c]/30 bg-[#fdf2f2] px-3 py-2 text-sm text-[#a4262c]"><AlertTriangle size={16} className="mt-0.5 shrink-0" /> {error}</div>}
        <div className="space-y-3">
          <FluentFormField label="الفرع" required>
            <FluentSelect value={newWh.branch || ''} onChange={(e) => setNewWh({ ...newWh, branch: e.target.value })}>
              <option value="">— اختر فرعاً —</option>
              {branches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </FluentSelect>
          </FluentFormField>
          <FluentFormField label="اسم المستودع" required><FluentInput value={newWh.name || ''} onChange={(e) => setNewWh({ ...newWh, name: e.target.value })} /></FluentFormField>
          <FluentFormField label="رمز المستودع" required><FluentInput value={newWh.code || ''} onChange={(e) => setNewWh({ ...newWh, code: e.target.value })} placeholder="WH-01" /></FluentFormField>
          <FluentFormField label="السعة"><FluentInput type="number" value={newWh.capacity || 0} onChange={(e) => setNewWh({ ...newWh, capacity: e.target.value })} /></FluentFormField>
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
