// components/Industry/IndustryFormModal.tsx
import { useState, useEffect } from 'react';
import { X, Building2, Users, TrendingUp, DollarSign, MapPin, FileText, Tag } from 'lucide-react';

export interface IndustryFormData {
  id?: string;
  name: string;
  sector: string;
  description: string;
  status: 'active' | 'inactive' | 'pending' | 'archived';
  revenue: number;
  employees: number;
  growthRate: number;
  location: string;
  tags: string[];
  logo?: string;
}

interface IndustryFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: IndustryFormData) => void;
  initialData?: IndustryFormData;
}

const initialFormData: IndustryFormData = {
  name: '',
  sector: 'technology',
  description: '',
  status: 'active',
  revenue: 0,
  employees: 0,
  growthRate: 0,
  location: '',
  tags: []
};

export function IndustryFormModal({ isOpen, onClose, onSubmit, initialData }: IndustryFormModalProps) {
  const [formData, setFormData] = useState<IndustryFormData>(initialFormData);
  const [tagInput, setTagInput] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
    } else {
      setFormData(initialFormData);
    }
    setErrors({});
  }, [initialData, isOpen]);

  if (!isOpen) return null;

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) newErrors.name = 'اسم القطاع مطلوب';
    if (!formData.description.trim()) newErrors.description = 'الوصف مطلوب';
    if (formData.revenue < 0) newErrors.revenue = 'الإيرادات يجب أن تكون موجبة';
    if (formData.employees < 0) newErrors.employees = 'عدد الموظفين يجب أن يكون موجباً';
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

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData(prev => ({ ...prev, tags: [...prev.tags, tagInput.trim()] }));
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData(prev => ({ ...prev, tags: prev.tags.filter(t => t !== tagToRemove) }));
  };

  const updateField = (field: keyof IndustryFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => { const n = { ...prev }; delete n[field]; return n; });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-bold text-gray-800">
            {initialData ? 'تعديل القطاع' : 'إضافة قطاع جديد'}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Name & Sector */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                <Building2 size={16} />
                اسم القطاع *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => updateField('name', e.target.value)}
                className={`w-full border rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent ${errors.name ? 'border-red-300' : 'border-gray-200'}`}
                placeholder="مثال: شركة التقنية المتقدمة"
              />
              {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
            </div>

            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                <Tag size={16} />
                التصنيف
              </label>
              <select
                value={formData.sector}
                onChange={(e) => updateField('sector', e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="technology">تقنية المعلومات</option>
                <option value="healthcare">الرعاية الصحية</option>
                <option value="finance">المالية</option>
                <option value="education">التعليم</option>
                <option value="manufacturing">التصنيع</option>
                <option value="retail">التجزئة</option>
                <option value="energy">الطاقة</option>
                <option value="transport">النقل</option>
              </select>
            </div>
          </div>

          {/* Description */}
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
              placeholder="وصف تفصيلي للقطاع..."
            />
            {errors.description && <p className="text-red-500 text-xs mt-1">{errors.description}</p>}
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">الحالة</label>
            <div className="flex gap-3 flex-wrap">
              {[
                { value: 'active', label: 'نشط', color: 'bg-green-100 text-green-700 border-green-200' },
                { value: 'inactive', label: 'غير نشط', color: 'bg-gray-100 text-gray-700 border-gray-200' },
                { value: 'pending', label: 'معلق', color: 'bg-yellow-100 text-yellow-700 border-yellow-200' },
                { value: 'archived', label: 'مؤرشف', color: 'bg-red-100 text-red-700 border-red-200' }
              ].map((status) => (
                <button
                  key={status.value}
                  type="button"
                  onClick={() => updateField('status', status.value)}
                  className={`px-4 py-2 rounded-lg border transition-all ${
                    formData.status === status.value 
                      ? status.color + ' ring-2 ring-offset-1' 
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  {status.label}
                </button>
              ))}
            </div>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                <DollarSign size={16} />
                الإيرادات (مليون)
              </label>
              <input
                type="number"
                value={formData.revenue}
                onChange={(e) => updateField('revenue', parseFloat(e.target.value) || 0)}
                min="0"
                step="0.1"
                className={`w-full border rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent ${errors.revenue ? 'border-red-300' : 'border-gray-200'}`}
              />
              {errors.revenue && <p className="text-red-500 text-xs mt-1">{errors.revenue}</p>}
            </div>

            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                <Users size={16} />
                عدد الموظفين
              </label>
              <input
                type="number"
                value={formData.employees}
                onChange={(e) => updateField('employees', parseInt(e.target.value) || 0)}
                min="0"
                className={`w-full border rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent ${errors.employees ? 'border-red-300' : 'border-gray-200'}`}
              />
              {errors.employees && <p className="text-red-500 text-xs mt-1">{errors.employees}</p>}
            </div>

            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                <TrendingUp size={16} />
                معدل النمو (%)
              </label>
              <input
                type="number"
                value={formData.growthRate}
                onChange={(e) => updateField('growthRate', parseFloat(e.target.value) || 0)}
                step="0.1"
                className="w-full border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Location */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
              <MapPin size={16} />
              الموقع
            </label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => updateField('location', e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="المدينة، الدولة"
            />
          </div>

          {/* Tags */}
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
              <Tag size={16} />
              الوسوم
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                className="flex-1 border border-gray-200 rounded-lg px-3 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="أضف وسماً واضغط Enter"
              />
              <button
                type="button"
                onClick={handleAddTag}
                className="px-4 py-2.5 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                إضافة
              </button>
            </div>
            <div className="flex gap-2 flex-wrap">
              {formData.tags.map((tag) => (
                <span key={tag} className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm">
                  {tag}
                  <button type="button" onClick={() => handleRemoveTag(tag)} className="text-blue-400 hover:text-blue-600">×</button>
                </span>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t">
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
              {initialData ? 'حفظ التعديلات' : 'إضافة القطاع'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
