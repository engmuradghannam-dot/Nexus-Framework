// pages/CompanySetup/CompanySetupPage.tsx
import { useEffect, useState } from 'react';
import { Building2, Save, CheckCircle2, Layers, Boxes } from 'lucide-react';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { controlsApi } from '../../services/api';

const COUNTRIES: Record<string, { currency: string; language: string; vat: string; tz: string }> = {
  'Saudi Arabia': { currency: 'SAR', language: 'Arabic', vat: '15%', tz: 'Asia/Riyadh' },
  'UAE': { currency: 'AED', language: 'Arabic', vat: '5%', tz: 'Asia/Dubai' },
  'Qatar': { currency: 'QAR', language: 'Arabic', vat: '0%', tz: 'Asia/Qatar' },
  'USA': { currency: 'USD', language: 'English', vat: 'State Based', tz: 'America/New_York' },
};
const COMPANY_TYPES = ['LLC', 'Corporation', 'Holding Company', 'Government', 'Branch'];
const MODULES = ['Finance', 'HR', 'Payroll', 'Procurement', 'Sales', 'CRM', 'Inventory'];
const DEPARTMENTS = ['Finance', 'HR', 'Procurement', 'Sales', 'IT', 'Operations'];

const field = 'h-10 w-full rounded-md border border-[#d1d1d1] bg-white px-3 text-sm text-[#323130] focus:outline-none focus:border-[#0078d4] focus:ring-2 focus:ring-[#0078d4]/30';
const labelCls = 'block text-sm font-medium text-[#323130] mb-1';

export default function CompanySetupPage() {
  const [form, setForm] = useState<any>({
    company_name: '', legal_name: '', company_code: '', company_type: 'LLC',
    country: 'Saudi Arabia', city: '', currency: 'SAR', language: 'Arabic',
    timezone: 'Asia/Riyadh', fiscal_year: 'Jan-Dec', tax_number: '', commercial_registration: '',
    industry: '', sub_industry: '',
  });
  const [sectors, setSectors] = useState<any[]>([]);
  const [sector, setSector] = useState('');
  const [sectorControls, setSectorControls] = useState<any[]>([]);
  const [enabledEntities, setEnabledEntities] = useState<string[]>([]);
  const [modules, setModules] = useState<string[]>(['Finance', 'HR', 'Sales']);
  const [departments, setDepartments] = useState<string[]>(['Finance', 'HR']);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    controlsApi.sectors().then(setSectors).catch(() => {});
  }, []);

  useEffect(() => {
    if (!sector) { setSectorControls([]); return; }
    controlsApi.sectorControls(sector).then((list: any[]) => {
      setSectorControls(list);
      setEnabledEntities(list.map((e) => e.entity)); // enable all by default
    }).catch(() => setSectorControls([]));
  }, [sector]);

  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));

  const onCountry = (c: string) => {
    const meta = COUNTRIES[c];
    setForm((f: any) => ({ ...f, country: c, ...(meta ? { currency: meta.currency, language: meta.language, timezone: meta.tz } : {}) }));
  };

  const toggle = (arr: string[], setArr: (v: string[]) => void, v: string) =>
    setArr(arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);

  const save = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await controlsApi.saveCompanySetup({
        ...form, sector, enabled_modules: modules, departments, enabled_entities: enabledEntities,
      });
      setSaved(true);
    } catch (e) {
      alert('تعذّر الحفظ — تأكد من تعبئة الاسم والرمز.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6" dir="rtl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-[#eff6fc] text-[#0078d4]"><Building2 size={22} /></div>
          <div>
            <h1 className="text-2xl font-bold text-[#323130]">إعداد الشركة</h1>
            <p className="text-sm text-[#605e5c]">تسجيل معلومات الشركة الكاملة واختيار القطاع وضوابطه</p>
          </div>
        </div>
        <button onClick={save} disabled={saving}
          className="flex items-center gap-2 rounded-md bg-[#0078d4] px-4 py-2 text-sm font-medium text-white hover:bg-[#106ebe] disabled:opacity-60">
          <Save size={16} /> {saving ? 'جارٍ الحفظ…' : 'حفظ الإعداد'}
        </button>
      </div>

      {saved && (
        <div className="flex items-center gap-2 rounded-md border border-[#107c10]/30 bg-[#f3faf3] px-4 py-2 text-sm text-[#107c10]">
          <CheckCircle2 size={16} /> تم حفظ إعداد الشركة بنجاح
        </div>
      )}

      {/* Company profile */}
      <FluentCard>
        <h3 className="mb-4 text-base font-semibold text-[#323130]">معلومات الشركة</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div><label className={labelCls}>اسم الشركة *</label><input className={field} value={form.company_name} onChange={(e) => set('company_name', e.target.value)} /></div>
          <div><label className={labelCls}>الاسم القانوني</label><input className={field} value={form.legal_name} onChange={(e) => set('legal_name', e.target.value)} /></div>
          <div><label className={labelCls}>رمز الشركة *</label><input className={field} value={form.company_code} onChange={(e) => set('company_code', e.target.value)} placeholder="ABC001" /></div>
          <div><label className={labelCls}>نوع الشركة</label><select className={field} value={form.company_type} onChange={(e) => set('company_type', e.target.value)}>{COMPANY_TYPES.map((t) => <option key={t}>{t}</option>)}</select></div>
          <div><label className={labelCls}>الدولة</label><select className={field} value={form.country} onChange={(e) => onCountry(e.target.value)}>{Object.keys(COUNTRIES).map((c) => <option key={c}>{c}</option>)}</select></div>
          <div><label className={labelCls}>المدينة</label><input className={field} value={form.city} onChange={(e) => set('city', e.target.value)} /></div>
          <div><label className={labelCls}>العملة</label><input className={field} value={form.currency} readOnly /></div>
          <div><label className={labelCls}>اللغة</label><input className={field} value={form.language} readOnly /></div>
          <div><label className={labelCls}>المنطقة الزمنية</label><input className={field} value={form.timezone} readOnly /></div>
          <div><label className={labelCls}>السنة المالية</label><input className={field} value={form.fiscal_year} onChange={(e) => set('fiscal_year', e.target.value)} /></div>
          <div><label className={labelCls}>الرقم الضريبي</label><input className={field} value={form.tax_number} onChange={(e) => set('tax_number', e.target.value)} /></div>
          <div><label className={labelCls}>السجل التجاري</label><input className={field} value={form.commercial_registration} onChange={(e) => set('commercial_registration', e.target.value)} /></div>
        </div>
      </FluentCard>

      {/* Sector selection */}
      <FluentCard>
        <div className="flex items-center gap-2 mb-3"><Layers size={18} className="text-[#0078d4]" /><h3 className="text-base font-semibold text-[#323130]">القطاع</h3></div>
        <p className="text-sm text-[#605e5c] mb-3">اختر قطاع الشركة — ستظهر الضوابط والكيانات المناسبة له تلقائياً.</p>
        <select className={`${field} md:w-96`} value={sector} onChange={(e) => setSector(e.target.value)}>
          <option value="">— اختر القطاع —</option>
          {sectors.map((s) => <option key={s.sector} value={s.sector}>{s.sector} ({s.entity_count})</option>)}
        </select>
      </FluentCard>

      {/* Sector-specific controls */}
      {sector && (
        <FluentCard>
          <div className="flex items-center gap-2 mb-1"><Boxes size={18} className="text-[#0078d4]" /><h3 className="text-base font-semibold text-[#323130]">ضوابط قطاع «{sector}»</h3></div>
          <p className="text-sm text-[#605e5c] mb-4">الكيانات والضوابط المفعّلة لهذا القطاع — فعّل ما تحتاجه.</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {sectorControls.map((c) => {
              const on = enabledEntities.includes(c.entity);
              return (
                <div key={c.entity} onClick={() => toggle(enabledEntities, setEnabledEntities, c.entity)}
                  className={`cursor-pointer rounded-lg border p-3 transition-colors ${on ? 'border-[#0078d4] bg-[#eff6fc]' : 'border-[#e1dfdd] bg-white hover:border-[#8a8886]'}`}>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-[#323130] text-sm">{c.entity}</span>
                    {on ? <CheckCircle2 size={16} className="text-[#0078d4]" /> : <span className="h-4 w-4 rounded-full border border-[#8a8886]" />}
                  </div>
                  <p className="text-xs text-[#605e5c] mt-1">{c.description}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {(c.fields || []).slice(0, 5).map((f: string) => (
                      <span key={f} className="rounded bg-[#f3f2f1] px-1.5 py-0.5 text-[10px] text-[#605e5c]">{f}</span>
                    ))}
                    {c.fields && c.fields.length > 5 && <span className="text-[10px] text-[#605e5c]">+{c.fields.length - 5}</span>}
                  </div>
                  {c.module && <div className="mt-2"><FluentBadge label={c.module} variant="info" size="small" /></div>}
                </div>
              );
            })}
          </div>
        </FluentCard>
      )}

      {/* Modules + Departments */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FluentCard>
          <h3 className="mb-3 text-base font-semibold text-[#323130]">الوحدات المفعّلة</h3>
          <div className="flex flex-wrap gap-2">
            {MODULES.map((m) => (
              <button key={m} onClick={() => toggle(modules, setModules, m)}
                className={`rounded-full px-3 py-1.5 text-sm border ${modules.includes(m) ? 'border-[#0078d4] bg-[#eff6fc] text-[#0078d4]' : 'border-[#8a8886] text-[#605e5c]'}`}>
                {m}
              </button>
            ))}
          </div>
        </FluentCard>
        <FluentCard>
          <h3 className="mb-3 text-base font-semibold text-[#323130]">الأقسام</h3>
          <div className="flex flex-wrap gap-2">
            {DEPARTMENTS.map((d) => (
              <button key={d} onClick={() => toggle(departments, setDepartments, d)}
                className={`rounded-full px-3 py-1.5 text-sm border ${departments.includes(d) ? 'border-[#0078d4] bg-[#eff6fc] text-[#0078d4]' : 'border-[#8a8886] text-[#605e5c]'}`}>
                {d}
              </button>
            ))}
          </div>
        </FluentCard>
      </div>
    </div>
  );
}
