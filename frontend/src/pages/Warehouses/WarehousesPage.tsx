// pages/Warehouses/WarehousesPage.tsx
import { Warehouse } from 'lucide-react';
import { ModuleCrudPage } from '../../components/ModuleCrudPage';
import { MODULE_FIELDS } from '../../config/moduleFields';

export default function WarehousesPage() {
  return (
    <ModuleCrudPage
      module="warehouses"
      fields={MODULE_FIELDS.warehouses}
      title="المستودعات"
      subtitle="Warehouses"
      newLabel="إضافة مستودع"
      icon={<Warehouse size={20} />}
    />
  );
}
