// components/Header.tsx
import { useState } from 'react';
import { Menu, Bell, Settings, HelpCircle, User, Command } from 'lucide-react';
import { FluentSearchBox } from './FluentUI/FluentSearchBox';

export default function Header({ onMenuClick }: { onMenuClick: () => void }) {
  const [notifications] = useState([
    { id: 1, title: 'مشروع جديد تم إنشاؤه', time: 'منذ 5 دقائق', read: false },
    { id: 2, title: 'تنبيه مخزون منخفض', time: 'منذ ساعة', read: false },
    { id: 3, title: 'تمت الموافقة على طلب الشراء', time: 'منذ يوم', read: true },
  ]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <header className="fixed top-0 left-0 right-0 h-12 bg-[#0078d4] z-30 flex items-center justify-between px-4">
      {/* Menu (Start) button + brand */}
      <div className="flex items-center gap-3 flex-1">
        <button
          onClick={onMenuClick}
          className="p-2 text-white hover:bg-white/20 rounded-sm transition-colors"
          aria-label="القائمة"
        >
          <Menu size={20} />
        </button>
        <div className="hidden sm:flex items-center gap-2 ml-2">
          <span className="text-white font-semibold text-sm">Nexus</span>
          <span className="text-white/70 text-xs">Framework</span>
        </div>
        <div className="w-64">
          <FluentSearchBox 
            placeholder="البحث في النظام..."
            className="[&_input]:bg-white/20 [&_input]:text-white [&_input]:placeholder-white/70 [&_input]:border-transparent [&_input]:hover:bg-white/30 [&_input]:focus:bg-white [&_input]:focus:text-[#323130] [&_input]:focus:placeholder-[#605e5c] [&_svg]:text-white/70"
          />
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-1">
        <button className="p-2 text-white/90 hover:bg-white/20 rounded-sm transition-colors">
          <Command size={18} />
        </button>

        <button className="p-2 text-white/90 hover:bg-white/20 rounded-sm transition-colors">
          <HelpCircle size={18} />
        </button>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 text-white/90 hover:bg-white/20 rounded-sm transition-colors relative"
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-4 h-4 bg-[#d83b01] text-white text-[10px] rounded-full flex items-center justify-center">
                {unreadCount}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute left-0 top-12 w-80 bg-white border border-[#e1dfdd] shadow-lg rounded-sm z-50">
              <div className="px-4 py-3 border-b border-[#e1dfdd] flex items-center justify-between">
                <h3 className="font-semibold text-[#323130]">الإشعارات</h3>
                <button className="text-xs text-[#0078d4] hover:underline">تحديد الكل كمقروء</button>
              </div>
              <div className="max-h-80 overflow-y-auto">
                {notifications.map((n) => (
                  <div key={n.id} className={`px-4 py-3 border-b border-[#f3f2f1] hover:bg-[#f3f2f1] cursor-pointer ${!n.read ? 'bg-[#eff6fc]' : ''}`}>
                    <p className="text-sm text-[#323130]">{n.title}</p>
                    <p className="text-xs text-[#605e5c] mt-1">{n.time}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Profile */}
        <div className="relative">
          <button
            onClick={() => setShowProfile(!showProfile)}
            className="flex items-center gap-2 p-1.5 text-white hover:bg-white/20 rounded-sm transition-colors"
          >
            <div className="w-7 h-7 bg-white/30 rounded-full flex items-center justify-center">
              <User size={16} />
            </div>
            <span className="text-sm font-medium hidden lg:block">المستخدم</span>
          </button>

          {showProfile && (
            <div className="absolute left-0 top-12 w-56 bg-white border border-[#e1dfdd] shadow-lg rounded-sm z-50">
              <div className="px-4 py-3 border-b border-[#e1dfdd]">
                <p className="font-semibold text-[#323130]">المستخدم الحالي</p>
                <p className="text-sm text-[#605e5c]">admin@nexus.com</p>
              </div>
              <div className="py-1">
                <button className="w-full px-4 py-2 text-right text-sm text-[#323130] hover:bg-[#f3f2f1] flex items-center gap-2">
                  <Settings size={16} /> الإعدادات
                </button>
                <button className="w-full px-4 py-2 text-right text-sm text-[#323130] hover:bg-[#f3f2f1] flex items-center gap-2">
                  <User size={16} /> الملف الشخصي
                </button>
                <div className="border-t border-[#e1dfdd] my-1"></div>
                <button className="w-full px-4 py-2 text-right text-sm text-[#d83b01] hover:bg-[#fdf2f2]">
                  تسجيل الخروج
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
