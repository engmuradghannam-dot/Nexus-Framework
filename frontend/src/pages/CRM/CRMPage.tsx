// pages/CRM/CRMPage.tsx
import { useEffect, useMemo, useState } from 'react';
import { HeartHandshake, Users, Plus, RefreshCw, ArrowUpRight, AlertTriangle, CheckCircle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { crmApi } from '../../services/api';

const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const LEAD_STATUS_LABEL: Record<string, string> = { Open: 'مفتوح', Replied: 'تم الرد', Opportunity: 'فرصة', Quotation: 'عرض سعر', Lost: 'خسارة', Converted: 'محوّل' };
const LEAD_STATUS_VARIANT: Record<string, any> = { Open: 'info', Replied: 'warning', Opportunity: 'success', Quotation: 'success', Lost: 'error', Converted: 'success' };
const OPP_STATUS_LABEL: Record<string, string> = { Open: 'مفتوحة', Quotation: 'عرض سعر', Converted: 'محوّلة', Lost: 'خسارة' };
const OPP_STATUS_VARIANT: Record<string, any> = { Open: 'info', Quotation: 'warning', Converted: 'success', Lost: 'error' };

export default function CRMPage() {
  const [leads, setLeads] = useState<any[]>([]);
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const [leadPanel, setLeadPanel] = useState(false);
  const [newLead, setNewLead] = useState<any>({});
  const [oppPanel, setOppPanel] = useState(false);
  const [newOpp, setNewOpp] = useState<any>({});

  const reload = () => {
    setLoading(true);
    Promise.all([crmApi.leads(), crmApi.opportunities()])
      .then(([l, o]) => { setLeads(l); setOpportunities(o); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(reload, []);

  const stats = useMemo(() => ({
    openLeads: leads.filter((l) => l.status === 'Open' || l.status === 'Replied').length,
    opportunities: opportunities.length,
    pipelineValue: opportunities.filter((o) => o.status === 'Open' || o.status === 'Quotation').reduce((s, o) => s + Number(o.expected_amount || 0), 0),
  }), [leads, opportunities]);

  const openNewLead = () => { setNewLead({ lead_name: '', organization: '', source: '' }); setError(''); setLeadPanel(true); };
  const saveLead = async () => {
    try { await crmApi.createLead(newLead); setLeadPanel(false); reload(); }
    catch (e: any) { setError(formatApiError(e)); }
  };

  const convertToOpportunity = async (lead: any) => {
    try {
      await crmApi.createOpportunity({ lead: lead.id, opportunity_name: lead.lead_name, customer_name: lead.organization, status: 'Open' });
      await crmApi.updateLead(lead.id, { status: 'Opportunity' });
      setNotice(`تم تحويل "${lead.lead_name}" إلى فرصة بيعية.`);
      reload();
    } catch (e: any) { setError(formatApiError(e)); }
  };

  const openNewOpp = () => { setNewOpp({ opportunity_name: '', customer_name: '', expected_amount: 0, probability: 50 }); setError(''); setOppPanel(true); };
  const saveOpp = async () => {
    try { await crmApi.createOpportunity(newOpp); setOppPanel(false); reload(); }
    catch (e: any) { setError(formatApiError(e)); }
  };

  const setOppStatus = async (id: number, status: string) => {
    await crmApi.updateOpportunity(id, { status });
    reload();
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar
        title="إدارة علاقات العملاء" subtitle="CRM — العملاء المحتملون والفرص البيعية"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new-lead', label: 'عميل محتمل جديد', icon: <Plus size={16} />, variant: 'secondary', onClick: openNewLead },
          { id: 'new-opp', label: 'فرصة بيعية جديدة', icon: <Plus size={16} />, variant: 'primary', onClick: openNewOpp },
        ]}
      />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-3 gap-4">
          <FluentStatsCard title="عملاء محتملون مفتوحون" value={stats.openLeads} icon={<Users size={20} />} color="blue" />
          <FluentStatsCard title="الفرص البيعية" value={stats.opportunities} icon={<HeartHandshake size={20} />} color="purple" />
          <FluentStatsCard title="قيمة خط الأنابيب المتوقعة" value={fmt(stats.pipelineValue)} icon={<HeartHandshake size={20} />} color="green" />
        </div>

        {notice && <div className="flex items-center gap-2 rounded-md border border-[#107c10]/30 bg-[#f3faf3] px-3 py-2 text-sm text-[#107c10]"><CheckCircle size={16} /> {notice}</div>}

        <FluentTable
          title="العملاء المحتملون"
          subtitle={loading ? 'جارٍ التحميل…' : `${leads.length} عميل محتمل`}
          columns={[
            { key: 'lead_name', label: 'الاسم', sortable: true },
            { key: 'organization', label: 'الجهة' },
            { key: 'source', label: 'المصدر' },
            { key: 'status', label: 'الحالة', render: (v: string) => <FluentBadge label={LEAD_STATUS_LABEL[v] || v} variant={LEAD_STATUS_VARIANT[v] || 'info'} size="small" /> },
            {
              key: '__convert', label: '', render: (_: any, row: any) => (
                row.status !== 'Converted' && row.status !== 'Lost' && row.status !== 'Opportunity' ? (
                  <button onClick={(e) => { e.stopPropagation(); convertToOpportunity(row); }} className="flex items-center gap-1 text-xs text-[#0078d4] border border-[#0078d4] px-2 py-1 rounded hover:bg-[#eff6fc]">
                    <ArrowUpRight size={12} /> تحويل لفرصة
                  </button>
                ) : null
              ),
            },
          ]}
          data={leads}
        />

        <FluentTable
          title="الفرص البيعية"
          subtitle={loading ? 'جارٍ التحميل…' : `${opportunities.length} فرصة`}
          columns={[
            { key: 'opportunity_name', label: 'اسم الفرصة', sortable: true },
            { key: 'customer_name', label: 'العميل' },
            { key: 'expected_amount', label: 'القيمة المتوقعة', render: (v: any) => fmt(v) },
            { key: 'probability', label: 'الاحتمالية', render: (v: any) => `${v}%` },
            { key: 'status', label: 'الحالة', render: (v: string, row: any) => (
                <FluentSelect value={v} onChange={(e) => setOppStatus(row.id, e.target.value)} className="!py-1 !text-xs w-32" onClick={(e: any) => e.stopPropagation()}>
                  {Object.entries(OPP_STATUS_LABEL).map(([k, label]) => <option key={k} value={k}>{label}</option>)}
                </FluentSelect>
              ) },
          ]}
          data={opportunities}
        />
      </div>

      <FluentPanel isOpen={leadPanel} onClose={() => setLeadPanel(false)} title="عميل محتمل جديد"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setLeadPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={saveLead} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        {error && <div className="mb-4 flex items-start gap-2 rounded-md border border-[#a4262c]/30 bg-[#fdf2f2] px-3 py-2 text-sm text-[#a4262c]"><AlertTriangle size={16} className="mt-0.5 shrink-0" /> {error}</div>}
        <div className="space-y-3">
          <FluentFormField label="الاسم" required><FluentInput value={newLead.lead_name || ''} onChange={(e) => setNewLead({ ...newLead, lead_name: e.target.value })} /></FluentFormField>
          <FluentFormField label="الجهة / الشركة"><FluentInput value={newLead.organization || ''} onChange={(e) => setNewLead({ ...newLead, organization: e.target.value })} /></FluentFormField>
          <FluentFormField label="البريد الإلكتروني"><FluentInput type="email" value={newLead.email || ''} onChange={(e) => setNewLead({ ...newLead, email: e.target.value })} /></FluentFormField>
          <FluentFormField label="الهاتف"><FluentInput value={newLead.phone || ''} onChange={(e) => setNewLead({ ...newLead, phone: e.target.value })} /></FluentFormField>
          <FluentFormField label="المصدر"><FluentInput value={newLead.source || ''} onChange={(e) => setNewLead({ ...newLead, source: e.target.value })} placeholder="موقع إلكتروني، إحالة..." /></FluentFormField>
        </div>
      </FluentPanel>

      <FluentPanel isOpen={oppPanel} onClose={() => setOppPanel(false)} title="فرصة بيعية جديدة"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setOppPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={saveOpp} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        {error && <div className="mb-4 flex items-start gap-2 rounded-md border border-[#a4262c]/30 bg-[#fdf2f2] px-3 py-2 text-sm text-[#a4262c]"><AlertTriangle size={16} className="mt-0.5 shrink-0" /> {error}</div>}
        <div className="space-y-3">
          <FluentFormField label="اسم الفرصة" required><FluentInput value={newOpp.opportunity_name || ''} onChange={(e) => setNewOpp({ ...newOpp, opportunity_name: e.target.value })} /></FluentFormField>
          <FluentFormField label="العميل"><FluentInput value={newOpp.customer_name || ''} onChange={(e) => setNewOpp({ ...newOpp, customer_name: e.target.value })} /></FluentFormField>
          <FluentFormField label="القيمة المتوقعة"><FluentInput type="number" step="0.01" value={newOpp.expected_amount || 0} onChange={(e) => setNewOpp({ ...newOpp, expected_amount: e.target.value })} /></FluentFormField>
          <FluentFormField label="نسبة الاحتمالية %"><FluentInput type="number" min="0" max="100" value={newOpp.probability ?? 50} onChange={(e) => setNewOpp({ ...newOpp, probability: e.target.value })} /></FluentFormField>
        </div>
      </FluentPanel>
    </div>
  );
}

function formatApiError(e: any): string {
  const data = e?.response?.data;
  if (!data) return 'حدث خطأ غير متوقع.';
  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  const parts: string[] = [];
  for (const [k, v] of Object.entries(data)) {
    parts.push(Array.isArray(v) ? v.join(' ') : String(v));
  }
  return parts.join(' — ') || 'حدث خطأ غير متوقع.';
}
