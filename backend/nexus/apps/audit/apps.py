from django.apps import AppConfig

# Models tracked with full CDHDR/CDPOS-style change logging. This spans the
# primary transactional and master-data records across every module - the
# same universal coverage philosophy as SAP change documents (CDHDR/CDPOS),
# applied to every master-data and business-document model in the system.
# Unknown paths are skipped (see _register_models) so this list stays safe to
# extend even for apps/models that don't exist in every deployment.
AUDITED_MODEL_PATHS = [
    # core - master data (BRN/WHS)
    'core.Company', 'core.Branch', 'core.Warehouse', 'core.SubWarehouse', 'core.Department',
    # hr - employee master data and payroll documents
    'hr.Employee', 'hr.LeaveRequest', 'hr.SalaryStructure', 'hr.PayrollRun', 'hr.Payslip',
    # accounting - GL/AP/AR documents
    'accounting.ChartOfAccounts', 'accounting.JournalEntry', 'accounting.Invoice', 'accounting.Payment',
    # industry - product/inventory master data and procurement documents
    'industry.Product', 'industry.Inventory', 'industry.Supplier', 'industry.PurchaseOrder',
    # crm - customer master data and pipeline
    'crm.Customer', 'crm.Opportunity',
    # sales - sales documents
    'sales.SalesOrder', 'sales.Invoice', 'sales.Quotation',
    # pmo - project master data
    'pmo.Project', 'pmo.Milestone',
    # manufacturing - production master data and orders
    'manufacturing.WorkCenter', 'manufacturing.BOM', 'manufacturing.ManufacturingOrder', 'manufacturing.MaterialRequisition',
    # permissions - authorization master data (SAP PFCG-style role changes)
    'permissions.Role', 'permissions.UserRole',
    # workflow - approval engine
    'workflow.Workflow', 'workflow.ApprovalRequest',
    # ecommerce - orders
    'ecommerce.Customer', 'ecommerce.Order',
    # regulatory - compliance master data
    'regulatory.Regulation',
    # api_infra - tenant master data
    'api_infra.Tenant',
]


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nexus.apps.audit'
    label = 'audit'

    def ready(self):
        from . import signals

        signals.connect_signals()
        self._register_models()

    def _register_models(self):
        from django.apps import apps as django_apps

        from . import signals

        for path in AUDITED_MODEL_PATHS:
            app_label, model_name = path.split('.')
            try:
                model = django_apps.get_model(app_label, model_name)
            except LookupError:
                continue
            signals.register_audited_model(model)
