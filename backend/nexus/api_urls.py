from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.core.views import UserViewSet, CompanyViewSet, BranchViewSet, WarehouseViewSet
from apps.accounts.views import AccountViewSet, JournalEntryViewSet
from apps.inventory.views import ItemViewSet, ItemGroupViewSet, StockEntryViewSet
from apps.buying.views import SupplierViewSet, PurchaseOrderViewSet
from apps.selling.views import CustomerViewSet, SalesOrderViewSet
from apps.manufacturing.views import WorkOrderViewSet, BOMViewSet
from apps.hr.views import EmployeeViewSet, DepartmentViewSet
from apps.crm.views import LeadViewSet, OpportunityViewSet
from apps.projects.views import ProjectViewSet, TaskViewSet
from apps.assets.views import AssetViewSet, AssetCategoryViewSet
from apps.workflow.views import WorkflowViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'branches', BranchViewSet)
router.register(r'warehouses', WarehouseViewSet)
router.register(r'accounts', AccountViewSet)
router.register(r'journal-entries', JournalEntryViewSet)
router.register(r'items', ItemViewSet)
router.register(r'item-groups', ItemGroupViewSet)
router.register(r'stock-entries', StockEntryViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'purchase-orders', PurchaseOrderViewSet)
router.register(r'customers', CustomerViewSet)
router.register(r'sales-orders', SalesOrderViewSet)
router.register(r'work-orders', WorkOrderViewSet)
router.register(r'boms', BOMViewSet)
router.register(r'employees', EmployeeViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'leads', LeadViewSet)
router.register(r'opportunities', OpportunityViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'assets', AssetViewSet)
router.register(r'asset-categories', AssetCategoryViewSet)
router.register(r'workflows', WorkflowViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
]
