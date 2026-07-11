// pages/Selling/SellingPage.tsx
import { ShoppingCart } from 'lucide-react';
import { ModuleCrudPage } from '../../components/ModuleCrudPage';
import { MODULE_FIELDS } from '../../config/moduleFields';

export default function SellingPage() {
  return (
    <ModuleCrudPage
      module="selling"
      fields={MODULE_FIELDS.selling}
      title="المبيعات"
      subtitle="Sales Orders"
      newLabel="أمر بيع"
      icon={<ShoppingCart size={20} />}
    />
  );
}
