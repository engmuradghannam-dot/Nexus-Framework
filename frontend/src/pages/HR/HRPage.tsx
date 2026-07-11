// pages/HR/HRPage.tsx
import { Users } from 'lucide-react';
import { ModuleCrudPage } from '../../components/ModuleCrudPage';
import { MODULE_FIELDS } from '../../config/moduleFields';

export default function HRPage() {
  return (
    <ModuleCrudPage
      module="hr"
      fields={MODULE_FIELDS.hr}
      title="الموارد البشرية"
      subtitle="HR Employees"
      newLabel="إضافة موظف"
      icon={<Users size={20} />}
    />
  );
}
