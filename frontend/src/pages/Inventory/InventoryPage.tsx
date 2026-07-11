// pages/Inventory/InventoryPage.tsx
import { Boxes } from 'lucide-react';
import { ModuleCrudPage } from '../../components/ModuleCrudPage';
import { MODULE_FIELDS } from '../../config/moduleFields';

export default function InventoryPage() {
  return (
    <ModuleCrudPage
      module="inventory"
      fields={MODULE_FIELDS.inventory}
      title="المخزون"
      subtitle="Inventory Items"
      newLabel="إضافة صنف"
      icon={<Boxes size={20} />}
    />
  );
}
