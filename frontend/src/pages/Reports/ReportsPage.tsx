// pages/Reports/ReportsPage.tsx
import { useEffect, useState } from 'react';
import { FileBarChart, Play, Save, RefreshCw, Download, Plus, Trash2 } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { reportsApi } from '../../services/api';
import { exportToCsv } from '../../utils/exportCsv';

const SOURCES = [
  ['inventory', 'المخزون'], ['crm', 'العملاء'], ['selling', 'المبيعات'], ['buying', 'المشتريات'],
  ['hr', 'الموارد البشرية'], ['assets', 'الأصول'], ['invoices', 'الفواتير'],
];
const OPS = [['eq', '='], ['ne', '≠'], ['contains', 'يحتوي'], ['>', '>'], ['<', '<'], ['>=', '≥'], ['<=', '≤']];

export default function ReportsPage() {
  const [source, setSource] = useState('inventory');
  const [availFields, setAvailFields] = useState<string[]>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [groupBy, setGroupBy] = useState('');
  const [aggregate, setAggregate] = useState('count');
  const [sumField, setSumField] = useState('');
  const [filters, setFilters] = useState<any[]>([]);
  const [result, setResult] = useState<any>({ columns: [], rows: [] });
  const [saved, setSaved] = useState<any[]>([]);
  const [reportName, setReportName] = useState('');

  const loadSaved = () => reportsApi.list().then(setSaved).catch(() => {});
  useEffect(loadSaved, []);
  // discover fields when source changes
  useEffect(() => {
    reportsApi.preview({ source }).then((r) => setAvailFields(r.columns || [])).catch(() => setAvailFields([]));
    setColumns([]); setGroupBy(''); setFilters([]); setResult({ columns: [], rows: [] });
  }, [source]);

  const buildDef = () => ({
    source, columns, filters: filters.filter((f) => f.field),
    group_by: groupBy, aggregate: groupBy ? (aggregate === 'sum' ? `sum:${sumField}` : 'count') : '',
  });
  const preview = () => reportsApi.preview(buildDef()).then(setResult).catch(() => setResult({ columns: [], rows: [] }));
  const save = async () => { if (!reportName) return alert('أدخل اسم التقرير'); await reportsApi.create({ ...buildDef(), name: reportName }); setReportName(''); loadSaved(); };
  const runSaved = async (r: any) => { setSource(r.source); const res = await reportsApi.run(r.id); setResult(res); };
  const delSaved = async (id: number) => { if (confirm('حذف التقرير؟')) { await reportsApi.remove(id); loadSaved(); } };

  const toggleCol = (f: string) => setColumns((c) => c.includes(f) ? c.filter((x) => x !== f) : [...c, f]);
  const addFilter = () => setFilters((f) => [...f, { field: availFields[0] || '', op: 'eq', value: '' }]);
  const setFilter = (i: number, k: string, v: any) => setFilters((f) => f.map((x, j) => j === i ? { ...x, [k]: v } : x));

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="منشئ التقارير" subtitle="Report Builder — تقارير مخصّصة من بيانات أي وحدة"
        commands={[
          { id: 'preview', label: 'تشغيل', icon: <Play size={16} />, variant: 'primary', onClick: preview },
          { id: 'export', label: 'تصدير CSV', icon: <Download size={16} />, variant: 'secondary', onClick: () => exportToCsv(result.rows, `${source}_report.csv`) },
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: loadSaved },
        ]} />
      <div className="p-6 grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="space-y-4">
          <FluentCard>
            <FluentFormField label="مصدر البيانات">
              <FluentSelect value={source} onChange={(e) => setSource(e.target.value)}>
                {SOURCES.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
              </FluentSelect>
            </FluentFormField>
            <div className="mt-3">
              <div className="text-xs font-semibold text-[#605e5c] mb-1">الأعمدة</div>
              <div className="max-h-40 overflow-auto space-y-1 border border-[#e1dfdd] rounded p-2">
                {availFields.map((f) => (
                  <label key={f} className="flex items-center gap-2 text-xs text-[#323130]">
                    <input type="checkbox" checked={columns.includes(f)} onChange={() => toggleCol(f)} className="accent-[#0078d4]" /> {f}
                  </label>
                ))}
                {!availFields.length && <div className="text-xs text-[#a19f9d]">لا حقول</div>}
              </div>
            </div>
          </FluentCard>
          <FluentCard>
            <div className="text-xs font-semibold text-[#605e5c] mb-2">تجميع (اختياري)</div>
            <FluentSelect value={groupBy} onChange={(e) => setGroupBy(e.target.value)}>
              <option value="">بدون تجميع</option>
              {availFields.map((f) => <option key={f} value={f}>{f}</option>)}
            </FluentSelect>
            {groupBy && (
              <div className="mt-2 space-y-2">
                <FluentSelect value={aggregate} onChange={(e) => setAggregate(e.target.value)}>
                  <option value="count">عدد</option><option value="sum">مجموع حقل</option>
                </FluentSelect>
                {aggregate === 'sum' && (
                  <FluentSelect value={sumField} onChange={(e) => setSumField(e.target.value)}>
                    <option value="">اختر حقلاً</option>
                    {availFields.map((f) => <option key={f} value={f}>{f}</option>)}
                  </FluentSelect>
                )}
              </div>
            )}
          </FluentCard>
          <FluentCard>
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs font-semibold text-[#605e5c]">عوامل التصفية</div>
              <button onClick={addFilter} className="text-[#0078d4]"><Plus size={14} /></button>
            </div>
            {filters.map((f, i) => (
              <div key={i} className="flex gap-1 mb-1">
                <select value={f.field} onChange={(e) => setFilter(i, 'field', e.target.value)} className="text-xs border rounded p-1 flex-1">
                  {availFields.map((x) => <option key={x} value={x}>{x}</option>)}
                </select>
                <select value={f.op} onChange={(e) => setFilter(i, 'op', e.target.value)} className="text-xs border rounded p-1 w-14">
                  {OPS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                </select>
                <input value={f.value} onChange={(e) => setFilter(i, 'value', e.target.value)} className="text-xs border rounded p-1 w-16" />
              </div>
            ))}
          </FluentCard>
          <FluentCard>
            <FluentFormField label="حفظ باسم"><FluentInput value={reportName} onChange={(e) => setReportName(e.target.value)} placeholder="تقرير المخزون" /></FluentFormField>
            <button onClick={save} className="mt-2 w-full flex items-center justify-center gap-1 text-sm text-white bg-[#0078d4] py-1.5 rounded hover:bg-[#106ebe]"><Save size={14} /> حفظ</button>
            <div className="mt-3 space-y-1">
              {saved.map((r) => (
                <div key={r.id} className="flex items-center justify-between text-xs bg-[#f3f2f1] rounded px-2 py-1">
                  <button onClick={() => runSaved(r)} className="text-[#0078d4] hover:underline truncate">{r.name}</button>
                  <button onClick={() => delSaved(r.id)} className="text-[#a4262c]"><Trash2 size={12} /></button>
                </div>
              ))}
            </div>
          </FluentCard>
        </div>

        <div className="lg:col-span-3">
          <FluentTable
            title="نتيجة التقرير"
            subtitle={`${result.rows.length} صف`}
            columns={(result.columns || []).map((c: string) => ({ key: c, label: c, render: (v: any) => v == null ? '—' : String(v) }))}
            data={result.rows}
            emptyMessage="اضغط «تشغيل» لعرض النتيجة"
          />
        </div>
      </div>
    </div>
  );
}
