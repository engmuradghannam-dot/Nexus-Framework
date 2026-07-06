import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTenant } from '../hooks/useTenant';
import {
  LayoutDashboard, ShoppingCart, Package, Users,
  Building2, CreditCard, Puzzle, Settings, BarChart3,
  Factory, Briefcase, Landmark, FileText
} from 'lucide-react';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard', module: 'core' },
  { path: '/accounts', icon: Landmark, label: 'Accounts', module: 'accounts' },
  { path: '/inventory', icon: Package, label: 'Inventory', module: 'inventory' },
  { path: '/buying', icon: ShoppingCart, label: 'Buying', module: 'buying' },
  { path: '/selling', icon: BarChart3, label: 'Selling', module: 'selling' },
  { path: '/manufacturing', icon: Factory, label: 'Manufacturing', module: 'manufacturing' },
  { path: '/hr', icon: Users, label: 'HR', module: 'hr' },
  { path: '/crm', icon: Briefcase, label: 'CRM', module: 'crm' },
  { path: '/projects', icon: FileText, label: 'Projects', module: 'projects' },
  { path: '/billing', icon: CreditCard, label: 'Billing', module: 'billing' },
  { path: '/plugins', icon: Puzzle, label: 'Plugins', module: 'plugins' },
  { path: '/settings', icon: Settings, label: 'Settings', module: 'core' },
];

export default function Sidebar() {
  const { tenant } = useTenant();
  const enabledModules = tenant?.enabled_modules || [];

  return (
    <aside className="w-64 bg-white border-l border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center">
            <Building2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-gray-900 text-sm">Nexus ERP</h1>
            <p className="text-xs text-gray-500">SaaS Platform</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isEnabled = item.module === 'core' || item.module === 'billing' || 
                           item.module === 'plugins' || enabledModules.includes(item.module);
          if (!isEnabled) return null;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gray-200">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-xl p-4 text-white">
          <p className="text-xs opacity-80 mb-1">Current Plan</p>
          <p className="font-bold text-sm">{tenant?.tier || 'Free'}</p>
          <div className="mt-2 h-1.5 bg-white/20 rounded-full overflow-hidden">
            <div className="h-full bg-white/80 rounded-full" style={{ width: '60%' }} />
          </div>
        </div>
      </div>
    </aside>
  );
}
