// pages/Roles/RolesPage.tsx
import { useEffect, useState } from 'react';
import { Shield, Save, CheckCircle2, Users } from 'lucide-react';
import { FluentCommandBar } from '../../components/FluentUI/FluentCommandBar';
import { FluentCard } from '../../components/FluentUI/FluentCard';
import { rbacApi } from '../../services/api';

const ACTION_LABELS: Record<string, string> = { view: 'عرض', create: 'إضافة', edit: 'تعديل', delete: 'حذف' };

export default function RolesPage() {
  const [roles, setRoles] = useState<any[]>([]);
  const [catalog, setCatalog] = useState<{ modules: any[]; actions: string[] }>({ modules: [], actions: [] });
  const [selected, setSelected] = useState<any>(null);
  const [perms, setPerms] = useState<Record<string, string[]>>({});
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    rbacApi.roles().then((r) => { setRoles(r); if (r[0]) pick(r[0]); }).catch(() => {});
    rbacApi.catalog().then(setCatalog).catch(() => {});
  }, []);

  const pick = (role: any) => { setSelected(role); setPerms(JSON.parse(JSON.stringify(role.permissions || {}))); setSaved(false); };

  const toggle = (mod: string, act: string) => {
    setPerms((p) => {
      const cur = new Set(p[mod] || []);
      cur.has(act) ? cur.delete(act) : cur.add(act);
      return { ...p, [mod]: Array.from(cur) };
    });
  };

  const save = async () => {
    if (!selected) return;
    try {
      await rbacApi.updateRole(selected.id, perms);
      setSaved(true);
      setRoles((rs) => rs.map((r) => (r.id === selected.id ? { ...r, permissions: perms } : r)));
      setTimeout(() => setSaved(false), 3000);
    } catch { alert('تعذّر الحفظ'); }
  };

  const has = (mod: string, act: string) => (perms[mod] || []).includes(act);

  return (
    <div className="min-h-full" dir="rtl">
      <FluentCommandBar title="الأدوار والصلاحيات" subtitle="RBAC — صلاحيات دقيقة لكل وحدة"
        commands={[{ id: 'save', label: 'حفظ الصلاحيات', icon: <Save size={16} />, variant: 'primary', onClick: save }]} />
      <div className="p-6">
        {saved && <div className="mb-4 flex items-center gap-2 rounded-md border border-[#107c10]/30 bg-[#f3faf3] px-4 py-2 text-sm text-[#107c10]"><CheckCircle2 size={16} /> تم حفظ صلاحيات الدور</div>}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Roles list */}
          <FluentCard>
            <h3 className="text-sm font-semibold text-[#605e5c] mb-3">الأدوار ({roles.length})</h3>
            <div className="space-y-1">
              {roles.map((r) => (
                <button key={r.id} onClick={() => pick(r)}
                  className={`w-full text-right px-3 py-2 rounded-md text-sm flex items-center justify-between ${selected?.id === r.id ? 'bg-[#eff6fc] text-[#0078d4] font-medium' : 'text-[#323130] hover:bg-[#f3f2f1]'}`}>
                  <span className="flex items-center gap-2"><Shield size={15} /> {r.name_ar || r.name}</span>
                  <span className="text-xs text-[#605e5c] flex items-center gap-1"><Users size={12} />{r.assigned_count || 0}</span>
                </button>
              ))}
            </div>
          </FluentCard>

          {/* Permission matrix */}
          <div className="lg:col-span-3">
            <FluentCard>
              {selected ? (
                <>
                  <div className="mb-4">
                    <h3 className="text-base font-semibold text-[#323130]">{selected.name_ar || selected.name}</h3>
                    <p className="text-sm text-[#605e5c]">{selected.description}</p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-[#e1dfdd] text-[#605e5c]">
                          <th className="text-right py-2 px-2 font-medium">الوحدة</th>
                          {catalog.actions.map((a) => <th key={a} className="text-center py-2 px-2 font-medium">{ACTION_LABELS[a] || a}</th>)}
                        </tr>
                      </thead>
                      <tbody>
                        {catalog.modules.map((m) => (
                          <tr key={m.key} className="border-b border-[#f3f2f1] hover:bg-[#faf9f8]">
                            <td className="py-2 px-2 text-[#323130]">{m.label}</td>
                            {catalog.actions.map((a) => (
                              <td key={a} className="text-center py-2 px-2">
                                <input type="checkbox" checked={has(m.key, a)} onChange={() => toggle(m.key, a)} className="h-4 w-4 accent-[#0078d4] cursor-pointer" />
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : <p className="text-[#605e5c]">اختر دوراً لعرض صلاحياته</p>}
            </FluentCard>
          </div>
        </div>
      </div>
    </div>
  );
}
