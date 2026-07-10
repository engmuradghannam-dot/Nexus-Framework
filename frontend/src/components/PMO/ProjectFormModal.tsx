// components/PMO/ProjectFormModal.tsx
import { useState, useEffect } from 'react';
import { X, Briefcase, Users, Calendar, DollarSign, Flag, FileText, Target, AlertTriangle, CheckCircle } from 'lucide-react';

export interface ProjectFormData {
  id?: string;
  name: string;
  description: string;
  status: 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled';
  priority: 'critical' | 'high' | 'medium' | 'low';
  phase: 'initiation' | 'planning' | 'execution' | 'monitoring' | 'closure';
  startDate: string;
  endDate: string;
  budget: number;
  spent: number;
  progress: number;
  manager: string;
  team: string[];
  objectives: string[];
  risks: string[];
  milestones: { title: string; date: string; completed: boolean }[];
}

interface ProjectFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ProjectFormData) => void;
  initialData?: ProjectFormData;
}

const initialFormData: ProjectFormData = {
  name: '',
  description: '',
  status: 'planning',
  priority: 'medium',
  phase: 'initiation',
  startDate: new Date().toISOString().split('T')[0],
  endDate: '',
  budget: 0,
  spent: 0,
  progress: 0,
  manager: '',
  team: [],
  objectives: [],
  risks: [],
  milestones: []
};

export function ProjectFormModal({ isOpen, onClose, onSubmit, initialData }: ProjectFormModalProps) {
  const [formData, setFormData] = useState<ProjectFormData>(initialFormData);
  const [teamInput, setTeamInput] = useState('');
  const [objectiveInput, setObjectiveInput] = useState('');
  const [riskInput, setRiskInput] = useState('');
  const [milestoneTitle, setMilestoneTitle] = useState('');
  const [milestoneDate, setMilestoneDate] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState<'basic' | 'team' | 'milestones' | 'risks'>('basic');

  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
    } else {
      setFormData(initialFormData);
    }
    setErrors({});
    setActiveTab('basic');
  }, [initialData, isOpen]);

  if (!isOpen) return null;

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) newErrors.name = 'اسم المشروع مطلوب';
    if (!formData.description.trim()) newErrors.description = 'الوصف مطلوب';
    if (!formData.startDate) newErrors.startDate = 'تاريخ البدء مطلوب';
    if (!formData.endDate) newErrors.endDate = 'تاريخ الانتهاء مطلوب';
    if (formData.budget < 0) newErrors.budget = 'الميزانية يجب أن تكون موجبة';
    if (formData.progress < 0 || formData.progress > 100) newErrors.progress = 'نسبة الإنجاز بين 0 و 100';
    if (!formData.manager.trim()) newErrors.manager = 'مدير المشروع مطلوب';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onSubmit(formData);
      onClose();
    }
  };

  const updateField = (field: keyof ProjectFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => { const n = { ...prev }; delete n[field]; return n; });
    }
  };

  const addTeamMember = () => {
    if (teamInput.trim() && !formData.team.includes(teamInput.trim())) {
      updateField('team', [...formData.team, teamInput.trim()]);
      setTeamInput('');
    }
  };

  const removeTeamMember = (member: string) => {
    updateField('team', formData.team.filter(m => m !== member));
  };

  const addObjective = () => {
    if (objectiveInput.trim()) {
      updateField('objectives', [...formData.objectives, objectiveInput.trim()]);
      setObjectiveInput('');
    }
  };

  const removeObjective = (obj: string) => {
    updateField('objectives', formData.objectives.filter(o => o !== obj));
  };

  const addRisk = () => {
    if (riskInput.trim()) {
      updateField('risks', [...formData.risks, riskInput.trim()]);
      setRiskInput('');
    }
  };

  const removeRisk = (risk: string) => {
    updateField('risks', formData.risks.filter(r => r !== risk));
  };

  const addMilestone = () => {
    if (milestoneTitle.trim() && milestoneDate) {
      updateField('milestones', [...formData.milestones, { title: milestoneTitle.trim(), date: milestoneDate, completed: false }]);
      setMilestoneTitle('');
      setMilestoneDate('');
    }
  };

  const removeMilestone = (idx: number) => {
    updateField('milestones', formData.milestones.filter((_, i) => i !== idx));
  };

  const toggleMilestone = (idx: number) => {
    const newMilestones = [...formData.milestones];
    newMilestones[idx].completed = !newMilestones[idx].completed;
    updateField('milestones', newMilestones);
  };

  const tabs = [
    { id: 'basic' as const, label: 'معلومات أساسية', icon: Briefcase },
    { id: 'team' as const, label: 'الفريق', icon: Users },
    { id: 'milestones' as const, label: 'المراحل', icon: Target },
    { id: 'risks' as const, label: 'المخاطر', icon: AlertTriangle }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-bold text-gray-800">
            {initialData ? 'تعديل المشروع' : 'مشروع جديد'}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-3 border-b-2 transition-colors whitespace-nowrap ${
                activeTab === tab.id 
                  ? 'border-blue-600 text-blue-600 bg-blue-50' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              <tab.icon size={16} />
              {tab.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          {/* Basic Info Tab */}
          {activeTab === 'basic' && (
            <div className="space-y-5">
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                  <Briefcase size={16} />
                  اسم المشروع *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => updateField('name', e.target.value)}
                  className={`w-full border rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent ${errors.name ? 'border-red-300' : 'border-gray-200'}`}
                  placeholder="اسم المشروع"
                />
                {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
              </div>

              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                  <FileText size={16} />
                  الوصف *
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => updateField('description', e.target.value)}
                  rows={3}
                  className={`w-full border rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent ${errors.description ? 'border-red-300' : 'border-gray-200'}`}
                  placeholder="وصف تفصيلي للمشروع..."
                />
                {errors.description && <p className="text-red-500 text-xs mt-1">{errors.description}</p>}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">الحالة</label>
                  <select
                    value={formData.status}
                    onChange={(e) => updateField('status', e.target.value)}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="planning">تخطيط</option>
                    <option value="active">نشط</option>
                    <option value="on_hold">معلق</option>
                    <option value="completed">مكتمل</option>
                    <option value="cancelled">ملغي</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">الأولوية</label>
                  <select
                    value={formData.priority}
                    onChange={(e) => updateField('priority', e.target.value)}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="critical">حرج</option>
                    <option value="high">عالي</option>
                    <option value="medium">متوسط</option>
                    <option value="low">منخفض</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">المرحلة الحالية</label>
                <div className="flex gap-2 flex-wrap">
                  {[
                    { value: 'initiation', label: 'البدء', color: 'bg-purple-100 text-purple-700 border-purple-200' },
                    { value: 'planning', label: 'التخطيط', color: 'bg-blue-100 text-blue-700 border-blue-200' },
                    { value: 'execution', label: 'التنفيذ', color: 'bg-green-100 text-green-700 border-green-200' },
                    { value: 'monitoring', label: 'المراقبة', color: 'bg-yellow-100 text-yellow-700 border-yellow-200' },
                    { value: 'closure', label: 'الإغلاق', color: 'bg-gray-100 text-gray-700 border-gray-200' }
                  ].map((phase) => (
                    <button
                      key={phase.value}
                      type="button"
                      onClick={() => updateField('phase', phase.value)}
                      className={`px-4 py-2 rounded-lg border transition-all ${
                        formData.phase === phase.value 
                          ? phase.color + ' ring-2 ring-offset-1' 
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      {phase.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                    <Calendar size={16} />
                    تاريخ البدء *
                  </label>
                  <input
                    type="date"
                    value={formData.startDate}
                    onChange={(e) => updateField('startDate', e.target.value)}
                    className={`w-full border rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent ${errors.startDate ? 'border-red-300' : 'border-gray-200'}`}
                  />
                  {errors.startDate && <p className="text-red-500 text-xs mt-1">{errors.startDate}</p>}
                </div>

                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                    <Calendar size={16} />
                    تاريخ الانتهاء *
                  </label>
                  <input
                    type="date"
                    value={formData.endDate}
                    onChange={(e) => updateField('endDate', e.target.value)}
                    className={`w-full border rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent ${errors.endDate ? 'border-red-300' : 'border-gray-200'}`}
                  />
                  {errors.endDate && <p className="text-red-500 text-xs mt-1">{errors.endDate}</p>}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                    <DollarSign size={16} />
                    الميزانية
                  </label>
                  <input
                    type="number"
                    value={formData.budget}
                    onChange={(e) => updateField('budget', parseFloat(e.target.value) || 0)}
                    min="0"
                    step="1000"
                    className={`w-full border rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent ${errors.budget ? 'border-red-300' : 'border-gray-200'}`}
                  />
                  {errors.budget && <p className="text-red-500 text-xs mt-1">{errors.budget}</p>}
                </div>

                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                    <DollarSign size={16} />
                    المنصرف
                  </label>
                  <input
                    type="number"
                    value={formData.spent}
                    onChange={(e) => updateField('spent', parseFloat(e.target.value) || 0)}
                    min="0"
                    step="1000"
                    className="w-full border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                    <Flag size={16} />
                    نسبة الإنجاز (%)
                  </label>
                  <input
                    type="number"
                    value={formData.progress}
                    onChange={(e) => updateField('progress', parseInt(e.target.value) || 0)}
                    min="0"
                    max="100"
                    className={`w-full border rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent ${errors.progress ? 'border-red-300' : 'border-gray-200'}`}
                  />
                  {errors.progress && <p className="text-red-500 text-xs mt-1">{errors.progress}</p>}
                </div>
              </div>

              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                  <Users size={16} />
                  مدير المشروع *
                </label>
                <input
                  type="text"
                  value={formData.manager}
                  onChange={(e) => updateField('manager', e.target.value)}
                  className={`w-full border rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent ${errors.manager ? 'border-red-300' : 'border-gray-200'}`}
                  placeholder="اسم مدير المشروع"
                />
                {errors.manager && <p className="text-red-500 text-xs mt-1">{errors.manager}</p>}
              </div>
            </div>
          )}

          {/* Team Tab */}
          {activeTab === 'team' && (
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">أعضاء الفريق</label>
                <div className="flex gap-2 mb-3">
                  <input
                    type="text"
                    value={teamInput}
                    onChange={(e) => setTeamInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTeamMember())}
                    className="flex-1 border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="اسم العضو"
                  />
                  <button
                    type="button"
                    onClick={addTeamMember}
                    className="px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    إضافة
                  </button>
                </div>
                <div className="flex gap-2 flex-wrap">
                  {formData.team.map((member) => (
                    <span key={member} className="inline-flex items-center gap-1 bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-full text-sm">
                      <Users size={14} />
                      {member}
                      <button type="button" onClick={() => removeTeamMember(member)} className="text-indigo-400 hover:text-indigo-600">×</button>
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">أهداف المشروع</label>
                <div className="flex gap-2 mb-3">
                  <input
                    type="text"
                    value={objectiveInput}
                    onChange={(e) => setObjectiveInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addObjective())}
                    className="flex-1 border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="هدف المشروع"
                  />
                  <button
                    type="button"
                    onClick={addObjective}
                    className="px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    إضافة
                  </button>
                </div>
                <div className="space-y-2">
                  {formData.objectives.map((obj, idx) => (
                    <div key={idx} className="flex items-center gap-2 bg-green-50 text-green-800 px-3 py-2 rounded-lg">
                      <Target size={14} />
                      <span className="flex-1">{obj}</span>
                      <button type="button" onClick={() => removeObjective(obj)} className="text-green-400 hover:text-green-600">×</button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Milestones Tab */}
          {activeTab === 'milestones' && (
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">إضافة مرحلة</label>
                <div className="flex gap-2 mb-3">
                  <input
                    type="text"
                    value={milestoneTitle}
                    onChange={(e) => setMilestoneTitle(e.target.value)}
                    placeholder="عنوان المرحلة"
                    className="flex-1 border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <input
                    type="date"
                    value={milestoneDate}
                    onChange={(e) => setMilestoneDate(e.target.value)}
                    className="border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    type="button"
                    onClick={addMilestone}
                    className="px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    إضافة
                  </button>
                </div>
                <div className="space-y-2">
                  {formData.milestones.map((milestone, idx) => (
                    <div key={idx} className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${milestone.completed ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                      <button
                        type="button"
                        onClick={() => toggleMilestone(idx)}
                        className={milestone.completed ? 'text-green-600' : 'text-gray-400 hover:text-green-600'}
                      >
                        <CheckCircle size={20} />
                      </button>
                      <div className="flex-1">
                        <p className={`font-medium ${milestone.completed ? 'line-through text-gray-500' : 'text-gray-800'}`}>{milestone.title}</p>
                        <p className="text-sm text-gray-500">{milestone.date}</p>
                      </div>
                      <button type="button" onClick={() => removeMilestone(idx)} className="text-red-400 hover:text-red-600">×</button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Risks Tab */}
          {activeTab === 'risks' && (
            <div className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">المخاطر المحتملة</label>
                <div className="flex gap-2 mb-3">
                  <input
                    type="text"
                    value={riskInput}
                    onChange={(e) => setRiskInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addRisk())}
                    className="flex-1 border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="وصف المخاطر"
                  />
                  <button
                    type="button"
                    onClick={addRisk}
                    className="px-4 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    إضافة
                  </button>
                </div>
                <div className="space-y-2">
                  {formData.risks.map((risk, idx) => (
                    <div key={idx} className="flex items-center gap-2 bg-red-50 text-red-800 px-3 py-2 rounded-lg">
                      <AlertTriangle size={14} />
                      <span className="flex-1">{risk}</span>
                      <button type="button" onClick={() => removeRisk(risk)} className="text-red-400 hover:text-red-600">×</button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-6 mt-6 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2.5 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors"
            >
              إلغاء
            </button>
            <button
              type="submit"
              className="px-6 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-sm"
            >
              {initialData ? 'حفظ التعديلات' : 'إنشاء المشروع'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
