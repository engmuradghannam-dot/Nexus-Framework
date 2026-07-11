// components/ModuleForm.tsx
import { FluentFormField, FluentInput, FluentSelect, FluentTextArea } from './FluentUI';
import type { FieldDef } from '../config/moduleFields';

interface Props {
  fields: FieldDef[];
  value?: Record<string, any>;
  onChange?: (v: Record<string, any>) => void;
}

export function ModuleForm({ fields, value = {}, onChange }: Props) {
  const set = (k: string, v: any) => onChange?.({ ...value, [k]: v });

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {fields.map((f) => (
        <div key={f.key} className={f.full ? 'md:col-span-2' : ''}>
          <FluentFormField label={f.label}>
            {f.type === 'select' ? (
              <FluentSelect value={value[f.key] ?? ''} onChange={(e) => set(f.key, e.target.value)}>
                <option value="">—</option>
                {(f.options || []).map((o) => (
                  <option key={o} value={o}>{o}</option>
                ))}
              </FluentSelect>
            ) : f.type === 'textarea' ? (
              <FluentTextArea value={value[f.key] ?? ''} onChange={(e) => set(f.key, e.target.value)} rows={2} />
            ) : f.type === 'checkbox' ? (
              <label className="flex items-center gap-2 h-9">
                <input
                  type="checkbox"
                  checked={!!value[f.key]}
                  onChange={(e) => set(f.key, e.target.checked)}
                  className="h-4 w-4 accent-[#0078d4]"
                />
                <span className="text-sm text-[#605e5c]">نعم</span>
              </label>
            ) : (
              <FluentInput
                type={f.type === 'number' ? 'number' : f.type === 'date' ? 'date' : 'text'}
                value={value[f.key] ?? ''}
                onChange={(e) => set(f.key, e.target.value)}
              />
            )}
          </FluentFormField>
        </div>
      ))}
    </div>
  );
}

export default ModuleForm;
