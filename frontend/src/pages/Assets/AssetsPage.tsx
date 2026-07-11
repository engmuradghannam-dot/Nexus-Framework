// pages/Assets/AssetsPage.tsx
import { Briefcase } from 'lucide-react';
import { ModuleCrudPage } from '../../components/ModuleCrudPage';
import { MODULE_FIELDS } from '../../config/moduleFields';

export default function AssetsPage() {
  return (
    <ModuleCrudPage
      module="assets"
      fields={MODULE_FIELDS.assets}
      title="الأصول"
      subtitle="Assets"
      newLabel="إضافة أصل"
      icon={<Briefcase size={20} />}
    />
  );
}
