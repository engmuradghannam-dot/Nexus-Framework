// components/PMO/PMOControls.tsx
import { useState } from 'react';
import { Search, Plus, Filter, Download, Calendar, Grid, List, SlidersHorizontal, Kanban } from 'lucide-react';

interface PMOControlsProps {
  onSearch: (query: string) => void;
  onFilter: (filters: PMOFilters) => void;
  onAddNew: () => void;
  onExport: () => void;
  viewMode: 'grid' | 'list' | 'kanban' | 'gantt';
  onViewModeChange: (mode: 'grid' | 'list' | 'kanban' | 'gantt') => void;
  totalCount: number;
}

export interface PMOFilters {
  status: string;
  priority: string;
  phase: string;
  manager: string;
  dateRange: string;
  sortBy: string;
}

export function PMOControls({
  onSearch,
  onFilter,
  onAddNew,
  onExport,
  viewMode,
  onViewModeChange,
  totalCount
}: PMOControlsProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<PMOFilters>({
    status: '',
    priority: '',
    phase: '',
    manager: '',
    dateRange: '',
    sortBy: 'startDate'
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(searchQuery);
  };

  const handleFilterChange = (key: keyof PMOFilters, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilter(newFilters);
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
              placeholder="البحث في المشاريع..."
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

          <button
            onClick={onExport}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors"
          >
            <Download size={18} />
            <span className="hidden sm:inline">تصدير</span>
          </button>

          {/* View Mode Toggle */}
          <div className="flex border border-gray-200 rounded-xl overflow-hidden">
            {[
              { mode: 'grid' as const, icon: Grid },
              { mode: 'list' as const, icon: List },
              { mode: 'kanban' as const, icon: Kanban },
              { mode: 'gantt' as const, icon: Calendar }
            ].map(({ mode, icon: Icon }) => (
              <button
                key={mode}
                onClick={() => onViewModeChange(mode)}
                className={`p-2.5 ${viewMode === mode ? 'bg-blue-600 text-white' : 'hover:bg-gray-50'}`}
                title={mode}
              >
                <Icon size={18} />
              </button>
            ))}
          </div>

          <button
            onClick={onAddNew}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-sm"
          >
            <Plus size={18} />
            <span>مشروع جديد</span>
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-gray-50 rounded-xl p-4 border">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">الحالة</label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">الكل</option>
                <option value="planning">تخطيط</option>
                <option value="active">نشط</option>
                <option value="on_hold">معلق</option>
                <option value="completed">مكتمل</option>
                <option value="cancelled">ملغي</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">الأولوية</label>
              <select
                value={filters.priority}
                onChange={(e) => handleFilterChange('priority', e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">الكل</option>
                <option value="critical">حرج</option>
                <option value="high">عالي</option>
                <option value="medium">متوسط</option>
                <option value="low">منخفض</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">المرحلة</label>
              <select
                value={filters.phase}
                onChange={(e) => handleFilterChange('phase', e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">الكل</option>
                <option value="initiation">البدء</option>
                <option value="planning">التخطيط</option>
                <option value="execution">التنفيذ</option>
                <option value="monitoring">المراقبة</option>
                <option value="closure">الإغلاق</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">مدير المشروع</label>
              <select
                value={filters.manager}
                onChange={(e) => handleFilterChange('manager', e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">الكل</option>
                <option value="me">أنا</option>
                <option value="team">فريقي</option>
                <option value="unassigned">غير معين</option>
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
                <option value="overdue">متأخر</option>
                <option value="this_week">هذا الأسبوع</option>
                <option value="this_month">هذا الشهر</option>
                <option value="next_month">الشهر القادم</option>
                <option value="this_quarter">هذا الربع</option>
                <option value="this_year">هذا العام</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">الترتيب حسب</label>
              <select
                value={filters.sortBy}
                onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="startDate">تاريخ البدء</option>
                <option value="endDate">تاريخ الانتهاء</option>
                <option value="priority">الأولوية</option>
                <option value="progress">نسبة الإنجاز</option>
                <option value="budget">الميزانية</option>
                <option value="name">الاسم</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Results Count */}
      <div className="text-sm text-gray-500">
        إجمالي المشاريع: <span className="font-semibold text-gray-700">{totalCount}</span> مشروع
      </div>
    </div>
  );
}
