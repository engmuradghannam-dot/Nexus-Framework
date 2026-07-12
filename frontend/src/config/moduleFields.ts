// config/moduleFields.ts
// Field/input definitions per module, derived from Nexus_ERP_Template.xlsx.
// Bilingual name fields (Arabic/English) are included where the template has them.

export type FieldType = 'text' | 'number' | 'date' | 'select' | 'checkbox' | 'textarea';
export interface FieldDef {
  key: string;
  label: string;
  type?: FieldType;
  options?: string[];
  full?: boolean;
}

const STATUS = ['Active', 'Inactive', 'Draft', 'Pending', 'Approved', 'Closed'];
const CURRENCY = ['SAR', 'AED', 'QAR', 'USD', 'EUR'];
const COUNTRY = ['Saudi Arabia', 'UAE', 'Qatar', 'Kuwait', 'Bahrain', 'Oman', 'Egypt', 'USA'];
const PRIORITY = ['High', 'Medium', 'Low'];
const RISK = ['Low', 'Medium', 'High'];

export const MODULE_FIELDS: Record<string, FieldDef[]> = {
  suppliers: [
    { key: 'supplier_code', label: 'رمز المورّد' },
    { key: 'supplier_name', label: 'اسم المورّد (إنجليزي)' },
    { key: 'arabic_name', label: 'الاسم بالعربي' },
    { key: 'cr_number', label: 'رقم السجل التجاري' },
    { key: 'vat_number', label: 'الرقم الضريبي' },
    { key: 'country', label: 'الدولة', type: 'select', options: COUNTRY },
    { key: 'city', label: 'المدينة' },
    { key: 'address', label: 'العنوان', full: true },
    { key: 'phone', label: 'الهاتف' },
    { key: 'email', label: 'البريد الإلكتروني' },
    { key: 'currency', label: 'العملة', type: 'select', options: CURRENCY },
    { key: 'payment_terms', label: 'شروط الدفع' },
    { key: 'credit_limit', label: 'حد الائتمان', type: 'number' },
    { key: 'bank', label: 'البنك' },
    { key: 'iban', label: 'الآيبان' },
    { key: 'category', label: 'الفئة' },
    { key: 'status', label: 'الحالة', type: 'select', options: STATUS },
    { key: 'risk_level', label: 'مستوى المخاطر', type: 'select', options: RISK },
    { key: 'preferred', label: 'مورّد مفضّل', type: 'checkbox' },
    { key: 'notes', label: 'ملاحظات', type: 'textarea', full: true },
  ],
  purchase_requisition: [
    { key: 'pr_no', label: 'رقم الطلب' },
    { key: 'date', label: 'التاريخ', type: 'date' },
    { key: 'department', label: 'القسم' },
    { key: 'requester', label: 'مقدّم الطلب' },
    { key: 'cost_center', label: 'مركز التكلفة' },
    { key: 'project', label: 'المشروع' },
    { key: 'priority', label: 'الأولوية', type: 'select', options: PRIORITY },
    { key: 'required_date', label: 'التاريخ المطلوب', type: 'date' },
    { key: 'status', label: 'الحالة', type: 'select', options: STATUS },
    { key: 'remarks', label: 'ملاحظات', type: 'textarea', full: true },
  ],
  purchase_order: [
    { key: 'po_no', label: 'رقم أمر الشراء' },
    { key: 'supplier', label: 'المورّد' },
    { key: 'pr_no', label: 'رقم الطلب' },
    { key: 'currency', label: 'العملة', type: 'select', options: CURRENCY },
    { key: 'payment_terms', label: 'شروط الدفع' },
    { key: 'delivery_date', label: 'تاريخ التسليم', type: 'date' },
    { key: 'buyer', label: 'المشتري' },
    { key: 'status', label: 'الحالة', type: 'select', options: STATUS },
    { key: 'total', label: 'الإجمالي', type: 'number' },
  ],
  inventory: [
    { key: 'item_code', label: 'رمز الصنف' },
    { key: 'sku', label: 'SKU' },
    { key: 'arabic_name', label: 'الاسم بالعربي' },
    { key: 'english_name', label: 'الاسم بالإنجليزي' },
    { key: 'category', label: 'الفئة' },
    { key: 'unit', label: 'الوحدة' },
    { key: 'cost', label: 'التكلفة', type: 'number' },
    { key: 'selling_price', label: 'سعر البيع', type: 'number' },
    { key: 'min_stock', label: 'الحد الأدنى', type: 'number' },
    { key: 'max_stock', label: 'الحد الأقصى', type: 'number' },
    { key: 'current_stock', label: 'المخزون الحالي', type: 'number' },
    { key: 'reorder_level', label: 'حد إعادة الطلب', type: 'number' },
    { key: 'warehouse', label: 'المستودع' },
  ],
  warehouses: [
    { key: 'warehouse_code', label: 'رمز المستودع' },
    { key: 'warehouse_name', label: 'اسم المستودع' },
    { key: 'branch', label: 'الفرع' },
    { key: 'manager', label: 'المدير' },
    { key: 'location', label: 'الموقع' },
    { key: 'capacity', label: 'السعة', type: 'number' },
    { key: 'status', label: 'الحالة', type: 'select', options: STATUS },
  ],
  crm: [
    { key: 'customer_code', label: 'رمز العميل' },
    { key: 'customer_name', label: 'اسم العميل' },
    { key: 'type', label: 'النوع', type: 'select', options: ['Company', 'Individual', 'Government'] },
    { key: 'phone', label: 'الهاتف' },
    { key: 'email', label: 'البريد الإلكتروني' },
    { key: 'city', label: 'المدينة' },
    { key: 'country', label: 'الدولة', type: 'select', options: COUNTRY },
    { key: 'salesperson', label: 'مندوب المبيعات' },
    { key: 'credit_limit', label: 'حد الائتمان', type: 'number' },
    { key: 'status', label: 'الحالة', type: 'select', options: STATUS },
  ],
  selling: [
    { key: 'so_no', label: 'رقم أمر البيع' },
    { key: 'customer', label: 'العميل' },
    { key: 'date', label: 'التاريخ', type: 'date' },
    { key: 'currency', label: 'العملة', type: 'select', options: CURRENCY },
    { key: 'warehouse', label: 'المستودع' },
    { key: 'salesperson', label: 'مندوب المبيعات' },
    { key: 'status', label: 'الحالة', type: 'select', options: STATUS },
    { key: 'total', label: 'الإجمالي', type: 'number' },
  ],
  hr: [
    { key: 'employee_no', label: 'الرقم الوظيفي' },
    { key: 'name', label: 'الاسم' },
    { key: 'department', label: 'القسم' },
    { key: 'position', label: 'المنصب' },
    { key: 'hire_date', label: 'تاريخ التعيين', type: 'date' },
    { key: 'nationality', label: 'الجنسية' },
    { key: 'manager', label: 'المدير' },
    { key: 'status', label: 'الحالة', type: 'select', options: STATUS },
  ],
  assets: [
    { key: 'asset_code', label: 'رمز الأصل' },
    { key: 'asset_name', label: 'اسم الأصل' },
    { key: 'category', label: 'الفئة' },
    { key: 'purchase_date', label: 'تاريخ الشراء', type: 'date' },
    { key: 'cost', label: 'التكلفة', type: 'number' },
    { key: 'location', label: 'الموقع' },
    { key: 'custodian', label: 'العهدة' },
    { key: 'status', label: 'الحالة', type: 'select', options: STATUS },
  ],
};
