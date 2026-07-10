// pages/Settings/SettingsPage.tsx
import { useState } from 'react';
import { 
  Settings, Globe, Bell, Lock, Palette, Database, 
  Server, Mail, Smartphone, Save, CheckCircle, AlertTriangle 
} from 'lucide-react';

interface SettingSection {
  id: string;
  title: string;
  icon: any;
  description: string;
}

const sections: SettingSection[] = [
  { id: 'general', title: 'عام', icon: Globe, description: 'إعدادات النظام العامة' },
  { id: 'notifications', title: 'الإشعارات', icon: Bell, description: 'إدارة التنبيهات والإشعارات' },
  { id: 'security', title: 'الأمان', icon: Lock, description: 'كلمة المرور والمصادقة الثنائية' },
  { id: 'appearance', title: 'المظهر', icon: Palette, description: 'اللون واللغة والاتجاه' },
  { id: 'database', title: 'قاعدة البيانات', icon: Database, description: 'النسخ الاحتياطي والاستعادة' },
  { id: 'server', title: 'الخادم', icon: Server, description: 'إعدادات الخادم والأداء' },
];

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState('general');
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gray-100 rounded-xl"><Settings className="text-gray-600" size={24} /></div>
          <div>
            <h1 className="text-xl font-bold text-gray-800">إعدادات النظام</h1>
            <p className="text-sm text-gray-500">System Settings — تخصيص وإدارة النظام</p>
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row">
        {/* Sidebar */}
        <div className="lg:w-64 bg-white border-l p-4">
          <nav className="space-y-1">
            {sections.map((section) => {
              const Icon = section.icon;
              return (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-right ${
                    activeSection === section.id 
                      ? 'bg-gray-800 text-white' 
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <Icon size={20} />
                  <div className="flex-1">
                    <p className="font-medium text-sm">{section.title}</p>
                  </div>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 p-6">
          {saved && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-xl flex items-center gap-2 text-green-700">
              <CheckCircle size={20} /> تم حفظ الإعدادات بنجاح
            </div>
          )}

          {activeSection === 'general' && (
            <div className="space-y-6">
              <h2 className="text-lg font-bold text-gray-800">إعدادات عامة</h2>
              <div className="bg-white rounded-2xl border p-6 space-y-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">اسم الشركة</label>
                    <input type="text" defaultValue="Nexus Framework" className="w-full border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-gray-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">البريد الإلكتروني الرسمي</label>
                    <input type="email" defaultValue="info@nexus.com" className="w-full border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-gray-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">اللغة الافتراضية</label>
                    <select className="w-full border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-gray-500">
                      <option value="ar">العربية</option>
                      <option value="en">English</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">المنطقة الزمنية</label>
                    <select className="w-full border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-gray-500">
                      <option>الرياض (GMT+3)</option>
                      <option>دبي (GMT+4)</option>
                      <option>UTC</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'notifications' && (
            <div className="space-y-6">
              <h2 className="text-lg font-bold text-gray-800">إعدادات الإشعارات</h2>
              <div className="bg-white rounded-2xl border p-6 space-y-4">
                {[
                  { label: 'إشعارات البريد الإلكتروني', desc: 'استلام التنبيهات عبر البريد', checked: true },
                  { label: 'إشعارات الجوال', desc: 'استلام التنبيهات على الهاتف', checked: true },
                  { label: 'تنبيهات المخزون المنخفض', desc: 'إشعار عند انخفاض المخزون', checked: true },
                  { label: 'تنبيهات المشاريع', desc: 'إشعار بتغييرات المشاريع', checked: false },
                  { label: 'تقارير أسبوعية', desc: 'إرسال تقرير أسبوعي تلقائياً', checked: true },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between py-3 border-b last:border-0">
                    <div>
                      <p className="font-medium text-gray-800">{item.label}</p>
                      <p className="text-sm text-gray-500">{item.desc}</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" defaultChecked={item.checked} className="sr-only peer" />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-gray-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gray-800"></div>
                    </label>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeSection === 'security' && (
            <div className="space-y-6">
              <h2 className="text-lg font-bold text-gray-800">الأمان</h2>
              <div className="bg-white rounded-2xl border p-6 space-y-5">
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-xl flex items-center gap-2 text-yellow-700">
                  <AlertTriangle size={20} /> تأكد من استخدام كلمة مرور قوية
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">كلمة المرور الحالية</label>
                    <input type="password" className="w-full border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-gray-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">كلمة المرور الجديدة</label>
                    <input type="password" className="w-full border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-gray-500" />
                  </div>
                </div>
                <div className="flex items-center justify-between py-3">
                  <div>
                    <p className="font-medium text-gray-800">المصادقة الثنائية (2FA)</p>
                    <p className="text-sm text-gray-500">تفعيل المصادقة بخطوتين لحماية إضافية</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-gray-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gray-800"></div>
                  </label>
                </div>
                <div className="flex items-center justify-between py-3">
                  <div>
                    <p className="font-medium text-gray-800">تسجيل الدخول بـ Google</p>
                    <p className="text-sm text-gray-500">تفعيل تسجيل الدخول بحساب Google</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" defaultChecked className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-gray-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gray-800"></div>
                  </label>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'appearance' && (
            <div className="space-y-6">
              <h2 className="text-lg font-bold text-gray-800">المظهر</h2>
              <div className="bg-white rounded-2xl border p-6 space-y-5">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">السمة</label>
                  <div className="flex gap-3">
                    {['فاتح', 'داكن', 'تلقائي'].map((theme) => (
                      <button key={theme} className={`px-6 py-3 rounded-xl border transition-colors ${theme === 'فاتح' ? 'bg-gray-800 text-white border-gray-800' : 'border-gray-200 hover:bg-gray-50'}`}>
                        {theme}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">اللون الرئيسي</label>
                  <div className="flex gap-3">
                    {['bg-blue-500', 'bg-purple-500', 'bg-green-500', 'bg-orange-500', 'bg-red-500'].map((color) => (
                      <button key={color} className={`w-10 h-10 rounded-full ${color} ring-2 ring-offset-2 ring-transparent hover:ring-gray-300 transition-all`} />
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">حجم الخط</label>
                  <select className="w-full border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-gray-500">
                    <option>صغير</option>
                    <option selected>متوسط</option>
                    <option>كبير</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'database' && (
            <div className="space-y-6">
              <h2 className="text-lg font-bold text-gray-800">قاعدة البيانات</h2>
              <div className="bg-white rounded-2xl border p-6 space-y-5">
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                  <div>
                    <p className="font-medium text-gray-800">نسخ احتياطي يدوي</p>
                    <p className="text-sm text-gray-500">آخر نسخة: 2026-07-10 03:00</p>
                  </div>
                  <button className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors">إنشاء نسخة</button>
                </div>
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                  <div>
                    <p className="font-medium text-gray-800">استعادة من نسخة</p>
                    <p className="text-sm text-gray-500">استعادة البيانات من نسخة احتياطية</p>
                  </div>
                  <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">استعراض</button>
                </div>
                <div className="flex items-center justify-between py-3">
                  <div>
                    <p className="font-medium text-gray-800">النسخ الاحتياطي التلقائي</p>
                    <p className="text-sm text-gray-500">إنشاء نسخة احتياطية يومياً</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" defaultChecked className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:ring-4 peer-focus:ring-gray-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gray-800"></div>
                  </label>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'server' && (
            <div className="space-y-6">
              <h2 className="text-lg font-bold text-gray-800">الخادم</h2>
              <div className="bg-white rounded-2xl border p-6 space-y-5">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-gray-50 rounded-xl text-center">
                    <p className="text-2xl font-bold text-gray-800">98.5%</p>
                    <p className="text-sm text-gray-500">نسبة التشغيل</p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-xl text-center">
                    <p className="text-2xl font-bold text-gray-800">245ms</p>
                    <p className="text-sm text-gray-500">متوسط الاستجابة</p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-xl text-center">
                    <p className="text-2xl font-bold text-gray-800">1.2GB</p>
                    <p className="text-sm text-gray-500">استخدام الذاكرة</p>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">البيئة</label>
                  <select className="w-full border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-gray-500">
                    <option>إنتاج</option>
                    <option>تطوير</option>
                    <option>اختبار</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">مستوى السجل (Logging)</label>
                  <select className="w-full border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-gray-500">
                    <option>خطأ فقط</option>
                    <option selected>تحذير</option>
                    <option>معلومات</option>
                    <option>تصحيح</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Save Button */}
          <div className="mt-6 flex justify-end">
            <button onClick={handleSave} className="flex items-center gap-2 px-6 py-3 bg-gray-800 text-white rounded-xl hover:bg-gray-700 transition-colors">
              <Save size={18} /> حفظ الإعدادات
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
