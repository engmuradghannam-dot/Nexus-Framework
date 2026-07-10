// pages/Users/UsersPage.tsx
import { useState } from 'react';
import { 
  Users, Plus, Search, Filter, Shield, Mail, Phone, 
  Building2, MoreVertical, Edit2, Trash2, UserPlus, Lock 
} from 'lucide-react';

interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: string;
  department: string;
  branch: string;
  status: 'active' | 'inactive' | 'suspended';
  lastLogin: string;
  avatar?: string;
}

const demoUsers: User[] = [
  {
    id: '1', name: 'أحمد محمد العلي', email: 'ahmed@company.com', phone: '+966 50 123 4567',
    role: 'مدير عام', department: 'الإدارة العليا', branch: 'الرياض',
    status: 'active', lastLogin: '2026-07-10 09:30'
  },
  {
    id: '2', name: 'سارة أحمد الخالد', email: 'sara@company.com', phone: '+966 50 987 6543',
    role: 'مديرة مشاريع', department: 'إدارة المشاريع', branch: 'جدة',
    status: 'active', lastLogin: '2026-07-10 08:15'
  },
  {
    id: '3', name: 'خالد السالم الفهد', email: 'khaled@company.com', phone: '+966 50 456 7890',
    role: 'محاسب', department: 'المالية', branch: 'الدمام',
    status: 'inactive', lastLogin: '2026-07-05 14:20'
  },
  {
    id: '4', name: 'فاطمة الزهراء', email: 'fatima@company.com', phone: '+966 50 789 0123',
    role: 'مطورة', department: 'تقنية المعلومات', branch: 'الرياض',
    status: 'active', lastLogin: '2026-07-10 10:45'
  }
];

const roleColors: Record<string, string> = {
  'مدير عام': 'bg-purple-100 text-purple-700',
  'مديرة مشاريع': 'bg-blue-100 text-blue-700',
  'محاسب': 'bg-green-100 text-green-700',
  'مطورة': 'bg-orange-100 text-orange-700',
  'default': 'bg-gray-100 text-gray-700'
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>(demoUsers);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRole, setFilterRole] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterBranch, setFilterBranch] = useState('');

  const filtered = users.filter(u => {
    const matchSearch = !searchQuery || u.name.includes(searchQuery) || u.email.includes(searchQuery);
    const matchRole = !filterRole || u.role === filterRole;
    const matchStatus = !filterStatus || u.status === filterStatus;
    const matchBranch = !filterBranch || u.branch === filterBranch;
    return matchSearch && matchRole && matchStatus && matchBranch;
  });

  const roles = [...new Set(users.map(u => u.role))];
  const branches = [...new Set(users.map(u => u.branch))];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-100 rounded-xl"><Users className="text-indigo-600" size={24} /></div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">إدارة المستخدمين</h1>
              <p className="text-sm text-gray-500">User Management — إدارة الموظفين والصلاحيات</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-2 px-4 py-2.5 border border-gray-200 rounded-xl hover:bg-gray-50">
              <Lock size={18} /> الصلاحيات
            </button>
            <button className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors">
              <UserPlus size={18} /> إضافة مستخدم
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 p-6">
        {[
          { label: 'إجمالي المستخدمين', value: users.length, icon: Users, color: 'bg-indigo-500' },
          { label: 'نشط', value: users.filter(u => u.status === 'active').length, icon: Shield, color: 'bg-green-500' },
          { label: 'غير نشط', value: users.filter(u => u.status === 'inactive').length, icon: Lock, color: 'bg-gray-500' },
          { label: 'موقوف', value: users.filter(u => u.status === 'suspended').length, icon: Lock, color: 'bg-red-500' }
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl border p-4 flex items-center gap-4">
            <div className={`w-12 h-12 ${stat.color} rounded-xl flex items-center justify-center text-white`}>
              <stat.icon size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-800">{stat.value}</p>
              <p className="text-sm text-gray-500">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="px-6 pb-4">
        <div className="bg-white rounded-xl border p-4 flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[300px]">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="البحث باسم أو بريد..."
              className="w-full pr-10 pl-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500" />
          </div>
          <select value={filterRole} onChange={(e) => setFilterRole(e.target.value)}
            className="border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-indigo-500">
            <option value="">كل الأدوار</option>
            {roles.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
          <select value={filterBranch} onChange={(e) => setFilterBranch(e.target.value)}
            className="border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-indigo-500">
            <option value="">كل الفروع</option>
            {branches.map(b => <option key={b} value={b}>{b}</option>)}
          </select>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
            className="border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-indigo-500">
            <option value="">كل الحالات</option>
            <option value="active">نشط</option>
            <option value="inactive">غير نشط</option>
            <option value="suspended">موقوف</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="px-6 pb-6">
        <div className="bg-white rounded-2xl border shadow-sm overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">المستخدم</th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الدور</th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">القسم</th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الفرع</th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الحالة</th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">آخر دخول</th>
                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700">الإجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filtered.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold">
                        {user.name.charAt(0)}
                      </div>
                      <div>
                        <p className="font-semibold text-gray-800">{user.name}</p>
                        <div className="flex items-center gap-3 text-sm text-gray-500 mt-0.5">
                          <span className="flex items-center gap-1"><Mail size={12} /> {user.email}</span>
                          <span className="flex items-center gap-1"><Phone size={12} /> {user.phone}</span>
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${roleColors[user.role] || roleColors.default}`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{user.department}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1"><Building2 size={14} className="text-indigo-400" /> {user.branch}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      user.status === 'active' ? 'bg-green-100 text-green-700' : 
                      user.status === 'inactive' ? 'bg-gray-100 text-gray-700' : 
                      'bg-red-100 text-red-700'
                    }`}>
                      {user.status === 'active' ? 'نشط' : user.status === 'inactive' ? 'غير نشط' : 'موقوف'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{user.lastLogin}</td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button className="p-2 hover:bg-indigo-50 text-indigo-600 rounded-lg transition-colors"><Edit2 size={16} /></button>
                      <button className="p-2 hover:bg-red-50 text-red-600 rounded-lg transition-colors"><Trash2 size={16} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
