// pages/Dashboard/DashboardPage.tsx
import { useEffect, useState } from 'react';
import { 
  LayoutDashboard, MessageSquare, Building2, Briefcase, 
  TrendingUp, Users, DollarSign, Activity, ArrowUpRight, ArrowDownRight 
} from 'lucide-react';
import { projectApi, industryApi, chatApi } from '../../services/api';

interface DashboardStats {
  totalProjects: number;
  activeProjects: number;
  totalIndustries: number;
  totalRevenue: number;
  totalEmployees: number;
  chatMessages: number;
  recentActivity: Array<{
    id: string;
    type: 'project' | 'industry' | 'chat';
    title: string;
    timestamp: string;
  }>;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    totalProjects: 12,
    activeProjects: 8,
    totalIndustries: 24,
    totalRevenue: 125000000,
    totalEmployees: 850,
    chatMessages: 156,
    recentActivity: [
      { id: '1', type: 'project', title: 'إنشاء مشروع نظام ERP', timestamp: '2026-07-10T10:30:00' },
      { id: '2', type: 'industry', title: 'إضافة قطاع التقنية', timestamp: '2026-07-10T09:15:00' },
      { id: '3', type: 'chat', title: 'محادثة مع AI Assistant', timestamp: '2026-07-10T08:45:00' },
    ]
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const dashboard = await projectApi.getDashboard();
      if (dashboard) setStats(dashboard);
    } catch (err) {
      console.log('Using demo data');
    }
  };

  const statCards = [
    { 
      title: 'المشاريع', 
      value: stats.totalProjects, 
      sub: `${stats.activeProjects} نشط`,
      icon: Briefcase, 
      color: 'bg-blue-500', 
      trend: '+12%',
      trendUp: true 
    },
    { 
      title: 'القطاعات', 
      value: stats.totalIndustries, 
      sub: 'قطاع نشط',
      icon: Building2, 
      color: 'bg-green-500', 
      trend: '+5%',
      trendUp: true 
    },
    { 
      title: 'الإيرادات', 
      value: `${(stats.totalRevenue / 1000000).toFixed(0)}M`, 
      sub: 'ريال سعودي',
      icon: DollarSign, 
      color: 'bg-purple-500', 
      trend: '+18%',
      trendUp: true 
    },
    { 
      title: 'الموظفين', 
      value: stats.totalEmployees, 
      sub: 'موظف',
      icon: Users, 
      color: 'bg-orange-500', 
      trend: '+8%',
      trendUp: true 
    },
  ];

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'project': return Briefcase;
      case 'industry': return Building2;
      case 'chat': return MessageSquare;
      default: return Activity;
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'project': return 'bg-blue-100 text-blue-600';
      case 'industry': return 'bg-green-100 text-green-600';
      case 'chat': return 'bg-purple-100 text-purple-600';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">لوحة التحكم</h1>
          <p className="text-gray-500 mt-1">نظرة عامة على النظام</p>
        </div>
        <div className="text-sm text-gray-500">
          {new Date().toLocaleDateString('ar-SA', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          })}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.title} className="bg-white rounded-2xl border shadow-sm p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-xl ${card.color} bg-opacity-10`}>
                  <Icon className={card.color.replace('bg-', 'text-')} size={24} />
                </div>
                <div className={`flex items-center gap-1 text-sm font-medium ${card.trendUp ? 'text-green-600' : 'text-red-600'}`}>
                  {card.trendUp ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                  {card.trend}
                </div>
              </div>
              <h3 className="text-2xl font-bold text-gray-800">{card.value}</h3>
              <p className="text-sm text-gray-500 mt-1">{card.title}</p>
              <p className="text-xs text-gray-400 mt-0.5">{card.sub}</p>
            </div>
          );
        })}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Projects Status Chart */}
        <div className="bg-white rounded-2xl border shadow-sm p-6">
          <h3 className="font-bold text-gray-800 mb-4">حالة المشاريع</h3>
          <div className="space-y-4">
            {[
              { label: 'نشط', value: 8, total: 12, color: 'bg-green-500' },
              { label: 'تخطيط', value: 2, total: 12, color: 'bg-blue-500' },
              { label: 'معلق', value: 1, total: 12, color: 'bg-yellow-500' },
              { label: 'مكتمل', value: 1, total: 12, color: 'bg-purple-500' },
            ].map((item) => (
              <div key={item.label}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">{item.label}</span>
                  <span className="font-medium text-gray-800">{item.value} / {item.total}</span>
                </div>
                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full ${item.color}`}
                    style={{ width: `${(item.value / item.total) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-2xl border shadow-sm p-6">
          <h3 className="font-bold text-gray-800 mb-4">النشاط الأخير</h3>
          <div className="space-y-4">
            {stats.recentActivity.map((activity) => {
              const Icon = getActivityIcon(activity.type);
              return (
                <div key={activity.id} className="flex items-center gap-4">
                  <div className={`p-2.5 rounded-xl ${getActivityColor(activity.type)}`}>
                    <Icon size={18} />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-800 text-sm">{activity.title}</p>
                    <p className="text-xs text-gray-400">
                      {new Date(activity.timestamp).toLocaleString('ar-SA')}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="bg-white rounded-2xl border shadow-sm p-6">
        <h3 className="font-bold text-gray-800 mb-4">وصول سريع</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { path: '/chat', label: 'المحادثات', icon: MessageSquare, color: 'bg-blue-50 text-blue-600 hover:bg-blue-100' },
            { path: '/industry', label: 'مكتبة القطاعات', icon: Building2, color: 'bg-green-50 text-green-600 hover:bg-green-100' },
            { path: '/pmo', label: 'إدارة المشاريع', icon: Briefcase, color: 'bg-purple-50 text-purple-600 hover:bg-purple-100' },
            { path: '/dashboard', label: 'الإعدادات', icon: LayoutDashboard, color: 'bg-gray-50 text-gray-600 hover:bg-gray-100' },
          ].map((link) => {
            const Icon = link.icon;
            return (
              <a
                key={link.path}
                href={link.path}
                className={`flex items-center gap-3 p-4 rounded-xl transition-colors ${link.color}`}
              >
                <Icon size={24} />
                <span className="font-medium">{link.label}</span>
              </a>
            );
          })}
        </div>
      </div>
    </div>
  );
}
