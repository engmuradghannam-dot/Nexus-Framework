// pages/Controls/ControlsPage.tsx
import { useEffect, useState } from 'react';
import { ClipboardCheck, CheckCircle, XCircle, Clock, RefreshCw } from 'lucide-react';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { controlsApi } from '../../services/api';

const STATUS_LABEL: Record<string, { label: string; variant: any }> = {
  present: { label: 'مطبّق', variant: 'success' },
  missing: { label: 'ناقص', variant: 'error' },
  planned: { label: 'مخطّط', variant: 'warning' },
};

export default function ControlsPage() {
  const [summary, setSummary] = useState<any>(null);
  const [byForm, setByForm] = useState<any[]>([]);
  const [library, setLibrary] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [selectedForm, setSelectedForm] = useState<string>('');
  const [formInputs, setFormInputs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [inputsLoading, setInputsLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [s, f, lib, cat] = await Promise.all([
        controlsApi.summary(),
        controlsApi.byForm(),
        controlsApi.industryControls(),
        controlsApi.categories(),
      ]);
      setSummary(s);
      const forms = Array.isArray(f) ? f : [];
      setByForm(forms);
      setLibrary((lib as any).results || lib || []);
      setCategories(Array.isArray(cat) ? cat : []);
      if (forms.length && !selectedForm) setSelectedForm(forms[0].form_name);
    } catch (e) {
      console.error('Error loading controls:', e);
    } finally {
      setLoading(false);
    }
  };

  const loadInputs = async (formName: string) => {
    if (!formName) return;
    setInputsLoading(true);
    try {
      const res = await controlsApi.formControls(formName);
      setFormInputs((res as any).results || res || []);
    } catch (e) {
      console.error('Error loading form inputs:', e);
      setFormInputs([]);
    } finally {
      setInputsLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (selectedForm) loadInputs(selectedForm);
  }, [selectedForm]);

  const stats = summary
    ? [
        { title: 'إجمالي المدخلات', value: summary.total, icon: <ClipboardCheck size={20} />, color: 'blue' as const },
        { title: 'مطبّقة', value: summary.present, subtitle: `${summary.coverage_percent}% تغطية`, icon: <CheckCircle size={20} />, color: 'green' as const },
        { title: 'ناقصة', value: summary.missing, icon: <XCircle size={20} />, color: 'red' as const },
        { title: 'مخطّطة', value: summary.planned, icon: <Clock size={20} />, color: 'orange' as const },
      ]
    : [];

  const inputColumns = [
    { key: 'seq', label: '#', sortable: true },
    { key: 'input_name', label: 'الحقل / المدخل', sortable: true },
    { key: 'input_type', label: 'النوع', sortable: true, render: (v: string) => (
      <span className="rounded bg-[#f3f2f1] px-2 py-0.5 text-xs text-[#605e5c]">{v || '—'}</span>
    )},
    { key: 'priority', label: 'الأولوية', sortable: true, render: (v: string) => (
      <FluentBadge label={v} variant={v === 'High' ? 'error' : v === 'Medium' ? 'warning' : 'neutral'} size="small" />
    )},
    { key: 'status', label: 'الحالة', sortable: true, render: (v: string) => {
      const s = STATUS_LABEL[v] || { label: v, variant: 'neutral' };
      return <FluentBadge label={s.label} variant={s.variant} size="small" />;
    }},
  ];

  const libraryColumns = [
    { key: 'control_id', label: 'الرمز', sortable: true },
    { key: 'control_name', label: 'الضابط', sortable: true },
    { key: 'industry', label: 'الصناعة', sortable: true },
    { key: 'module', label: 'الوحدة', sortable: true },
    { key: 'ai_agent', label: 'وكيل الذكاء', sortable: true },
    { key: 'compliance', label: 'الامتثال', render: (v: string) => v ? <FluentBadge label={v} variant="info" size="small" /> : null },
  ];

  const selectedFormMeta = byForm.find((f) => f.form_name === selectedForm);

  return (
    <div className="space-y-6" dir="rtl">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#323130]">مكتبة الضوابط</h1>
          <p className="text-sm text-[#605e5c] mt-0.5">الضوابط ومدخلاتها والتغطية عبر جميع النماذج</p>
        </div>
        <button onClick={load} className="flex items-center gap-1.5 rounded-sm border border-[#8a8886] px-3 py-1.5 text-sm text-[#323130] hover:bg-[#f3f2f1]">
          <RefreshCw size={14} /> تحديث
        </button>
      </div>

      {loading ? (
        <div className="text-[#605e5c] py-8 text-center">جارٍ التحميل…</div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stats.map((s) => <FluentStatsCard key={s.title} {...s} />)}
          </div>

          {/* Form inputs — each form and its input fields (ERP-style) */}
          <FluentCard>
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
              <div>
                <h3 className="text-base font-semibold text-[#323130]">مدخلات النموذج</h3>
                {selectedFormMeta && (
                  <p className="text-xs text-[#605e5c] mt-0.5">
                    {selectedFormMeta.present}/{selectedFormMeta.total} حقل مطبّق ({selectedFormMeta.coverage_percent}%)
                  </p>
                )}
              </div>
              <select
                value={selectedForm}
                onChange={(e) => setSelectedForm(e.target.value)}
                className="h-9 rounded-sm border border-[#8a8886] bg-white px-3 text-sm text-[#323130] focus:outline-none focus:border-[#0078d4] min-w-[220px]"
              >
                {byForm.map((f) => (
                  <option key={f.form_name} value={f.form_name}>
                    {f.form_name} ({f.total})
                  </option>
                ))}
              </select>
            </div>
            {inputsLoading ? (
              <div className="text-[#605e5c] py-6 text-center">جارٍ تحميل المدخلات…</div>
            ) : (
              <FluentTable columns={inputColumns} data={formInputs} />
            )}
          </FluentCard>

          {/* Industry control library */}
          <FluentTable
            title="مكتبة الضوابط الصناعية"
            subtitle={`${library.length} ضابط`}
            columns={libraryColumns}
            data={library}
          />

          {/* Industries by category */}
          <FluentCard>
            <h3 className="text-base font-semibold text-[#323130] mb-3">الصناعات حسب الفئة</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {categories.map((c) => (
                <div key={c.category || 'other'} className="flex items-center justify-between rounded-sm border border-[#edebe9] px-3 py-2">
                  <span className="text-sm text-[#323130]">{c.category || 'غير مصنّف'}</span>
                  <span className="rounded-full bg-[#f3f2f1] px-2 py-0.5 text-xs text-[#605e5c]">{c.count}</span>
                </div>
              ))}
            </div>
          </FluentCard>
        </>
      )}
    </div>
  );
}
