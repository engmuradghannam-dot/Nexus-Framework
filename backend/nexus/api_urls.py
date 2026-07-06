from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.core.views import UserViewSet, CompanyViewSet, BranchViewSet, WarehouseViewSet, PrintTemplateViewSet, ModuleViewSet, AuditLogViewSet
from apps.accounts.views import AccountViewSet, JournalEntryViewSet, CostCenterViewSet, BudgetViewSet
from apps.inventory.views import (
    ItemViewSet, ItemGroupViewSet, StockEntryViewSet,
    ItemSerialNumberViewSet, ItemBatchViewSet,
    StockReconciliationViewSet, StockReconciliationItemViewSet,
)
from apps.buying.views import (
    SupplierViewSet, PurchaseOrderViewSet, PurchaseOrderItemViewSet,
    PurchaseTaxChargeViewSet, PurchasePaymentViewSet,
)
from apps.selling.views import (
    CustomerViewSet, SalesOrderViewSet, SalesOrderItemViewSet,
    SalesTaxChargeViewSet, SalesPaymentViewSet,
)
from apps.manufacturing.views import (
    BOMViewSet, WorkOrderViewSet, JobCardViewSet,
)
from apps.hr.views import (
    EmployeeViewSet, DepartmentViewSet, LeaveRequestViewSet,
    AttendanceViewSet, PayrollEntryViewSet,
)
from apps.crm.views import LeadViewSet, OpportunityViewSet
from apps.projects.views import ProjectViewSet, TaskViewSet
from apps.assets.views import AssetCategoryViewSet, AssetViewSet
from apps.workflow.views import WorkflowViewSet, WorkflowInstanceViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'print-templates', PrintTemplateViewSet, basename='print-template')
router.register(r'modules', ModuleViewSet, basename='module')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'journal-entries', JournalEntryViewSet, basename='journal-entry')
router.register(r'cost-centers', CostCenterViewSet, basename='cost-center')
router.register(r'budgets', BudgetViewSet, basename='budget')

router.register(r'items', ItemViewSet, basename='item')
router.register(r'item-groups', ItemGroupViewSet, basename='item-group')
router.register(r'stock-entries', StockEntryViewSet, basename='stock-entry')
router.register(r'serial-numbers', ItemSerialNumberViewSet, basename='serial-number')
router.register(r'batches', ItemBatchViewSet, basename='batch')
router.register(r'stock-reconciliations', StockReconciliationViewSet, basename='stock-reconciliation')

router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'purchase-order-items', PurchaseOrderItemViewSet, basename='purchase-order-item')
router.register(r'purchase-tax-charges', PurchaseTaxChargeViewSet, basename='purchase-tax-charge')
router.register(r'purchase-payments', PurchasePaymentViewSet, basename='purchase-payment')

router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'sales-orders', SalesOrderViewSet, basename='sales-order')
router.register(r'sales-order-items', SalesOrderItemViewSet, basename='sales-order-item')
router.register(r'sales-tax-charges', SalesTaxChargeViewSet, basename='sales-tax-charge')
router.register(r'sales-payments', SalesPaymentViewSet, basename='sales-payment')

router.register(r'boms', BOMViewSet, basename='bom')
router.register(r'work-orders', WorkOrderViewSet, basename='work-order')
router.register(r'job-cards', JobCardViewSet, basename='job-card')

router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leave-request')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'payroll', PayrollEntryViewSet, basename='payroll')

router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'opportunities', OpportunityViewSet, basename='opportunity')

router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')

router.register(r'asset-categories', AssetCategoryViewSet, basename='asset-category')
router.register(r'assets', AssetViewSet, basename='asset')

router.register(r'workflows', WorkflowViewSet, basename='workflow')
router.register(r'workflow-instances', WorkflowInstanceViewSet, basename='workflow-instance')

urlpatterns = [
    path('', include(router.urls)),
]
