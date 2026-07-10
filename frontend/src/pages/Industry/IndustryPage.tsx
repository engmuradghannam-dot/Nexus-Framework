// pages/Industry/IndustryPage.tsx
import { useState } from 'react';
import { IndustryControls, IndustryFilters } from '../../components/Industry/IndustryControls';
import { IndustryFormModal, IndustryFormData } from '../../components/Industry/IndustryFormModal';
import { useIndustry } from '../../hooks/useIndustry';
import { Building2, TrendingUp, Users, MapPin, Tag, MoreVertical, Edit2, Trash2, Eye } from 'lucide-react';

// Demo data
const demoIndustries: IndustryFormData[] = [
  {
    id: '1',
    name: 'شركة التقنية المتقدمة',
    sector: 'technology',
    description: 'شركة رائدة في مجال تطوير البرمجيات والحلول التقنية',
    status: 'active',
    revenue: 150,
    employees: 250,
    growthRate: 15.5,
    location: 'الرياض، السعودية',
    tags: ['برمجيات', 'ذكاء اصطناعي', 'سحابي']
  },
  {
    id: '2',
    name: 'المستشفى الدولي',
    sector: 'healthcare',
    description: 'مستشفى متخصص في الرعاية الصحية المتقدمة',
    status: 'active',
    revenue: 300,
    employees: 500,
    growthRate: 8.2,
    location: 'جدة، السعودية',
    tags: ['صحة', 'طوارئ', 'جراحة']
  },
  {
    id: '3',
    name: 'البنك الوطني',
    sector: 'finance',
    description: 'بنك رائد في الخدمات المالية والمصرفية',
    status: 'active',
    revenue: 800,
    employees: 1200,
    growthRate: 12.1,
    location: 'الرياض، السعودية',
    tags: ['مصارف', 'استثمار', 'تمويل']
  }
];

const sectorLabels: Record<string, string> = {
  technology: 'تقنية المعلومات',
  healthcare: 'الرعاية الصحية',
  finance: 'المالية',
  education: 'التعليم',
  manufacturing: 'التصنيع',
  retail: 'التجزئة',
  energy: 'الطاقة',
  transport: 'النقل'
};

const statusConfig: Record<string, { label: string; color: string; bg: string }> = {
  active: { label: 'نشط', color: 'text-green-700', bg: 'bg-green-100' },
  inactive: { label: 'غير نشط', color: 'text-gray-700', bg: 'bg-gray-100' },
  pending: { label: 'معلق', color: 'text-yellow-700', bg: 'bg-yellow-100' },
  archived: { label: 'مؤرشف', color: 'text-red-700', bg: 'bg-red-100' }
};

export default function IndustryPage() {
  const { industries, loading, createIndustry, updateIndustry, deleteIndustry } = useIndustry();
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showForm, setShowForm] = useState(false);
  const [editingIndustry, setEditingIndustry] = useState<IndustryFormData | undefined>();
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<IndustryFilters>({
    sector: '',
    status: '',
    dateRange: '',
    sortBy: 'name'
  });

  // Use demo data if no API data
  const displayData = industries.length > 0 ? industries : demoIndustries;

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  const handleFilter = (newFilters: IndustryFilters) => {
    setFilters(newFilters);
  };

  const handleAddNew = () => {
    setEditingIndustry(undefined);
    setShowForm(true);
  };

  const handleEdit = (industry: IndustryFormData) => {
    setEditingIndustry(industry);
    setShowForm(true);
  };

  const handleSubmit = (data: IndustryFormData) => {
    if (data.id) {
      updateIndustry(data.id, data);
    } else {
      createIndustry(data);
    }
    setShowForm(false);
  };

  const handleDelete = (id: string) => {
    if (confirm('هل أنت متأكد من حذف هذا القطاع؟')) {
      deleteIndustry(id);
    }
  };

  const handleExport = () => {
    const csv = [
      ['الاسم', 'القطاع', 'الحالة', 'الإيرادات', 'الموظفين', 'النمو', 'الموقع'],
      ...displayData.map(i => [i.name, sectorLabels[i.sector] || i.sector, statusConfig[i.status]?.label || i.status, i.revenue.toString(), i.employees.toString(), i.growthRate.toString(), i.location])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'industries.csv';
    link.click();
  };

  const handleImport = (file: File) => {
    // Import logic
    console.log('Importing file:', file.name);
  };

  // Filter and search
  let filteredData = displayData.filter(item => {
    const matchesSearch = !searchQuery || item.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSector = !filters.sector || item.sector === filters.sector;
    const matchesStatus = !filters.status || item.status === filters.status;
    return matchesSearch && matchesSector && matchesStatus;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Controls */}
      <IndustryControls
        onSearch={handleSearch}
        onFilter={handleFilter}
        onAddNew={handleAddNew}
        onExport={handleExport}
        onImport={handleImport}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        totalCount={filteredData.length}
      />

      {/* Content */}
      <div className="p-6">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredData.length === 0 ? (
          <div className="text-center py-16">
            <Building2 size={64} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-600">لا توجد قطاعات</h3>
            <p className="text-gray-400 mt-1">ابدأ بإضافة قطاع جديد</p>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredData.map((industry) => (
              <div key={industry.id} className="bg-white rounded-2xl border shadow-sm hover:shadow-md transition-shadow overflow-hidden">
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="p-3 bg-blue-50 rounded-xl">
                      <Building2 className="text-blue-600" size={24} />
                    </div>
                    <div className="relative group">
                      <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                        <MoreVertical size={18} className="text-gray-400" />
                      </button>
                      <div className="absolute left-0 mt-1 w-40 bg-white border rounded-xl shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                        <button onClick={() => handleEdit(industry)} className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-gray-50 text-sm">
                          <Edit2 size={14} /> تعديل
                        </button>
                        <button onClick={() => handleDelete(industry.id!)} className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-red-50 text-red-600 text-sm">
                          <Trash2 size={14} /> حذف
                        </button>
                      </div>
                    </div>
                  </div>

                  <h3 className="font-bold text-lg text-gray-800 mb-1">{industry.name}</h3>
                  <p className="text-sm text-gray-500 mb-3 line-clamp-2">{industry.description}</p>

                  <div className="flex items-center gap-2 mb-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusConfig[industry.status]?.bg} ${statusConfig[industry.status]?.color}`}>
                      {statusConfig[industry.status]?.label}
                    </span>
                    <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                      {sectorLabels[industry.sector] || industry.sector}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-3 pt-4 border-t">
                    <div className="text-center">
                      <DollarSign className="mx-auto text-green-600 mb-1" size={18} />
                      <p className="text-sm font-semibold text-gray-800">{industry.revenue}M</p>
                      <p className="text-xs text-gray-400">إيرادات</p>
                    </div>
                    <div className="text-center">
                      <Users className="mx-auto text-blue-600 mb-1" size={18} />
                      <p className="text-sm font-semibold text-gray-800">{industry.employees}</p>
                      <p className="text-xs text-gray-400">موظفين</p>
                    </div>
                    <div className="text-center">
                      <TrendingUp className="mx-auto text-purple-600 mb-1" size={18} />
                      <p className="text-sm font-semibold text-gray-800">{industry.growthRate}%</p>
                      <p className="text-xs text-gray-400">نمو</p>
                    </div>
                  </div>

                  {industry.location && (
                    <div className="flex items-center gap-2 mt-4 text-sm text-gray-500">
                      <MapPin size={14} />
                      {industry.location}
                    </div>
                  )}

                  {industry.tags && industry.tags.length > 0 && (
                    <div className="flex gap-1 flex-wrap mt-3">
                      {industry.tags.map(tag => (
                        <span key={tag} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-2xl border shadow-sm overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">القطاع</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الحالة</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الإيرادات</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الموظفين</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">النمو</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الإجراءات</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filteredData.map((industry) => (
                  <tr key={industry.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-50 rounded-lg">
                          <Building2 className="text-blue-600" size={18} />
                        </div>
                        <div>
                          <p className="font-semibold text-gray-800">{industry.name}</p>
                          <p className="text-sm text-gray-500">{sectorLabels[industry.sector]}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusConfig[industry.status]?.bg} ${statusConfig[industry.status]?.color}`}>
                        {statusConfig[industry.status]?.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm font-semibold text-gray-800">{industry.revenue}M</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{industry.employees}</td>
                    <td className="px-6 py-4">
                      <span className={`text-sm font-semibold ${industry.growthRate > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {industry.growthRate > 0 ? '+' : ''}{industry.growthRate}%
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button onClick={() => handleEdit(industry)} className="p-2 hover:bg-blue-50 text-blue-600 rounded-lg transition-colors">
                          <Edit2 size={16} />
                        </button>
                        <button onClick={() => handleDelete(industry.id!)} className="p-2 hover:bg-red-50 text-red-600 rounded-lg transition-colors">
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Form Modal */}
      <IndustryFormModal
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={handleSubmit}
        initialData={editingIndustry}
      />
    </div>
  );
}
