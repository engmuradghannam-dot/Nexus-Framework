// pages/Inventory/InventoryPage.tsx
import { useEffect, useMemo, useState } from 'react';
import { Boxes, Plus, RefreshCw, AlertTriangle, ArrowDownToLine, ArrowUpFromLine, CheckCircle } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentTable } from '../../components/FluentUI/FluentTable';
import { FluentStatsCard } from '../../components/FluentUI/FluentStatsCard';
import { FluentBadge } from '../../components/FluentUI/FluentBadge';
import { FluentPanel } from '../../components/FluentUI/FluentPanel';
import { FluentFormField, FluentInput, FluentSelect } from '../../components/FluentUI';
import { itemsApi, itemGroupsApi, stockEntriesApi, getWarehouses } from '../../services/api';

const fmt = (n: any) => Number(n || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function InventoryPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [groups, setGroups] = useState<any[]>([]);
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const [itemPanel, setItemPanel] = useState(false);
  const [newItem, setNewItem] = useState<any>({});

  const [movePanel, setMovePanel] = useState(false);
  const [activeItem, setActiveItem] = useState<any>(null);
  const [move, setMove] = useState<any>({ entry_type: 'Receipt', warehouse: '', quantity: 1, rate: 0 });

  const reload = () => {
    setLoading(true);
    itemsApi.list().then(setItems).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(() => {
    reload();
    itemGroupsApi.list().then(setGroups).catch(() => {});
    getWarehouses().then((r: any) => setWarehouses(r.data?.results || r.data || [])).catch(() => {});
  }, []);

  const stats = useMemo(() => ({
    total: items.length,
    lowStock: items.filter((i) => Number(i.stock_quantity) <= Number(i.reorder_level || 0) && Number(i.reorder_level) > 0).length,
    value: items.reduce((s, i) => s + Number(i.stock_quantity || 0) * Number(i.standard_rate || 0), 0),
  }), [items]);

  const openNewItem = () => {
    setNewItem({ item_code: '', item_name: '', item_type: 'Stock', standard_rate: 0, reorder_level: 0, uom: 'Unit' });
    setError('');
    setItemPanel(true);
  };

  const saveItem = async () => {
    try {
      await itemsApi.create(newItem);
      setItemPanel(false);
      reload();
    } catch (e: any) {
      setError(formatApiError(e));
    }
  };

  const openMove = (row: any) => {
    setActiveItem(row);
    setMove({ entry_type: 'Receipt', warehouse: '', quantity: 1, rate: row.standard_rate || 0 });
    setError(''); setNotice('');
    setMovePanel(true);
  };

  const saveMove = async () => {
    try {
      await stockEntriesApi.create({ item: activeItem.id, warehouse: move.warehouse, entry_type: move.entry_type, quantity: move.quantity, rate: move.rate });
      setNotice(move.entry_type === 'Receipt' ? 'تم تسجيل استلام المخزون.' : 'تم تسجيل صرف المخزون.');
      reload();
      setMovePanel(false);
    } catch (e: any) {
      setError(formatApiError(e));
    }
  };

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar
        title="المخزون" subtitle="Inventory — الأصناف والحركات المخزنية"
        commands={[
          { id: 'refresh', label: 'تحديث', icon: <RefreshCw size={16} />, variant: 'secondary', onClick: reload },
          { id: 'new', label: 'صنف جديد', icon: <Plus size={16} />, variant: 'primary', onClick: openNewItem },
        ]}
      />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-3 gap-4">
          <FluentStatsCard title="عدد الأصناف" value={stats.total} icon={<Boxes size={20} />} color="blue" />
          <FluentStatsCard title="تحت حد إعادة الطلب" value={stats.lowStock} icon={<AlertTriangle size={20} />} color="orange" />
          <FluentStatsCard title="قيمة المخزون التقديرية" value={fmt(stats.value)} icon={<Boxes size={20} />} color="purple" />
        </div>

        {notice && <div className="flex items-center gap-2 rounded-md border border-[#107c10]/30 bg-[#f3faf3] px-3 py-2 text-sm text-[#107c10]"><CheckCircle size={16} /> {notice}</div>}

        <FluentTable
          title="الأصناف"
          subtitle={loading ? 'جارٍ التحميل…' : `${items.length} صنف`}
          columns={[
            { key: 'item_code', label: 'الرمز', sortable: true },
            { key: 'item_name', label: 'اسم الصنف', sortable: true },
            { key: 'item_group_name', label: 'المجموعة' },
            { key: 'stock_quantity', label: 'الكمية بالمخزون', render: (v: any, row: any) => {
                const low = Number(row.reorder_level) > 0 && Number(v) <= Number(row.reorder_level);
                return <span className={low ? 'text-[#a4262c] font-semibold' : ''}>{fmt(v)}</span>;
              } },
            { key: 'reorder_level', label: 'حد إعادة الطلب', render: (v: any) => fmt(v) },
            { key: 'standard_rate', label: 'السعر القياسي', render: (v: any) => fmt(v) },
            {
              key: '__move', label: '', render: (_: any, row: any) => (
                <button onClick={(e) => { e.stopPropagation(); openMove(row); }} className="flex items-center gap-1 text-xs text-[#0078d4] border border-[#0078d4] px-2 py-1 rounded hover:bg-[#eff6fc]">
                  <ArrowDownToLine size={12} /> حركة مخزنية
                </button>
              ),
            },
          ]}
          data={items}
        />
      </div>

      <FluentPanel isOpen={itemPanel} onClose={() => setItemPanel(false)} title="صنف جديد"
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setItemPanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={saveItem} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">حفظ</button>
        </div>}>
        {error && <div className="mb-4 flex items-start gap-2 rounded-md border border-[#a4262c]/30 bg-[#fdf2f2] px-3 py-2 text-sm text-[#a4262c]"><AlertTriangle size={16} className="mt-0.5 shrink-0" /> {error}</div>}
        <div className="space-y-3">
          <FluentFormField label="رمز الصنف" required><FluentInput value={newItem.item_code || ''} onChange={(e) => setNewItem({ ...newItem, item_code: e.target.value })} placeholder="SKU-001" /></FluentFormField>
          <FluentFormField label="اسم الصنف" required><FluentInput value={newItem.item_name || ''} onChange={(e) => setNewItem({ ...newItem, item_name: e.target.value })} /></FluentFormField>
          <FluentFormField label="المجموعة">
            <FluentSelect value={newItem.item_group || ''} onChange={(e) => setNewItem({ ...newItem, item_group: e.target.value })}>
              <option value="">— بلا —</option>
              {groups.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
            </FluentSelect>
          </FluentFormField>
          <FluentFormField label="وحدة القياس"><FluentInput value={newItem.uom || 'Unit'} onChange={(e) => setNewItem({ ...newItem, uom: e.target.value })} /></FluentFormField>
          <FluentFormField label="السعر القياسي"><FluentInput type="number" step="0.01" value={newItem.standard_rate || 0} onChange={(e) => setNewItem({ ...newItem, standard_rate: e.target.value })} /></FluentFormField>
          <FluentFormField label="حد إعادة الطلب" hint="تنبيه عندما تصل الكمية لهذا الحد"><FluentInput type="number" step="0.01" value={newItem.reorder_level || 0} onChange={(e) => setNewItem({ ...newItem, reorder_level: e.target.value })} /></FluentFormField>
        </div>
      </FluentPanel>

      <FluentPanel isOpen={movePanel} onClose={() => setMovePanel(false)} title={`حركة مخزنية — ${activeItem?.item_name || ''}`}
        subtitle={`الكمية الحالية: ${fmt(activeItem?.stock_quantity)}`}
        footer={<div className="flex gap-2 justify-end">
          <button onClick={() => setMovePanel(false)} className="px-4 py-2 text-sm text-[#323130] border border-[#8a8886] rounded-sm hover:bg-[#f3f2f1]">إلغاء</button>
          <button onClick={saveMove} className="px-4 py-2 text-sm text-white bg-[#0078d4] rounded-sm hover:bg-[#106ebe]">تنفيذ</button>
        </div>}>
        {error && <div className="mb-4 flex items-start gap-2 rounded-md border border-[#a4262c]/30 bg-[#fdf2f2] px-3 py-2 text-sm text-[#a4262c]"><AlertTriangle size={16} className="mt-0.5 shrink-0" /> {error}</div>}
        <div className="space-y-3">
          <FluentFormField label="نوع الحركة">
            <div className="flex gap-2">
              <button onClick={() => setMove({ ...move, entry_type: 'Receipt' })} className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm rounded-sm border ${move.entry_type === 'Receipt' ? 'bg-[#0078d4] text-white border-[#0078d4]' : 'border-[#8a8886] text-[#323130]'}`}><ArrowDownToLine size={14} /> استلام</button>
              <button onClick={() => setMove({ ...move, entry_type: 'Issue' })} className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm rounded-sm border ${move.entry_type === 'Issue' ? 'bg-[#0078d4] text-white border-[#0078d4]' : 'border-[#8a8886] text-[#323130]'}`}><ArrowUpFromLine size={14} /> صرف</button>
            </div>
          </FluentFormField>
          <FluentFormField label="المستودع" required>
            <FluentSelect value={move.warehouse} onChange={(e) => setMove({ ...move, warehouse: e.target.value })}>
              <option value="">— اختر مستودعاً —</option>
              {warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
            </FluentSelect>
          </FluentFormField>
          <FluentFormField label="الكمية"><FluentInput type="number" step="0.01" value={move.quantity} onChange={(e) => setMove({ ...move, quantity: e.target.value })} /></FluentFormField>
          <FluentFormField label="سعر الوحدة"><FluentInput type="number" step="0.01" value={move.rate} onChange={(e) => setMove({ ...move, rate: e.target.value })} /></FluentFormField>
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
