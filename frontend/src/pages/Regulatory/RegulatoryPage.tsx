// pages/Regulatory/RegulatoryPage.tsx
import { useState } from 'react';
import { 
  Shield, CheckCircle, AlertTriangle, XCircle, Clock, 
  FileText, Search, Plus, Filter, Download, Calendar, Flag 
} from 'lucide-react';

interface ComplianceRule {
  id: string;
  title: string;
  category: string;
  status: 'compliant' | 'non_compliant' | 'in_review' | 'pending';
  priority: 'critical' | 'high' | 'medium' | 'low';
  lastChecked: string;
  nextReview: string;
  assignedTo: string;
  description: string;
}

const demoRules: ComplianceRule[] = [
  {
    id: '1', title: 'حماية البيانات الشخصية (GDPR)', category: 'أمن المعلومات',
    status: 'compliant', priority: 'critical', lastChecked: '2026-07-01', nextReview: '2026-10-01',
    assignedTo: 'فريق الأمن', description: 'الالتزام بمعايير حماية البيانات الشخصية'
  },
  {
    id: '2', title: 'معايير ISO 27001', category: 'الأمن السيبراني',
    status: 'in_review', priority: 'high', lastChecked: '2026-06-15', nextReview: '2026-08-15',
    assignedTo: 'أحمد محمد', description: 'تطبيق معايير إدارة أمن المعلومات'
  },
  {
    id: '3', title: 'الالتزام الضريبي', category: 'مالي',
    status: 'pending', priority: 'medium', lastChecked: '2026-05-20', nextReview: '2026-09-20',
    assignedTo: 'المالية', description: 'الإقرار الضريبي الدوري'
  }
];

const statusConfig = {
  compliant: { label: 'متوافق', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  non_compliant: { label: 'غير متوافق', color: 'bg-red-100 text-red-700', icon: XCircle },
  in_review: { label: 'قيد المراجعة', color: 'bg-yellow-100 text-yellow-700', icon: Clock },
  pending: { label: 'معلق', color: 'bg-gray-100 text-gray-700', icon: AlertTriangle }
};

export default function RegulatoryPage() {
  const [rules, setRules] = useState<ComplianceRule[]>(demoRules);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [showForm, setShowForm] = useState(false);

  const filtered = rules.filter(r => {
    const matchSearch = !searchQuery || r.title.includes(searchQuery) || r.category.includes(searchQuery);
    const matchStatus = !filterStatus || r.status === filterStatus;
    const matchPriority = !filterPriority || r.priority === filterPriority;
    return matchSearch && matchStatus && matchPriority;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-xl"><Shield className="text-green-600" size={24} /></div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">الالتزام التنظيمي</h1>
              <p className="text-sm text-gray-500">Regulatory Compliance — إدارة المعايير والالتزامات</p>
            </div>
          </div>
          <button onClick={() => setShowForm(true)} className="flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-colors">
            <Plus size={18} /> إضافة قاعدة
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white border-b p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[300px]">
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="البحث في القواعد..."
              className="w-full pr-10 pl-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500" />
          </div>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
            className="border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-green-500">
            <option value="">كل الحالات</option>
            <option value="compliant">متوافق</option>
            <option value="non_compliant">غير متوافق</option>
            <option value="in_review">قيد المراجعة</option>
            <option value="pending">معلق</option>
          </select>
          <select value={filterPriority} onChange={(e) => setFilterPriority(e.target.value)}
            className="border border-gray-200 rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-green-500">
            <option value="">كل الأولويات</option>
            <option value="critical">حرج</option>
            <option value="high">عالي</option>
            <option value="medium">متوسط</option>
            <option value="low">منخفض</option>
          </select>
          <button className="flex items-center gap-2 px-4 py-2.5 border border-gray-200 rounded-xl hover:bg-gray-50">
            <Download size={18} /> تصدير
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 p-6">
        {[
          { label: 'متوافق', value: rules.filter(r => r.status === 'compliant').length, color: 'bg-green-500' },
          { label: 'غير متوافق', value: rules.filter(r => r.status === 'non_compliant').length, color: 'bg-red-500' },
          { label: 'قيد المراجعة', value: rules.filter(r => r.status === 'in_review').length, color: 'bg-yellow-500' },
          { label: 'معلق', value: rules.filter(r => r.status === 'pending').length, color: 'bg-gray-500' }
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl border p-4 flex items-center gap-4">
            <div className={`w-12 h-12 ${stat.color} rounded-xl flex items-center justify-center text-white font-bold`}>{stat.value}</div>
            <div><p className="text-sm text-gray-500">{stat.label}</p></div>
          </div>
        ))}
      </div>

      {/* Rules List */}
      <div className="px-6 pb-6 space-y-4">
        {filtered.map((rule) => {
          const StatusIcon = statusConfig[rule.status].icon;
          return (
            <div key={rule.id} className="bg-white rounded-xl border shadow-sm p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-xl ${statusConfig[rule.status].color.split(' ')[0]}`}>
                    <StatusIcon size={20} className={statusConfig[rule.status].color.split(' ')[1]} />
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-800">{rule.title}</h3>
                    <p className="text-sm text-gray-500 mt-1">{rule.description}</p>
                    <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                      <span className="flex items-center gap-1"><Calendar size={14} /> آخر فحص: {rule.lastChecked}</span>
                      <span className="flex items-center gap-1"><Clock size={14} /> المراجعة القادمة: {rule.nextReview}</span>
                      <span className="flex items-center gap-1"><FileText size={14} /> {rule.category}</span>
                    </div>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusConfig[rule.status].color}`}>
                    {statusConfig[rule.status].label}
                  </span>
                  <span className={`text-xs font-medium ${rule.priority === 'critical' ? 'text-red-600' : rule.priority === 'high' ? 'text-orange-600' : 'text-gray-500'}`}>
                    {rule.priority === 'critical' ? 'حرج' : rule.priority === 'high' ? 'عالي' : rule.priority === 'medium' ? 'متوسط' : 'منخفض'}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
