// pages/Controls/ControlsPage.tsx
import { useEffect, useState } from 'react';
import { ClipboardCheck, CheckCircle, XCircle, Clock, RefreshCw } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { controlsApi } from '../../services/api';

export default function ControlsPage() {
  const [summary, setSummary] = useState<any>(null);
  const [byForm, setByForm] = useState<any[]>([]);
  const [library, setLibrary] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

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
      setByForm(Array.isArray(f) ? f : []);
      setLibrary((lib as any).results || lib || []);
      setCategories(Array.isArray(cat) ? cat : []);
    } catch (e) {
      console.error('Error loading controls:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const stats = summary
    ? [
        { title: 'إجمالي الضوابط', value: summary.total, icon: <ClipboardCheck size={20} />, color: 'blue' as const },
        { title: 'مطبّقة', value: summary.present, subtitle: `${summary.coverage_percent}% تغطية`, icon: <CheckCircle size={20} />, color: 'green' as const },
        { title: 'ناقصة', value: summary.missing, icon: <XCircle size={20} />, color: 'red' as const },
        { title: 'مخطّطة', value: summary.planned, icon: <Clock size={20} />, color: 'orange' as const },
      ]
    : [];

  const libraryColumns = [
    { key: 'control_id', label: 'الرمز', sortable: true },
    { key: 'control_name', label: 'الضابط', sortable: true },
    { key: 'industry', label: 'الصناعة', sortable: true },
    { key: 'module', label: 'الوحدة', sortable: true },
    { key: 'ai_agent', label: 'وكيل الذكاء', sortable: true },
    { key: 'compliance', label: 'الامتثال', render: (v: string) => v ? <FluentBadge label={v} variant="info" size="small" /> : null },
  ];

  const formColumns = [
    { key: 'form_name', label: 'النموذج', sortable: true },
    { key: 'present', label: 'مطبّق', sortable: true },
    { key: 'total', label: 'الإجمالي', sortable: true },
    { key: 'coverage_percent', label: 'التغطية', sortable: true, render: (v: number) => (
      <FluentBadge label={`${v}%`} variant={v >= 80 ? 'success' : v >= 50 ? 'warning' : 'error'} size="small" />
    )},
  ];

  return (
    <div className="min-h-screen bg-[#faf9f8]" dir="rtl">
      <FluentCommandBar
        title="مكتبة الضوابط"
        subtitle="Controls Library — Coverage & Compliance"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: load },
        ]}
      />
      <div className="p-6 space-y-6">
        {loading ? (
          <div className="text-[#605e5c]">جارٍ التحميل…</div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              {stats.map((s) => <FluentStatsCard key={s.title} {...s} />)}
            </div>

            <FluentTable
              title="مكتبة الضوابط الصناعية"
              subtitle={`${library.length} ضابط`}
              columns={libraryColumns}
              data={library}
            />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <FluentTable
                  title="تغطية النماذج"
                  subtitle={`${byForm.length} نموذج`}
                  columns={formColumns}
                  data={byForm}
                />
              </div>
              <FluentCard>
                <h3 className="text-sm font-semibold text-[#323130] mb-3">الصناعات حسب الفئة</h3>
                <div className="space-y-2">
                  {categories.map((c) => (
                    <div key={c.category || 'other'} className="flex items-center justify-between border-b border-[#edebe9] py-1.5">
                      <span className="text-sm text-[#323130]">{c.category || 'غير مصنّف'}</span>
                      <span className="rounded-full bg-[#f3f2f1] px-2 py-0.5 text-xs text-[#605e5c]">{c.count}</span>
                    </div>
                  ))}
                </div>
              </FluentCard>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
