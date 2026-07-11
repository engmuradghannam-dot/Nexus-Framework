// pages/Buying/BuyingPage.tsx
import { Store } from 'lucide-react';
import { ModuleCrudPage } from '../../components/ModuleCrudPage';
import { MODULE_FIELDS } from '../../config/moduleFields';

export default function BuyingPage() {
  return (
    <ModuleCrudPage
      module="buying"
      fields={MODULE_FIELDS.purchase_order}
      title="المشتريات"
      subtitle="Purchase Orders"
      newLabel="أمر شراء"
      icon={<Store size={20} />}
    />
  );
}
