// components/Layout/Sidebar.tsx
import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, FolderKanban, Building2, BrainCircuit, ShieldCheck, ClipboardCheck, Receipt, Languages, BadgeCheck,
  MapPin, Warehouse, Users, Settings, ChevronLeft, ChevronRight, Zap,
  ShoppingCart, Store, Factory, Boxes, Briefcase, HeartHandshake, Contact,
  ChevronDown, BarChart3, X, Landmark, History, Receipt as ReceiptIcon, AlertTriangle, Shield, Clock, Calculator, FileText, Wallet, ArrowLeftRight, TrendingDown, Building, Coins, SlidersHorizontal, Tag, Barcode as BarcodeIcon, ShoppingBag, FileBarChart, Mail, UserCog, Ruler, Clock as ClockIcon2
, Undo2, CalendarClock} from 'lucide-react';

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
      { path: '/pricing', icon: Tag, label: 'قواعد التسعير' },
      { path: '/buying', icon: Store, label: 'المشتريات' },
      { path: '/purchasing', icon: ShoppingBag, label: 'دورة الشراء' },
      { path: '/inventory', icon: Boxes, label: 'المخزون' },
      { path: '/uom', icon: Ruler, label: 'وحدات القياس والتباينات' },
      { path: '/reorder', icon: AlertTriangle, label: 'إعادة الطلب' },
      { path: '/barcode', icon: BarcodeIcon, label: 'الباركود' },
      { path: '/valuation', icon: Calculator, label: 'تقييم المخزون' },
      { path: '/stock-movements', icon: ArrowLeftRight, label: 'حركات المخزون' },
      { path: '/warehouses', icon: Warehouse, label: 'المستودعات' },
      { path: '/manufacturing', icon: Factory, label: 'التصنيع' },
      { path: '/assets', icon: Briefcase, label: 'الأصول' },
      { path: '/depreciation', icon: TrendingDown, label: 'إهلاك الأصول' },
    ],
  },
  {
    label: 'الموارد البشرية',
    items: [
      { path: '/hr', icon: Users, label: 'الموارد البشرية' },
      { path: '/hr-extras', icon: UserCog, label: 'شؤون الموظفين' },
      { path: '/attendance', icon: Clock, label: 'الحضور والوقت' },
      { path: '/branches', icon: MapPin, label: 'الفروع والمواقع' },
    ],
  },
  {
    label: 'المالية والتوطين',
    items: [
      { path: '/accounting', icon: Landmark, label: 'المحاسبة' },
      { path: '/invoicing', icon: ReceiptIcon, label: 'الفواتير' },
      { path: '/credit-notes', icon: Undo2, label: 'الإشعارات الدائنة' },
      { path: '/periods', icon: CalendarClock, label: 'الفترات المحاسبية' },
      { path: '/aging', icon: Wallet, label: 'تقادم الذمم' },
      { path: '/banking', icon: Building2, label: 'التسوية البنكية' },
      { path: '/trade', icon: FileText, label: 'المستندات التجارية' },
      { path: '/taxes', icon: BarChart3, label: 'الضرائب' },
      { path: '/currencies', icon: Coins, label: 'العملات' },
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
      { path: '/tenants', icon: Building, label: 'المستأجرون' },
      { path: '/custom-fields', icon: SlidersHorizontal, label: 'الحقول المخصّصة' },
      { path: '/roles', icon: Shield, label: 'الأدوار والصلاحيات' },
      { path: '/security', icon: ShieldCheck, label: 'الأمان (2FA)' },
      { path: '/audit', icon: History, label: 'سجل التدقيق' },
      { path: '/approvals', icon: ClipboardCheck, label: 'الموافقات' },
      { path: '/automation', icon: ClockIcon2, label: 'الأتمتة (مهام/Webhooks)' },
      { path: '/reports', icon: FileBarChart, label: 'منشئ التقارير' },
      { path: '/notifications', icon: Mail, label: 'البريد والرسائل' },
      { path: '/settings', icon: Settings, label: 'الإعدادات العامة' },
    ],
  },
];

export function Sidebar({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(
    new Set(navGroups.map((g) => g.label))
  );
  const location = useLocation();

  const toggleGroup = (label: string) => {
    const s = new Set(expandedGroups);
    if (s.has(label)) s.delete(label);
    else s.add(label);
    setExpandedGroups(s);
  };

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div onClick={onClose} className="fixed inset-0 bg-black/30 z-40 transition-opacity" />
      )}

      {/* Flyout drawer (opens from the right in RTL, like a Start menu) */}
      <aside
        className={`fixed right-0 top-0 h-screen w-[280px] bg-[#f3f2f1] border-l border-[#e1dfdd] flex flex-col z-50 shadow-2xl transform transition-transform duration-200 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* App header */}
        <div className="h-12 bg-[#0078d4] flex items-center justify-between px-4 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white/20 rounded flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-white font-semibold text-sm">Nexus</span>
              <span className="text-white/70 text-xs">Framework</span>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-white/90 hover:bg-white/20 rounded" aria-label="إغلاق">
            <X size={18} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-2">
          {navGroups.map((group) => (
            <div key={group.label} className="mb-1">
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

              {expandedGroups.has(group.label) && (
                <div>
                  {group.items.map((item) => {
                    const isActive =
                      location.pathname === item.path ||
                      location.pathname.startsWith(item.path + '/');
                    return (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        onClick={onClose}
                        className={`flex items-center gap-3 mx-2 px-3 py-2 rounded-sm text-sm transition-colors duration-150 ${
                          isActive
                            ? 'bg-[#eff6fc] text-[#0078d4] font-medium'
                            : 'text-[#323130] hover:bg-[#e1dfdd]'
                        }`}
                      >
                        <item.icon size={18} className={isActive ? 'text-[#0078d4]' : 'text-[#605e5c]'} />
                        <span className="truncate">{item.label}</span>
                        {item.badge && (
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
      </aside>
    </>
  );
}

export default Sidebar;
