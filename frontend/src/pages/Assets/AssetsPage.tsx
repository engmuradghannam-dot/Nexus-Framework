// pages/Assets/AssetsPage.tsx
import { useState } from 'react';
import { ModuleForm } from '../../components/ModuleForm';
import { MODULE_FIELDS } from '../../config/moduleFields';
import { Briefcase, Plus, RefreshCw, Download, Building2, Wrench, CheckCircle, AlertTriangle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentSearchBox } from '../../components/FluentUI/FluentSearchBox';
import { FluentPanel, FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { exportToCsv } from '../../utils/exportCsv';

const assets = [
  { id: 'AST-001', name: 'مبنى الإدارة الرئيسي', category: 'عقارات', location: 'الرياض', value: 5000000, status: 'active', purchaseDate: '2020-01-15' },
  { id: 'AST-002', name: 'سيارة تويوتا لاندكروزر', category: 'مركبات', location: 'جدة', value: 250000, status: 'active', purchaseDate: '2024-03-20' },
  { id: 'AST-003', name: 'خادم Dell PowerEdge', category: 'تقنية', location: 'الرياض', value: 80000, status: 'maintenance', purchaseDate: '2023-06-10' },
  { id: 'AST-004', name: 'مكيف مركزي 10 طن', category: 'تكييف', location: 'الدمام', value: 35000, status: 'active', purchaseDate: '2024-01-05' },
  { id: 'AST-005', name: 'رافعة شوكية 3 طن', category: 'معدات', location: 'جدة', value: 120000, status: 'retired', purchaseDate: '2019-08-15' },
];

export default function AssetsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showPanel, setShowPanel] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<any>(null);

  const filtered = assets.filter(a => !searchQuery || a.name.includes(searchQuery) || a.id.includes(searchQuery));

  const stats = [
    { title: 'إجمالي الأصول', value: assets.length, icon: <Briefcase size={20} />, color: 'blue' as const },
    { title: 'نشطة', value: assets.filter(a => a.status === 'active').length, icon: <CheckCircle size={20} />, color: 'green' as const },
    { title: 'صيانة', value: assets.filter(a => a.status === 'maintenance').length, icon: <Wrench size={20} />, color: 'orange' as const },
    { title: 'القيمة الإجمالية', value: `${(assets.reduce((s, a) => s + a.value, 0) / 1000000).toFixed(1)}M ر.س`, icon: <Building2 size={20} />, color: 'purple' as const },
  ];

  const columns = [
    { key: 'id', label: 'الرمز', sortable: true },
    { key: 'name', label: 'الأصل', sortable: true },
    { key: 'category', label: 'الفئة', sortable: true },
    { key: 'location', label: 'الموقع', sortable: true },
    { key: 'value', label: 'القيمة', sortable: true, render: (v: number) => <span className="font-medium">{v.toLocaleString()} ر.س</span> },
    { key: 'purchaseDate', label: 'تاريخ الشراء', sortable: true },
    { key: 'status', label: 'الحالة', sortable: true, render: (v: string) => (
      <FluentBadge label={v === 'active' ? 'نشط' : v === 'maintenance' ? 'صيانة' : 'متقاعد'} 
        variant={v === 'active' ? 'success' : v === 'maintenance' ? 'warning' : 'neutral'} size="small" />
    )},
  ];

  return (
    <div className="min-h-screen bg-[#faf9f8]">
      <FluentCommandBar
        title="الأصول"
        subtitle="Asset Management & Tracking"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: () => window.location.reload() },
          { id: 'export', label: 'تصدير', icon: <Download size={16} />, variant: 'secondary', onClick: () => exportToCsv(assets, 'assets.csv') },
          { id: 'maintenance', label: 'جدولة صيانة', icon: <Wrench size={16} />, variant: 'secondary' },
          { id: 'new', label: 'أصل جديد', icon: <Plus size={16} />, variant: 'primary', onClick: () => { setSelectedAsset({}); setShowPanel(true); } },
        ]}
      />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {stats.map((stat) => <FluentStatsCard key={stat.title} {...stat} />)}
        </div>
        <FluentCard padding="small">
          <FluentSearchBox value={searchQuery} onChange={setSearchQuery} placeholder="البحث في الأصول..." className="w-80" />
        </FluentCard>
        <FluentTable
          title="قائمة الأصول"
          subtitle={`${filtered.length} أصل`}
          columns={columns}
          data={filtered}
          selectable
          onRowClick={(row) => { setSelectedAsset(row); setShowPanel(true); }}
        />
      </div>
      <FluentPanel isOpen={showPanel} onClose={() => setShowPanel(false)} title={selectedAsset?.name || 'تفاصيل الأصل'} footer={
        <div className="flex items-center justify-end gap-2">
          <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إغلاق</button>
          <button className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>
      }>
        {selectedAsset && (
          <ModuleForm fields={MODULE_FIELDS.assets} value={selectedAsset} onChange={setSelectedAsset} />
        )}
      </FluentPanel>
    </div>
  );
}
