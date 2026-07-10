// pages/PMO/PMOPage.tsx
import { useState } from 'react';
import { PMOControls, PMOFilters } from '../../components/PMO/PMOControls';
import { ProjectFormModal, ProjectFormData } from '../../components/PMO/ProjectFormModal';
import { useIndustry } from '../../hooks/useIndustry';
import { 
  Briefcase, Calendar, DollarSign, Users, Flag, Target, 
  TrendingUp, AlertTriangle, CheckCircle, Clock, MoreVertical, 
  Edit2, Trash2, BarChart3 
} from 'lucide-react';

// Demo data
const demoProjects: ProjectFormData[] = [
  {
    id: '1',
    name: 'نظام ERP المتكامل',
    description: 'تطوير وتنفيذ نظام ERP متكامل لإدارة الموارد المؤسسية',
    status: 'active',
    priority: 'high',
    phase: 'execution',
    startDate: '2026-01-15',
    endDate: '2026-12-31',
    budget: 5000000,
    spent: 2500000,
    progress: 45,
    manager: 'أحمد محمد',
    team: ['خالد العلي', 'سارة أحمد', 'فهد السالم'],
    objectives: ['تحسين الكفاءة التشغيلية', 'تقليل التكاليف', 'تحسين تجربة العملاء'],
    risks: ['تأخر في التسليم', 'ميزانية إضافية'],
    milestones: [
      { title: 'تحليل المتطلبات', date: '2026-02-28', completed: true },
      { title: 'تصميم النظام', date: '2026-04-30', completed: true },
      { title: 'التطوير', date: '2026-08-31', completed: false }
    ]
  },
  {
    id: '2',
    name: 'منصة التجارة الإلكترونية',
    description: 'بناء منصة تجارة إلكترونية متكاملة مع دفع إلكتروني',
    status: 'planning',
    priority: 'critical',
    phase: 'planning',
    startDate: '2026-07-01',
    endDate: '2026-12-31',
    budget: 3000000,
    spent: 150000,
    progress: 5,
    manager: 'فاطمة الزهراء',
    team: ['عمر خالد', 'نورة السعد'],
    objectives: ['زيادة المبيعات', 'تحسين الوصول للعملاء'],
    risks: ['منافسة شديدة'],
    milestones: [
      { title: 'دراسة السوق', date: '2026-07-15', completed: true }
    ]
  }
];

const statusConfig: Record<string, { label: string; color: string; bg: string; icon: any }> = {
  planning: { label: 'تخطيط', color: 'text-blue-700', bg: 'bg-blue-100', icon: Target },
  active: { label: 'نشط', color: 'text-green-700', bg: 'bg-green-100', icon: CheckCircle },
  on_hold: { label: 'معلق', color: 'text-yellow-700', bg: 'bg-yellow-100', icon: Clock },
  completed: { label: 'مكتمل', color: 'text-purple-700', bg: 'bg-purple-100', icon: CheckCircle },
  cancelled: { label: 'ملغي', color: 'text-red-700', bg: 'bg-red-100', icon: AlertTriangle }
};

const priorityConfig: Record<string, { label: string; color: string }> = {
  critical: { label: 'حرج', color: 'text-red-600' },
  high: { label: 'عالي', color: 'text-orange-600' },
  medium: { label: 'متوسط', color: 'text-yellow-600' },
  low: { label: 'منخفض', color: 'text-green-600' }
};

export default function PMOPage() {
  const { projects, loading, createProject, updateProject, deleteProject } = useIndustry();
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'kanban' | 'gantt'>('grid');
  const [showForm, setShowForm] = useState(false);
  const [editingProject, setEditingProject] = useState<ProjectFormData | undefined>();
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<PMOFilters>({
    status: '',
    priority: '',
    phase: '',
    manager: '',
    dateRange: '',
    sortBy: 'startDate'
  });

  const displayData = projects.length > 0 ? projects : demoProjects;

  const handleSearch = (query: string) => setSearchQuery(query);
  const handleFilter = (newFilters: PMOFilters) => setFilters(newFilters);

  const handleAddNew = () => {
    setEditingProject(undefined);
    setShowForm(true);
  };

  const handleEdit = (project: ProjectFormData) => {
    setEditingProject(project);
    setShowForm(true);
  };

  const handleSubmit = (data: ProjectFormData) => {
    if (data.id) {
      updateProject(data.id, data);
    } else {
      createProject(data);
    }
    setShowForm(false);
  };

  const handleDelete = (id: string) => {
    if (confirm('هل أنت متأكد من حذف هذا المشروع؟')) {
      deleteProject(id);
    }
  };

  const handleExport = () => {
    const csv = [
      ['الاسم', 'الحالة', 'الأولوية', 'المرحلة', 'تاريخ البدء', 'تاريخ الانتهاء', 'الميزانية', 'المنصرف', 'الإنجاز', 'المدير'],
      ...displayData.map(p => [
        p.name, statusConfig[p.status]?.label || p.status, priorityConfig[p.priority]?.label || p.priority,
        p.phase, p.startDate, p.endDate, p.budget.toString(), p.spent.toString(), p.progress.toString(), p.manager
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'projects.csv';
    link.click();
  };

  let filteredData = displayData.filter(item => {
    const matchesSearch = !searchQuery || item.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = !filters.status || item.status === filters.status;
    const matchesPriority = !filters.priority || item.priority === filters.priority;
    const matchesPhase = !filters.phase || item.phase === filters.phase;
    return matchesSearch && matchesStatus && matchesPriority && matchesPhase;
  });

  const getProgressColor = (progress: number) => {
    if (progress >= 80) return 'bg-green-500';
    if (progress >= 50) return 'bg-blue-500';
    if (progress >= 20) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getBudgetStatus = (budget: number, spent: number) => {
    const ratio = spent / budget;
    if (ratio > 1) return { color: 'text-red-600', label: 'تجاوز' };
    if (ratio > 0.8) return { color: 'text-yellow-600', label: 'قريب' };
    return { color: 'text-green-600', label: 'جيد' };
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Controls */}
      <PMOControls
        onSearch={handleSearch}
        onFilter={handleFilter}
        onAddNew={handleAddNew}
        onExport={handleExport}
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
            <Briefcase size={64} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-600">لا توجد مشاريع</h3>
            <p className="text-gray-400 mt-1">ابدأ بإضافة مشروع جديد</p>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredData.map((project) => {
              const StatusIcon = statusConfig[project.status]?.icon || Briefcase;
              const budgetStatus = getBudgetStatus(project.budget, project.spent);

              return (
                <div key={project.id} className="bg-white rounded-2xl border shadow-sm hover:shadow-md transition-shadow overflow-hidden">
                  <div className="p-6">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className={`p-3 rounded-xl ${statusConfig[project.status]?.bg}`}>
                          <StatusIcon className={statusConfig[project.status]?.color} size={24} />
                        </div>
                        <div>
                          <h3 className="font-bold text-lg text-gray-800">{project.name}</h3>
                          <p className="text-sm text-gray-500">{project.manager}</p>
                        </div>
                      </div>
                      <div className="relative group">
                        <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                          <MoreVertical size={18} className="text-gray-400" />
                        </button>
                        <div className="absolute left-0 mt-1 w-40 bg-white border rounded-xl shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                          <button onClick={() => handleEdit(project)} className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-gray-50 text-sm">
                            <Edit2 size={14} /> تعديل
                          </button>
                          <button onClick={() => handleDelete(project.id!)} className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-red-50 text-red-600 text-sm">
                            <Trash2 size={14} /> حذف
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Description */}
                    <p className="text-sm text-gray-500 mb-4 line-clamp-2">{project.description}</p>

                    {/* Badges */}
                    <div className="flex gap-2 mb-4 flex-wrap">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusConfig[project.status]?.bg} ${statusConfig[project.status]?.color}`}>
                        {statusConfig[project.status]?.label}
                      </span>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium bg-gray-100 ${priorityConfig[project.priority]?.color}`}>
                        {priorityConfig[project.priority]?.label}
                      </span>
                    </div>

                    {/* Progress */}
                    <div className="mb-4">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-600">نسبة الإنجاز</span>
                        <span className="font-semibold text-gray-800">{project.progress}%</span>
                      </div>
                      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all ${getProgressColor(project.progress)}`}
                          style={{ width: `${project.progress}%` }}
                        />
                      </div>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 gap-3 pt-4 border-t">
                      <div className="flex items-center gap-2">
                        <DollarSign size={16} className="text-green-600" />
                        <div>
                          <p className="text-sm font-semibold text-gray-800">
                            {(project.budget / 1000000).toFixed(1)}M
                          </p>
                          <p className="text-xs text-gray-400">الميزانية</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <BarChart3 size={16} className={budgetStatus.color} />
                        <div>
                          <p className={`text-sm font-semibold ${budgetStatus.color}`}>
                            {((project.spent / project.budget) * 100).toFixed(0)}%
                          </p>
                          <p className="text-xs text-gray-400">{budgetStatus.label}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Users size={16} className="text-blue-600" />
                        <div>
                          <p className="text-sm font-semibold text-gray-800">{project.team.length}</p>
                          <p className="text-xs text-gray-400">أعضاء الفريق</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Calendar size={16} className="text-purple-600" />
                        <div>
                          <p className="text-sm font-semibold text-gray-800">
                            {new Date(project.endDate).toLocaleDateString('ar-SA')}
                          </p>
                          <p className="text-xs text-gray-400">الانتهاء</p>
                        </div>
                      </div>
                    </div>

                    {/* Milestones Preview */}
                    {project.milestones.length > 0 && (
                      <div className="mt-4 pt-4 border-t">
                        <p className="text-xs font-medium text-gray-500 mb-2">المراحل</p>
                        <div className="space-y-1.5">
                          {project.milestones.slice(0, 3).map((m, idx) => (
                            <div key={idx} className="flex items-center gap-2 text-sm">
                              {m.completed ? (
                                <CheckCircle size={14} className="text-green-500 flex-shrink-0" />
                              ) : (
                                <Clock size={14} className="text-gray-400 flex-shrink-0" />
                              )}
                              <span className={m.completed ? 'text-gray-500 line-through' : 'text-gray-700'}>
                                {m.title}
                              </span>
                            </div>
                          ))}
                          {project.milestones.length > 3 && (
                            <p className="text-xs text-gray-400">+{project.milestones.length - 3} مراحل أخرى</p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : viewMode === 'list' ? (
          <div className="bg-white rounded-2xl border shadow-sm overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">المشروع</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الحالة</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الأولوية</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الإنجاز</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الميزانية</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">المدير</th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الإجراءات</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {filteredData.map((project) => (
                  <tr key={project.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${statusConfig[project.status]?.bg}`}>
                          <Briefcase className={statusConfig[project.status]?.color} size={18} />
                        </div>
                        <div>
                          <p className="font-semibold text-gray-800">{project.name}</p>
                          <p className="text-sm text-gray-500">{project.phase}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusConfig[project.status]?.bg} ${statusConfig[project.status]?.color}`}>
                        {statusConfig[project.status]?.label}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-sm font-medium ${priorityConfig[project.priority]?.color}`}>
                        {priorityConfig[project.priority]?.label}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="w-24">
                        <div className="flex justify-between text-xs mb-1">
                          <span>{project.progress}%</span>
                        </div>
                        <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full ${getProgressColor(project.progress)}`} style={{ width: `${project.progress}%` }} />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {(project.budget / 1000000).toFixed(1)}M
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{project.manager}</td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button onClick={() => handleEdit(project)} className="p-2 hover:bg-blue-50 text-blue-600 rounded-lg transition-colors">
                          <Edit2 size={16} />
                        </button>
                        <button onClick={() => handleDelete(project.id!)} className="p-2 hover:bg-red-50 text-red-600 rounded-lg transition-colors">
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : viewMode === 'kanban' ? (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {['initiation', 'planning', 'execution', 'monitoring', 'closure'].map((phase) => (
              <div key={phase} className="bg-gray-100 rounded-xl p-4">
                <h3 className="font-semibold text-gray-700 mb-4 text-center">
                  {phase === 'initiation' ? 'البدء' : 
                   phase === 'planning' ? 'التخطيط' : 
                   phase === 'execution' ? 'التنفيذ' : 
                   phase === 'monitoring' ? 'المراقبة' : 'الإغلاق'}
                </h3>
                <div className="space-y-3">
                  {filteredData.filter(p => p.phase === phase).map((project) => (
                    <div key={project.id} className="bg-white rounded-xl p-4 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                         onClick={() => handleEdit(project)}>
                      <h4 className="font-semibold text-sm text-gray-800 mb-2">{project.name}</h4>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <Flag size={12} className={priorityConfig[project.priority]?.color} />
                        <span>{priorityConfig[project.priority]?.label}</span>
                      </div>
                      <div className="mt-2">
                        <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full ${getProgressColor(project.progress)}`} style={{ width: `${project.progress}%` }} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          // Gantt View
          <div className="bg-white rounded-2xl border shadow-sm p-6 overflow-x-auto">
            <div className="min-w-[800px]">
              <div className="flex border-b pb-4 mb-4">
                <div className="w-48 font-semibold text-gray-700">المشروع</div>
                <div className="flex-1 grid grid-cols-12 gap-1">
                  {['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'].map(m => (
                    <div key={m} className="text-center text-xs text-gray-500">{m}</div>
                  ))}
                </div>
              </div>
              {filteredData.map((project) => {
                const start = new Date(project.startDate).getMonth();
                const end = new Date(project.endDate).getMonth();
                const duration = end - start + 1;

                return (
                  <div key={project.id} className="flex items-center py-3 border-b last:border-0">
                    <div className="w-48 pr-4">
                      <p className="font-medium text-sm text-gray-800">{project.name}</p>
                      <p className="text-xs text-gray-500">{project.manager}</p>
                    </div>
                    <div className="flex-1 grid grid-cols-12 gap-1 relative h-8">
                      <div 
                        className={`absolute h-6 rounded-lg ${getProgressColor(project.progress)} opacity-80`}
                        style={{ 
                          left: `${(start / 12) * 100}%`, 
                          width: `${(duration / 12) * 100}%` 
                        }}
                      >
                        <span className="text-xs text-white px-2 leading-6">{project.progress}%</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Form Modal */}
      <ProjectFormModal
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={handleSubmit}
        initialData={editingProject}
      />
    </div>
  );
}
