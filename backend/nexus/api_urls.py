from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.core.views import UserViewSet, CompanyViewSet, BranchViewSet, WarehouseViewSet
from apps.accounts.views import AccountViewSet, JournalEntryViewSet
from apps.inventory.views import ItemViewSet, StockEntryViewSet
from apps.buying.views import SupplierViewSet, PurchaseOrderViewSet
from apps.selling.views import CustomerViewSet, SalesOrderViewSet
from apps.hr.views import EmployeeViewSet, DepartmentViewSet
from apps.crm.views import LeadViewSet
from apps.projects.views import ProjectViewSet
from apps.assets.views import AssetViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'journal-entries', JournalEntryViewSet, basename='journal-entry')
router.register(r'items', ItemViewSet, basename='item')
router.register(r'stock-entries', StockEntryViewSet, basename='stock-entry')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'sales-orders', SalesOrderViewSet, basename='sales-order')
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'assets', AssetViewSet, basename='asset')

urlpatterns = [
    path('', include(router.urls)),
]
