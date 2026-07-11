// pages/Settings/SettingsPage.tsx
import { useState } from 'react';
import { Settings, Save, Globe, Palette, Bell, Shield, Database } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general');

  const tabs = [
    { id: 'general', label: 'عام', icon: Settings },
    { id: 'appearance', label: 'المظهر', icon: Palette },
    { id: 'notifications', label: 'الإشعارات', icon: Bell },
    { id: 'security', label: 'الأمان', icon: Shield },
    { id: 'database', label: 'قاعدة البيانات', icon: Database },
  ];

  return (
    <div className="min-h-screen bg-[#faf9f8]">
      <FluentCommandBar
        title="الإعدادات"
        subtitle="System Configuration & Preferences"
        commands={[
          { id: 'save', label: 'حفظ التغييرات', icon: <Save size={16} />, variant: 'primary', onClick: () => window.location.reload() },
        ]}
      />
      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Tabs */}
          <div className="lg:col-span-1">
            <FluentCard padding="none">
              <div className="py-2">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-right
                      transition-colors
                      ${activeTab === tab.id 
                        ? 'bg-[#eff6fc] text-[#0078d4] border-r-2 border-[#0078d4]' 
                        : 'text-[#323130] hover:bg-[#f3f2f1]'
                      }
                    `}
                  >
                    <tab.icon size={18} />
                    {tab.label}
                  </button>
                ))}
              </div>
            </FluentCard>
          </div>

          {/* Content */}
          <div className="lg:col-span-3">
            {activeTab === 'general' && (
              <FluentCard title="الإعدادات العامة" subtitle="إعدادات النظام الأساسية">
                <div className="space-y-4 max-w-xl">
                  <FluentFormField label="اسم الشركة" required>
                    <FluentInput defaultValue="شركة Nexus للتقنية" />
                  </FluentFormField>
                  <FluentFormField label="اللغة الافتراضية">
                    <FluentSelect defaultValue="ar">
                      <option value="ar">العربية</option>
                      <option value="en">English</option>
                    </FluentSelect>
                  </FluentFormField>
                  <FluentFormField label="المنطقة الزمنية">
                    <FluentSelect defaultValue="Asia/Riyadh">
                      <option value="Asia/Riyadh">الرياض (GMT+3)</option>
                      <option value="Asia/Dubai">دبي (GMT+4)</option>
                      <option value="UTC">UTC</option>
                    </FluentSelect>
                  </FluentFormField>
                  <FluentFormField label="العملة">
                    <FluentSelect defaultValue="SAR">
                      <option value="SAR">ريال سعودي (SAR)</option>
                      <option value="USD">دولار أمريكي (USD)</option>
                      <option value="EUR">يورو (EUR)</option>
                    </FluentSelect>
                  </FluentFormField>
                </div>
              </FluentCard>
            )}

            {activeTab === 'appearance' && (
              <FluentCard title="المظهر" subtitle="تخصيص واجهة المستخدم">
                <div className="space-y-4 max-w-xl">
                  <FluentFormField label="السمة">
                    <FluentSelect defaultValue="light">
                      <option value="light">فاتح</option>
                      <option value="dark">داكن</option>
                      <option value="system">حسب النظام</option>
                    </FluentSelect>
                  </FluentFormField>
                  <FluentFormField label="اللون الرئيسي">
                    <div className="flex gap-2">
                      {['#0078d4', '#107c10', '#d83b01', '#5c2d91', '#ffc107'].map((color) => (
                        <button key={color} className="w-8 h-8 rounded-sm" style={{ backgroundColor: color }} />
                      ))}
                    </div>
                  </FluentFormField>
                </div>
              </FluentCard>
            )}

            {activeTab === 'notifications' && (
              <FluentCard title="الإشعارات" subtitle="إعدادات التنبيهات والإشعارات">
                <div className="space-y-4 max-w-xl">
                  <div className="flex items-center justify-between py-3 border-b border-[#f3f2f1]">
                    <div>
                      <p className="font-medium text-[#323130]">إشعارات البريد الإلكتروني</p>
                      <p className="text-sm text-[#605e5c]">استلام الإشعارات عبر البريد الإلكتروني</p>
                    </div>
                    <input type="checkbox" defaultChecked className="w-5 h-5 text-[#0078d4] rounded" />
                  </div>
                  <div className="flex items-center justify-between py-3 border-b border-[#f3f2f1]">
                    <div>
                      <p className="font-medium text-[#323130]">تنبيهات المخزون</p>
                      <p className="text-sm text-[#605e5c]">إشعار عند انخفاض المخزون</p>
                    </div>
                    <input type="checkbox" defaultChecked className="w-5 h-5 text-[#0078d4] rounded" />
                  </div>
                  <div className="flex items-center justify-between py-3">
                    <div>
                      <p className="font-medium text-[#323130]">إشعارات المهام</p>
                      <p className="text-sm text-[#605e5c]">تذكير بالمهام القادمة</p>
                    </div>
                    <input type="checkbox" className="w-5 h-5 text-[#0078d4] rounded" />
                  </div>
                </div>
              </FluentCard>
            )}

            {activeTab === 'security' && (
              <FluentCard title="الأمان" subtitle="إعدادات الأمان والخصوصية">
                <div className="space-y-4 max-w-xl">
                  <FluentFormField label="تغيير كلمة المرور">
                    <FluentInput type="password" placeholder="كلمة المرور الحالية" />
                  </FluentFormField>
                  <FluentInput type="password" placeholder="كلمة المرور الجديدة" />
                  <FluentInput type="password" placeholder="تأكيد كلمة المرور" />
                  <div className="flex items-center justify-between py-3 border-t border-[#f3f2f1]">
                    <div>
                      <p className="font-medium text-[#323130]">المصادقة الثنائية (2FA)</p>
                      <p className="text-sm text-[#605e5c]">تفعيل المصادقة الثنائية</p>
                    </div>
                    <input type="checkbox" className="w-5 h-5 text-[#0078d4] rounded" />
                  </div>
                </div>
              </FluentCard>
            )}

            {activeTab === 'database' && (
              <FluentCard title="قاعدة البيانات" subtitle="إدارة النسخ الاحتياطي والاستعادة">
                <div className="space-y-4 max-w-xl">
                  <div className="p-4 bg-[#f3f2f1] rounded-sm">
                    <p className="font-medium text-[#323130]">آخر نسخة احتياطية</p>
                    <p className="text-sm text-[#605e5c] mt-1">2026-07-10 03:00 AM</p>
                  </div>
                  <div className="flex gap-3">
                    <button className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">نسخ احتياطي الآن</button>
                    <button className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">استعادة</button>
                  </div>
                </div>
              </FluentCard>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
