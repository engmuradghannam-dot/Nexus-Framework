// pages/Dashboard/DashboardPage.tsx
import { useState } from 'react';
import { 
  LayoutDashboard, TrendingUp, TrendingDown, Users, DollarSign, 
  Package, Briefcase, Activity, ArrowUpRight, BarChart3, PieChart,
  Calendar, Clock, AlertTriangle, CheckCircle
} from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentTable } from '../../components/FluentUI/FluentTable';

const statsData = [
  { title: 'إجمالي الإيرادات', value: '1,250,000 ر.س', trend: 'up' as const, trendValue: '+12.5%', icon: <DollarSign size={20} />, color: 'blue' as const },
  { title: 'الموظفين', value: '850', trend: 'up' as const, trendValue: '+5', icon: <Users size={20} />, color: 'green' as const },
  { title: 'المشاريع النشطة', value: '12', trend: 'neutral' as const, trendValue: '0%', icon: <Briefcase size={20} />, color: 'purple' as const },
  { title: 'الطلبات المعلقة', value: '45', trend: 'down' as const, trendValue: '-3', icon: <Package size={20} />, color: 'orange' as const },
];

const recentActivity = [
  { id: '1', type: 'project', title: 'إنشاء مشروع نظام ERP', user: 'أحمد العلي', time: 'منذ 5 دقائق', status: 'success' },
  { id: '2', type: 'inventory', title: 'تنبيه مخزون منخفض: لابتوب Dell', user: 'النظام', time: 'منذ 30 دقيقة', status: 'warning' },
  { id: '3', type: 'hr', title: 'موافقة على إجازة جديدة', user: 'سارة أحمد', time: 'منذ ساعة', status: 'info' },
  { id: '4', type: 'sales', title: 'طلب شراء جديد #PO-2026-001', user: 'خالد السالم', time: 'منذ يوم', status: 'success' },
  { id: '5', type: 'ai', title: 'تقرير تحليلي تم إنشاؤه بواسطة AI', user: 'AI Assistant', time: 'منذ يومين', status: 'info' },
];

const upcomingTasks = [
  { id: '1', title: 'اجتماع فريق التطوير', date: '2026-07-12', priority: 'high', completed: false },
  { id: '2', title: 'مراجعة المخزون الشهرية', date: '2026-07-15', priority: 'medium', completed: false },
  { id: '3', title: 'تقديم تقرير المبيعات', date: '2026-07-18', priority: 'high', completed: true },
  { id: '4', title: 'صيانة دورية للأجهزة', date: '2026-07-20', priority: 'low', completed: false },
];

export default function DashboardPage() {
  const [timeRange, setTimeRange] = useState('month');

  const activityColumns = [
    { key: 'title', label: 'النشاط', render: (v: string, row: any) => (
      <div className="flex items-center gap-2">
        {row.status === 'success' && <CheckCircle size={16} className="text-[#107c10]" />}
        {row.status === 'warning' && <AlertTriangle size={16} className="text-[#d83b01]" />}
        {row.status === 'info' && <Activity size={16} className="text-[#0078d4]" />}
        <span>{v}</span>
      </div>
    )},
    { key: 'user', label: 'المستخدم' },
    { key: 'time', label: 'الوقت' },
  ];

  return (
    <div className="min-h-screen bg-[#faf9f8]">
      {/* Command Bar */}
      <FluentCommandBar
        title="لوحة المعلومات"
        subtitle="نظرة عامة على أداء المؤسسة"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <Clock size={16} />, variant: 'secondary' },
          { id: 'export', label: 'تصدير', icon: <BarChart3 size={16} />, variant: 'secondary' },
          { id: 'new', label: 'نشاط جديد', icon: <ArrowUpRight size={16} />, variant: 'primary' },
        ]}
      />

      <div className="p-6 space-y-6">
        {/* Time Range Selector */}
        <div className="flex items-center gap-2">
          {['day', 'week', 'month', 'quarter', 'year'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`
                px-3 py-1.5 text-sm font-medium rounded-sm transition-colors
                ${timeRange === range
                  ? 'bg-[#0078d4] text-white'
                  : 'bg-white text-[#323130] border border-[#e1dfdd] hover:bg-[#f3f2f1]'
                }
              `}
            >
              {range === 'day' ? 'يوم' : range === 'week' ? 'أسبوع' : range === 'month' ? 'شهر' : range === 'quarter' ? 'ربع' : 'سنة'}
            </button>
          ))}
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {statsData.map((stat) => (
            <FluentStatsCard key={stat.title} {...stat} />
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Activity */}
          <div className="lg:col-span-2">
            <FluentCard title="النشاط الأخير" subtitle="آخر التحديثات في النظام">
              <FluentTable
                columns={activityColumns}
                data={recentActivity}
                emptyMessage="لا توجد أنشطة حديثة"
              />
            </FluentCard>
          </div>

          {/* Upcoming Tasks */}
          <div>
            <FluentCard title="المهام القادمة" subtitle="المهام المجدولة">
              <div className="space-y-3">
                {upcomingTasks.map((task) => (
                  <div key={task.id} className="flex items-start gap-3 p-3 bg-[#faf9f8] rounded-sm border border-[#f3f2f1]">
                    <div className={`
                      w-2 h-2 rounded-full mt-2 shrink-0
                      ${task.priority === 'high' ? 'bg-[#d83b01]' : task.priority === 'medium' ? 'bg-[#ffc107]' : 'bg-[#107c10]'}
                    `} />
                    <div className="flex-1">
                      <p className={`text-sm font-medium ${task.completed ? 'line-through text-[#a19f9d]' : 'text-[#323130]'}`}>
                        {task.title}
                      </p>
                      <p className="text-xs text-[#605e5c] mt-1 flex items-center gap-1">
                        <Calendar size={12} />
                        {task.date}
                      </p>
                    </div>
                    <FluentBadge
                      label={task.priority === 'high' ? 'عالي' : task.priority === 'medium' ? 'متوسط' : 'منخفض'}
                      variant={task.priority === 'high' ? 'error' : task.priority === 'medium' ? 'warning' : 'success'}
                      size="small"
                    />
                  </div>
                ))}
              </div>
            </FluentCard>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <FluentCard title="أداء المبيعات" subtitle="الإيرادات الشهرية">
            <div className="h-64 flex items-end justify-around gap-2 pt-4">
              {[65, 45, 80, 55, 70, 90, 60, 75, 85, 50, 95, 70].map((height, idx) => (
                <div key={idx} className="flex flex-col items-center gap-1 flex-1">
                  <div 
                    className="w-full bg-[#0078d4] rounded-t-sm hover:bg-[#106ebe] transition-colors cursor-pointer relative group"
                    style={{ height: `${height}%` }}
                  >
                    <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-[#323130] text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                      {height}K ر.س
                    </div>
                  </div>
                  <span className="text-xs text-[#605e5c]">{['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'][idx]}</span>
                </div>
              ))}
            </div>
          </FluentCard>

          <FluentCard title="توزيع المشاريع" subtitle="حسب القطاع">
            <div className="h-64 flex items-center justify-center">
              <div className="relative w-48 h-48">
                <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#eff6fc" strokeWidth="20" />
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#0078d4" strokeWidth="20" strokeDasharray="125.6 251.2" />
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#107c10" strokeWidth="20" strokeDasharray="75.36 251.2" strokeDashoffset="-125.6" />
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#d83b01" strokeWidth="20" strokeDasharray="50.24 251.2" strokeDashoffset="-200.96" />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-[#323130]">24</p>
                    <p className="text-xs text-[#605e5c]">مشروع</p>
                  </div>
                </div>
              </div>
              <div className="mr-8 space-y-3">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-sm bg-[#0078d4]" />
                  <span className="text-sm text-[#323130]">تقنية (50%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-sm bg-[#107c10]" />
                  <span className="text-sm text-[#323130]">صناعة (30%)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-sm bg-[#d83b01]" />
                  <span className="text-sm text-[#323130]">خدمات (20%)</span>
                </div>
              </div>
            </div>
          </FluentCard>
        </div>
      </div>
    </div>
  );
}
