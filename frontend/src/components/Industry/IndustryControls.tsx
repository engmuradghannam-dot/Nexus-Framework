// components/Industry/IndustryControls.tsx
import { useState } from 'react';
import { Search, Plus, Filter, Download, Upload, Grid, List, SlidersHorizontal } from 'lucide-react';

interface IndustryControlsProps {
  onSearch: (query: string) => void;
  onFilter: (filters: IndustryFilters) => void;
  onAddNew: () => void;
  onExport: () => void;
  onImport: (file: File) => void;
  viewMode: 'grid' | 'list';
  onViewModeChange: (mode: 'grid' | 'list') => void;
  totalCount: number;
}

export interface IndustryFilters {
  sector: string;
  status: string;
  dateRange: string;
  sortBy: string;
}

export function IndustryControls({
  onSearch,
  onFilter,
  onAddNew,
  onExport,
  onImport,
  viewMode,
  onViewModeChange,
  totalCount
}: IndustryControlsProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<IndustryFilters>({
    sector: '',
    status: '',
    dateRange: '',
    sortBy: 'name'
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(searchQuery);
  };

  const handleFilterChange = (key: keyof IndustryFilters, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilter(newFilters);
  };

  const handleFileImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onImport(e.target.files[0]);
    }
  };

  return (
    <div className="bg-white border-b p-4 space-y-4">
      {/* Top Row */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Search */}
        <form onSubmit={handleSearch} className="flex-1 min-w-[300px]">
          <div className="relative">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="البحث في القطاعات..."
              className="w-full pr-10 pl-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </form>

        {/* Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border transition-colors ${
              showFilters ? 'bg-blue-50 border-blue-200 text-blue-600' : 'border-gray-200 hover:bg-gray-50'
            }`}
          >
            <SlidersHorizontal size={18} />
            <span className="hidden sm:inline">تصفية</span>
          </button>

          <label className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors">
            <Upload size={18} />
            <span className="hidden sm:inline">استيراد</span>
            <input type="file" accept=".csv,.xlsx" className="hidden" onChange={handleFileImport} />
          </label>

          <button
            onClick={onExport}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            <Download size={18} />
            <span className="hidden sm:inline">تصدير</span>
          </button>

          <div className="flex border border-gray-200 rounded-xl overflow-hidden">
            <button
              onClick={() => onViewModeChange('grid')}
              className={`p-2.5 ${viewMode === 'grid' ? 'bg-blue-600 text-white' : 'hover:bg-gray-50'}`}
            >
              <Grid size={18} />
            </button>
            <button
              onClick={() => onViewModeChange('list')}
              className={`p-2.5 ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'hover:bg-gray-50'}`}
            >
              <List size={18} />
            </button>
          </div>

          <button
            onClick={onAddNew}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-sm"
          >
            <Plus size={18} />
            <span>إضافة قطاع</span>
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-gray-50 rounded-xl p-4 border">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">القطاع</label>
              <select
                value={filters.sector}
                onChange={(e) => handleFilterChange('sector', e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">الكل</option>
                <option value="technology">تقنية المعلومات</option>
                <option value="healthcare">الرعاية الصحية</option>
                <option value="finance">المالية</option>
                <option value="education">التعليم</option>
                <option value="manufacturing">التصنيع</option>
                <option value="retail">التجزئة</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">الحالة</label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">الكل</option>
                <option value="active">نشط</option>
                <option value="inactive">غير نشط</option>
                <option value="pending">معلق</option>
                <option value="archived">مؤرشف</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">الفترة الزمنية</label>
              <select
                value={filters.dateRange}
                onChange={(e) => handleFilterChange('dateRange', e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">الكل</option>
                <option value="today">اليوم</option>
                <option value="week">هذا الأسبوع</option>
                <option value="month">هذا الشهر</option>
                <option value="quarter">هذا الربع</option>
                <option value="year">هذا العام</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">الترتيب حسب</label>
              <select
                value={filters.sortBy}
                onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="name">الاسم</option>
                <option value="date">التاريخ</option>
                <option value="revenue">الإيرادات</option>
                <option value="employees">عدد الموظفين</option>
                <option value="growth">معدل النمو</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Results Count */}
      <div className="text-sm text-gray-500">
        إجمالي النتائج: <span className="font-semibold text-gray-700">{totalCount}</span> قطاع
      </div>
    </div>
  );
}
