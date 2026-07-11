// components/Layout/Sidebar.tsx
import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, FolderKanban, Building2, BrainCircuit, ShieldCheck, ClipboardCheck, Receipt, Languages, BadgeCheck,
  MapPin, Warehouse, Users, Settings, ChevronLeft, ChevronRight, Zap,
  ShoppingCart, Store, Factory, Boxes, Briefcase, HeartHandshake, Contact,
  ChevronDown, BarChart3
} from 'lucide-react';

interface NavGroup {
  label: string;
  items: NavItem[];
}

interface NavItem {
  path: string;
  icon: React.ElementType;
  label: string;
  badge?: number;
}

const navGroups: NavGroup[] = [
  {
    label: 'الرئيسية',
    items: [
      { path: '/dashboard', icon: LayoutDashboard, label: 'لوحة المعلومات' },
      { path: '/chat', icon: Contact, label: 'المحادثات' },
    ],
  },
  {
    label: 'الوحدات الذكية',
    items: [
      { path: '/pmo', icon: FolderKanban, label: 'إدارة المشاريع (PMO)' },
      { path: '/industry', icon: Building2, label: 'القطاعات الصناعية' },
      { path: '/ai', icon: BrainCircuit, label: 'محرك الذكاء الاصطناعي' },
    ],
  },
  {
    label: 'العمليات',
    items: [
      { path: '/crm', icon: HeartHandshake, label: 'إدارة العملاء (CRM)' },
      { path: '/selling', icon: ShoppingCart, label: 'المبيعات' },
      { path: '/buying', icon: Store, label: 'المشتريات' },
      { path: '/inventory', icon: Boxes, label: 'المخزون' },
      { path: '/warehouses', icon: Warehouse, label: 'المستودعات' },
      { path: '/manufacturing', icon: Factory, label: 'التصنيع' },
      { path: '/assets', icon: Briefcase, label: 'الأصول' },
    ],
  },
  {
    label: 'الموارد البشرية',
    items: [
      { path: '/hr', icon: Users, label: 'الموارد البشرية' },
      { path: '/branches', icon: MapPin, label: 'الفروع والمواقع' },
    ],
  },
  {
    label: 'المالية والتوطين',
    items: [
      { path: '/taxes', icon: BarChart3, label: 'الضرائب' },
      { path: '/i18n', icon: Zap, label: 'التوطين (i18n)' },
    ],
  },
  {
    label: 'الإعدادات',
    items: [
      { path: '/company-setup', icon: BadgeCheck, label: 'إعداد الشركة' },
      { path: '/controls', icon: ClipboardCheck, label: 'مكتبة الضوابط' },
      { path: '/regulatory', icon: ShieldCheck, label: 'الامتثال التنظيمي' },
      { path: '/users', icon: Users, label: 'المستخدمين' },
      { path: '/settings', icon: Settings, label: 'الإعدادات العامة' },
    ],
  },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['الرئيسية', 'العمليات']));
  const location = useLocation();

  const toggleGroup = (label: string) => {
    const newSet = new Set(expandedGroups);
    if (newSet.has(label)) newSet.delete(label);
    else newSet.add(label);
    setExpandedGroups(newSet);
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside
        className={`
          fixed right-0 top-0 h-screen bg-[#f3f2f1] border-l border-[#e1dfdd]
          flex flex-col z-40 transition-all duration-200
          ${collapsed ? 'w-[68px]' : 'w-[260px]'}
        `}
      >
        {/* App Header */}
        <div className="h-12 bg-[#0078d4] flex items-center px-4 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white/20 rounded flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            {!collapsed && (
              <div className="flex items-center gap-2">
                <span className="text-white font-semibold text-sm">Nexus</span>
                <span className="text-white/70 text-xs">Framework</span>
              </div>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-2">
          {navGroups.map((group) => (
            <div key={group.label} className="mb-1">
              {!collapsed && (
                <button
                  onClick={() => toggleGroup(group.label)}
                  className="w-full px-4 py-1.5 flex items-center justify-between text-xs font-semibold text-[#605e5c] uppercase tracking-wider hover:bg-[#e1dfdd]"
                >
                  {group.label}
                  <ChevronDown
                    size={14}
                    className={`transition-transform ${expandedGroups.has(group.label) ? '' : '-rotate-90'}`}
                  />
                </button>
              )}

              {(!collapsed || expandedGroups.has(group.label)) && (
                <div className={collapsed ? 'px-1' : ''}>
                  {group.items.map((item) => {
                    const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + '/');
                    return (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        className={`
                          flex items-center gap-3 mx-2 px-3 py-2 rounded-sm text-sm
                          transition-colors duration-150
                          ${isActive
                            ? 'bg-[#eff6fc] text-[#0078d4] font-medium'
                            : 'text-[#323130] hover:bg-[#e1dfdd]'
                          }
                          ${collapsed ? 'justify-center' : ''}
                        `}
                        title={collapsed ? item.label : undefined}
                      >
                        <item.icon size={18} className={isActive ? 'text-[#0078d4]' : 'text-[#605e5c]'} />
                        {!collapsed && (
                          <span className="truncate">{item.label}</span>
                        )}
                        {item.badge && !collapsed && (
                          <span className="mr-auto bg-[#d83b01] text-white text-xs rounded-full px-2 py-0.5 min-w-[20px] text-center">
                            {item.badge}
                          </span>
                        )}
                      </NavLink>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </nav>

        {/* Collapse Button */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="h-10 border-t border-[#e1dfdd] flex items-center justify-center text-[#605e5c] hover:bg-[#e1dfdd] transition-colors"
        >
          {collapsed ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
        </button>
      </aside>

      {/* Main Content Area */}
      <main className={`flex-1 transition-all duration-200 ${collapsed ? 'mr-[68px]' : 'mr-[260px]'}`}>
        <div className="min-h-screen bg-[#faf9f8]">
          {/* Content will be rendered here via Outlet */}
        </div>
      </main>
    </div>
  );
}

export default Sidebar;
