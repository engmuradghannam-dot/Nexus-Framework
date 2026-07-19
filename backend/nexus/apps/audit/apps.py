from django.apps import AppConfig

# Models tracked with full CDHDR/CDPOS-style change logging. This spans the
# primary transactional and master-data records across every module.
# Unknown paths are skipped (see _register_models) so this list stays safe to
# extend even for apps/models that don't exist in every deployment.
AUDITED_MODEL_PATHS = [
    'accounting.JournalEntry', 'accounting.ChartOfAccounts',
    'hr.Employee', 'hr.LeaveRequest',
    'industry.Product', 'industry.Inventory', 'industry.Supplier', 'industry.PurchaseOrder',
    'crm.Customer', 'crm.Opportunity',
    'sales.SalesOrder', 'sales.Invoice',
    'pmo.Project',
    'manufacturing.WorkCenter', 'manufacturing.BOM',
    'core.Branch', 'core.Warehouse',
    'workflow.ApprovalRequest',
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
