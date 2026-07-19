// pages/Tenants/TenantsPage.tsx
import { useEffect, useState } from 'react';
import { Building, Plus, RefreshCw, CheckCircle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { tenantsApi } from '../../services/api';

const planMeta: Record<string, { label: string; variant: any }> = {
  free: { label: 'مجاني', variant: 'neutral' },
  pro: { label: 'احترافي', variant: 'info' },
  enterprise: { label: 'مؤسسي', variant: 'success' },
};

export default function TenantsPage() {
  const [tenants, setTenants] = useState<any[]>([]);
  const [current, setCurrent] = useState<any>(null);
  const [showPanel, setShowPanel] = useState(false);
  const [form, setForm] = useState<any>({ plan: 'free' });
  const [msg, setMsg] = useState('');

  const reload = () => {
    tenantsApi.list().then(setTenants).catch(() => {});
    tenantsApi.current().then(setCurrent).catch(() => {});
  };
  useEffect(reload, []);
  const set = (k: string, v: any) => setForm((f: any) => ({ ...f, [k]: v }));

  const save = async () => {
    try {
      const slug = (form.slug || form.name || '').toString().trim().toLowerCase().replace(/\s+/g, '-');
      await tenantsApi.create({ ...form, slug });
      setShowPanel(false); setForm({ plan: 'free' }); setMsg('تم إنشاء المستأجر'); reload();
      setTimeout(() => setMsg(''), 3500);
    } catch { alert('تعذّر الإنشاء — تأكد من الاسم والمعرّف الفريد.'); }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="المستأجرون" subtitle="Multi-tenancy — عزل بيانات المؤسسات"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new', label: 'مستأجر جديد', icon: <Plus size={16} />, variant: 'primary', onClick: () => { setForm({ plan: 'free' }); setShowPanel(true); } },
        ]} />
      <div className="p-6 space-y-6">
        {msg && <div className="flex items-center gap-2 rounded-md border border-[#107c10]/30 bg-[#f3faf3] px-4 py-2 text-sm text-[#107c10]"><CheckCircle size={16} /> {msg}</div>}

        <FluentCard>
          <div className="flex items-center gap-3">
            <Building size={24} className="text-[#0078d4]" />
            <div>
              <p className="text-sm text-[#605e5c]">المستأجر الحالي</p>
              <p className="text-base font-semibold text-[#323130]">
                {current?.is_superuser ? 'مشرف عام — وصول لكل المستأجرين' : current?.tenant?.name || 'غير محدّد'}
              </p>
            </div>
          </div>
        </FluentCard>

        <FluentTable
          title="المستأجرون"
          subtitle={`${tenants.length} مؤسسة`}
          columns={[
            { key: 'name', label: 'الاسم', sortable: true },
            { key: 'slug', label: 'المعرّف' },
            { key: 'subdomain', label: 'النطاق الفرعي', render: (v: string) => v ? `${v}.nexus.app` : '—' },
            { key: 'plan', label: 'الباقة', render: (v: string) => { const m = planMeta[v]; return m ? <FluentBadge label={m.label} variant={m.variant} size="small" /> : v; } },
            { key: 'user_count', label: 'المستخدمون' },
            { key: 'isolation', label: 'عزل البيانات', render: (v: string, r: any) => v === 'dedicated'
              ? <FluentBadge label={`قاعدة خاصة (${r.db_alias})`} variant="success" size="small" />
              : <FluentBadge label="قاعدة مشتركة" variant="neutral" size="small" /> },
            { key: 'is_active', label: 'الحالة', render: (v: boolean) => <FluentBadge label={v ? 'نشط' : 'معطّل'} variant={v ? 'success' : 'error'} size="small" /> },
          ]}
          data={tenants}
          emptyMessage="لا يوجد مستأجرون بعد"
        />
      </div>

      <FluentPanel isOpen={showPanel} onClose={() => setShowPanel(false)} title="مستأجر جديد"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setShowPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={save} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">إنشاء</button>
        </div>}>
        <div className="space-y-3">
          <FluentFormField label="اسم المؤسسة"><FluentInput value={form.name || ''} onChange={(e) => set('name', e.target.value)} /></FluentFormField>
          <FluentFormField label="المعرّف (slug)"><FluentInput value={form.slug || ''} onChange={(e) => set('slug', e.target.value)} placeholder="my-company" /></FluentFormField>
          <FluentFormField label="النطاق الفرعي"><FluentInput value={form.subdomain || ''} onChange={(e) => set('subdomain', e.target.value)} placeholder="mycompany" /></FluentFormField>
          <FluentFormField label="الباقة">
            <FluentSelect value={form.plan || 'free'} onChange={(e) => set('plan', e.target.value)}>
              <option value="free">مجاني</option>
              <option value="pro">احترافي</option>
              <option value="enterprise">مؤسسي</option>
            </FluentSelect>
          </FluentFormField>
          <div className="rounded-sm border border-[#e1dfdd] bg-[#faf9f8] p-3 space-y-2">
            <FluentFormField label="قاعدة بيانات خاصة (اختياري)">
              <FluentInput value={form.database_url || ''} onChange={(e) => set('database_url', e.target.value)} placeholder="postgres://user:pass@host/db" />
            </FluentFormField>
            <p className="text-xs text-[#605e5c] leading-relaxed">
              اتركها فارغة ليستخدم المستأجر القاعدة المشتركة (عزل بالصفوف). عيّنها لتخصيص قاعدة فيزيائية منفصلة له.
              بعد الحفظ، شغّل <code className="bg-white px-1 rounded">provision_tenant_db &lt;id&gt;</code> من الخادم لإنشاء الجداول فيها.
              لأمانها، لا تُعرض القيمة بعد الحفظ — تظهر حالة العزل فقط.
            </p>
          </div>
          <p className="text-xs text-[#605e5c]">كل مستأجر بياناته معزولة تماماً — المستخدمون يرون بيانات مؤسستهم فقط.</p>
        </div>
      </FluentPanel>
    </div>
  );
}
