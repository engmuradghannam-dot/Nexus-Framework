// pages/Branches/BranchesPage.tsx
import { useState } from 'react';
import { 
  MapPin, Plus, Grid, List, Phone, Mail, Users, Building2, 
  Navigation, Edit3, Trash2, RefreshCw, Download, Filter
} from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentBadge } from '../../components/FluentBadge';
import { FluentTable } from '../../components/FluentTable';
import { FluentSearchBox } from '../../components/FluentSearchBox';
import { FluentPanel, FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { FluentStatsCard } from '../../components/FluentStatsCard';

interface Branch {
  id: string;
  name: string;
  address: string;
  city: string;
  country: string;
  phone: string;
  email: string;
  manager: string;
  employees: number;
  status: 'active' | 'inactive';
  coordinates: { lat: number; lng: number };
  type: 'main' | 'branch' | 'warehouse';
}

const demoBranches: Branch[] = [
  { id: '1', name: 'الفرع الرئيسي — الرياض', address: 'شارع الملك فهد، برج المملكة', city: 'الرياض', country: 'السعودية', phone: '+966 11 123 4567', email: 'riyadh@company.com', manager: 'أحمد العلي', employees: 150, status: 'active', coordinates: { lat: 24.7136, lng: 46.6753 }, type: 'main' },
  { id: '2', name: 'فرع جدة', address: 'شارع التحلية، حي الروضة', city: 'جدة', country: 'السعودية', phone: '+966 12 987 6543', email: 'jeddah@company.com', manager: 'سارة أحمد', employees: 80, status: 'active', coordinates: { lat: 21.4858, lng: 39.1925 }, type: 'branch' },
  { id: '3', name: 'مستودع الدمام', address: 'المنطقة الصناعية الثانية', city: 'الدمام', country: 'السعودية', phone: '+966 13 456 7890', email: 'dammam@company.com', manager: 'خالد السالم', employees: 45, status: 'active', coordinates: { lat: 26.3927, lng: 50.0916 }, type: 'warehouse' },
  { id: '4', name: 'فرع مكة', address: 'شارع إبراهيم الخليل', city: 'مكة', country: 'السعودية', phone: '+966 12 111 2222', email: 'makkah@company.com', manager: 'فاطمة حسن', employees: 60, status: 'active', coordinates: { lat: 21.3891, lng: 39.8579 }, type: 'branch' },
  { id: '5', name: 'فرع المدينة', address: 'طريق الملك عبدالله', city: 'المدينة', country: 'السعودية', phone: '+966 14 333 4444', email: 'madinah@company.com', manager: 'عمر خالد', employees: 35, status: 'inactive', coordinates: { lat: 24.5247, lng: 39.5692 }, type: 'branch' },
];

export default function BranchesPage() {
  const [branches] = useState<Branch[]>(demoBranches);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('');
  const [showPanel, setShowPanel] = useState(false);
  const [selectedBranch, setSelectedBranch] = useState<Branch | null>(null);

  const filtered = branches.filter(b => {
    const matchSearch = !searchQuery || b.name.includes(searchQuery) || b.city.includes(searchQuery);
    const matchType = !filterType || b.type === filterType;
    return matchSearch && matchType;
  });

  const stats = [
    { title: 'إجمالي الفروع', value: branches.length, icon: <Building2 size={20} />, color: 'blue' as const },
    { title: 'نشطة', value: branches.filter(b => b.status === 'active').length, icon: <Users size={20} />, color: 'green' as const },
    { title: 'إجمالي الموظفين', value: branches.reduce((sum, b) => sum + b.employees, 0), icon: <Users size={20} />, color: 'purple' as const },
    { title: 'مستودعات', value: branches.filter(b => b.type === 'warehouse').length, icon: <MapPin size={20} />, color: 'orange' as const },
  ];

  const columns = [
    { key: 'name', label: 'الفرع', sortable: true, render: (v: string, row: Branch) => (
      <div>
        <p className="font-medium text-[#323130]">{v}</p>
        <p className="text-xs text-[#605e5c]">{row.address}</p>
      </div>
    )},
    { key: 'city', label: 'المدينة', sortable: true },
    { key: 'type', label: 'النوع', sortable: true, render: (v: string) => (
      <FluentBadge 
        label={v === 'main' ? 'رئيسي' : v === 'branch' ? 'فرع' : 'مستودع'} 
        variant={v === 'main' ? 'primary' : v === 'branch' ? 'info' : 'warning'} 
        size="small"
      />
    )},
    { key: 'manager', label: 'المدير', sortable: true },
    { key: 'employees', label: 'الموظفين', sortable: true },
    { key: 'status', label: 'الحالة', sortable: true, render: (v: string) => (
      <FluentBadge label={v === 'active' ? 'نشط' : 'غير نشط'} variant={v === 'active' ? 'success' : 'neutral'} size="small" />
    )},
  ];

  return (
    <div className="min-h-screen bg-[#faf9f8]">
      <FluentCommandBar
        title="الفروع والمواقع"
        subtitle="Branches & Locations — إدارة الفروع والمستودعات"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary' },
          { id: 'export', label: 'تصدير', icon: <Download size={16} />, variant: 'secondary' },
          { id: 'new', label: 'إضافة فرع', icon: <Plus size={16} />, variant: 'primary' },
        ]}
      />

      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <FluentStatsCard key={stat.title} {...stat} />
          ))}
        </div>

        {/* Filters */}
        <FluentCard padding="small">
          <div className="flex flex-wrap items-center gap-3">
            <FluentSearchBox
              placeholder="البحث في الفروع..."
              value={searchQuery}
              onChange={setSearchQuery}
              className="w-80"
            />
            <FluentSelect
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-40"
            >
              <option value="">كل الأنواع</option>
              <option value="main">رئيسي</option>
              <option value="branch">فرع</option>
              <option value="warehouse">مستودع</option>
            </FluentSelect>
            <div className="flex items-center gap-1 mr-auto border border-[#e1dfdd] rounded-sm">
              <button 
                onClick={() => setViewMode('list')}
                className={`p-2 ${viewMode === 'list' ? 'bg-[#eff6fc] text-[#0078d4]' : 'text-[#605e5c] hover:bg-[#f3f2f1]'}`}
              >
                <List size={16} />
              </button>
              <button 
                onClick={() => setViewMode('grid')}
                className={`p-2 ${viewMode === 'grid' ? 'bg-[#eff6fc] text-[#0078d4]' : 'text-[#605e5c] hover:bg-[#f3f2f1]'}`}
              >
                <Grid size={16} />
              </button>
            </div>
          </div>
        </FluentCard>

        {/* Content */}
        {viewMode === 'list' ? (
          <FluentTable
            title="قائمة الفروع"
            subtitle={`${filtered.length} فرع`}
            columns={columns}
            data={filtered}
            selectable
            onRowClick={(row) => { setSelectedBranch(row); setShowPanel(true); }}
            actions={(row) => (
              <div className="py-1">
                <button className="w-full px-4 py-2 text-right text-sm text-[#323130] hover:bg-[#f3f2f1] flex items-center gap-2">
                  <Edit3 size={14} /> تعديل
                </button>
                <button className="w-full px-4 py-2 text-right text-sm text-[#d83b01] hover:bg-[#fdf2f2] flex items-center gap-2">
                  <Trash2 size={14} /> حذف
                </button>
              </div>
            )}
            emptyMessage="لا توجد فروع مطابقة"
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((branch) => (
              <FluentCard key={branch.id} padding="medium" className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => { setSelectedBranch(branch); setShowPanel(true); }}>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`
                      w-10 h-10 rounded-sm flex items-center justify-center
                      ${branch.type === 'main' ? 'bg-[#eff6fc] text-[#0078d4]' : 
                        branch.type === 'warehouse' ? 'bg-[#fff8f0] text-[#d83b01]' : 'bg-[#f3faf3] text-[#107c10]'}
                    `}>
                      <Building2 size={20} />
                    </div>
                    <div>
                      <p className="font-medium text-[#323130]">{branch.name}</p>
                      <p className="text-xs text-[#605e5c] flex items-center gap-1 mt-0.5">
                        <MapPin size={12} /> {branch.city}
                      </p>
                    </div>
                  </div>
                  <FluentBadge 
                    label={branch.status === 'active' ? 'نشط' : 'غير نشط'} 
                    variant={branch.status === 'active' ? 'success' : 'neutral'} 
                    size="small" 
                  />
                </div>
                <div className="mt-4 space-y-2 text-sm text-[#605e5c]">
                  <p className="flex items-center gap-2"><Phone size={14} /> {branch.phone}</p>
                  <p className="flex items-center gap-2"><Mail size={14} /> {branch.email}</p>
                  <p className="flex items-center gap-2"><Users size={14} /> {branch.employees} موظف</p>
                  <p className="flex items-center gap-2"><Navigation size={14} /> {branch.coordinates.lat}, {branch.coordinates.lng}</p>
                </div>
              </FluentCard>
            ))}
          </div>
        )}
      </div>

      {/* Detail Panel */}
      <FluentPanel
        isOpen={showPanel}
        onClose={() => setShowPanel(false)}
        title={selectedBranch?.name || 'تفاصيل الفرع'}
        subtitle={selectedBranch?.type === 'main' ? 'الفرع الرئيسي' : selectedBranch?.type === 'warehouse' ? 'مستودع' : 'فرع'}
        footer={
          <div className="flex items-center justify-end gap-2">
            <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">
              إغلاق
            </button>
            <button className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">
              حفظ التغييرات
            </button>
          </div>
        }
      >
        {selectedBranch && (
          <div className="space-y-4">
            <FluentFormField label="اسم الفرع" required>
              <FluentInput defaultValue={selectedBranch.name} />
            </FluentFormField>
            <FluentFormField label="العنوان">
              <FluentInput defaultValue={selectedBranch.address} />
            </FluentFormField>
            <div className="grid grid-cols-2 gap-4">
              <FluentFormField label="المدينة">
                <FluentInput defaultValue={selectedBranch.city} />
              </FluentFormField>
              <FluentFormField label="الدولة">
                <FluentInput defaultValue={selectedBranch.country} />
              </FluentFormField>
            </div>
            <FluentFormField label="المدير">
              <FluentInput defaultValue={selectedBranch.manager} />
            </FluentFormField>
            <div className="grid grid-cols-2 gap-4">
              <FluentFormField label="الهاتف">
                <FluentInput defaultValue={selectedBranch.phone} />
              </FluentFormField>
              <FluentFormField label="البريد الإلكتروني">
                <FluentInput defaultValue={selectedBranch.email} />
              </FluentFormField>
            </div>
            <FluentFormField label="عدد الموظفين">
              <FluentInput type="number" defaultValue={selectedBranch.employees} />
            </FluentFormField>
            <FluentFormField label="النوع">
              <FluentSelect defaultValue={selectedBranch.type}>
                <option value="main">رئيسي</option>
                <option value="branch">فرع</option>
                <option value="warehouse">مستودع</option>
              </FluentSelect>
            </FluentFormField>
            <FluentFormField label="الحالة">
              <FluentSelect defaultValue={selectedBranch.status}>
                <option value="active">نشط</option>
                <option value="inactive">غير نشط</option>
              </FluentSelect>
            </FluentFormField>
            <FluentFormField label="إحداثيات الموقع">
              <div className="grid grid-cols-2 gap-2">
                <FluentInput placeholder="خط العرض" defaultValue={selectedBranch.coordinates.lat} />
                <FluentInput placeholder="خط الطول" defaultValue={selectedBranch.coordinates.lng} />
              </div>
            </FluentFormField>
          </div>
        )}
      </FluentPanel>
    </div>
  );
}
