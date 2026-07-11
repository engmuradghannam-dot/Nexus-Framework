// pages/CRM/CRMPage.tsx
import { HeartHandshake } from 'lucide-react';
import { ModuleCrudPage } from '../../components/ModuleCrudPage';
import { MODULE_FIELDS } from '../../config/moduleFields';

export default function CRMPage() {
  return (
    <ModuleCrudPage
      module="crm"
      fields={MODULE_FIELDS.crm}
      title="إدارة العملاء"
      subtitle="CRM Customers"
      newLabel="إضافة عميل"
      icon={<HeartHandshake size={20} />}
    />
  );
}
