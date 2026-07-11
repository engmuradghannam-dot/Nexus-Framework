import { useCallback, useEffect, useState } from 'react';
import { recordsApi } from '../services/api';

// Flattens {id, data:{...}} -> {id, ...data} for easy table/form use.
export function useModuleRecords(module: string) {
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await recordsApi.list(module);
      setRecords(rows.map((r: any) => ({ id: r.id, ...(r.data || {}) })));
    } catch {
      setRecords([]);
    } finally {
      setLoading(false);
    }
  }, [module]);

  useEffect(() => { reload(); }, [reload]);

  const save = async (row: any) => {
    const { id, ...payload } = row || {};
    if (id) await recordsApi.update(id, module, payload);
    else await recordsApi.create(module, payload);
    await reload();
  };

  const remove = async (id: number) => {
    await recordsApi.remove(id);
    await reload();
  };

  return { records, loading, reload, save, remove };
}
