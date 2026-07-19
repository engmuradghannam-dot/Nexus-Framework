import graphene
from graphene_django import DjangoObjectType
from django.apps import apps
from django.db.models import Q, Sum, Avg, Count, Max, Min
from nexus.apps.core.models import Company, Branch, Department
from nexus.apps.pmo.models import Project, Task, Milestone
from nexus.apps.industry.models import Product, Inventory, Supplier, PurchaseOrder
from nexus.apps.hr.models import Employee, Attendance, LeaveRequest, PayrollRun
from nexus.apps.ecommerce.models import Order, Customer
from nexus.apps.accounting.models import Invoice, Payment, ChartOfAccounts

# ============ TYPES ============
class CompanyType(DjangoObjectType):
    class Meta:
        model = Company
        fields = '__all__'

    total_employees = graphene.Int()
    total_branches = graphene.Int()

    def resolve_total_employees(self, info):
        return self.employees.count()

    def resolve_total_branches(self, info):
        return self.branches.count()

class EmployeeType(DjangoObjectType):
    class Meta:
        model = Employee
        fields = '__all__'

    attendance_rate = graphene.Float()
    leave_balance = graphene.Int()

    def resolve_attendance_rate(self, info):
        total = self.attendances.count()
        if total == 0:
            return 100.0
        present = self.attendances.filter(status='present').count()
        return round(present / total * 100, 2)

    def resolve_leave_balance(self, info):
        from nexus.apps.hr.models import LeaveType, LeaveRequest
        total_entitled = sum(lt.days_per_year for lt in LeaveType.objects.all())
        used = LeaveRequest.objects.filter(employee=self, status='approved').count()
        return total_entitled - used

class ProjectType(DjangoObjectType):
    class Meta:
        model = Project
        fields = '__all__'

    completion_percentage = graphene.Float()
    total_tasks = graphene.Int()
    completed_tasks = graphene.Int()

    def resolve_completion_percentage(self, info):
        total = self.tasks.count()
        if total == 0:
            return 0.0
        completed = self.tasks.filter(completed=True).count()
        return round(completed / total * 100, 2)

    def resolve_total_tasks(self, info):
        return self.tasks.count()

    def resolve_completed_tasks(self, info):
        return self.tasks.filter(completed=True).count()

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = '__all__'

    stock_status = graphene.String()

    def resolve_stock_status(self, info):
        if self.quantity <= self.min_stock:
            return 'low'
        elif self.quantity <= self.min_stock * 1.5:
            return 'medium'
        return 'high'

class InvoiceType(DjangoObjectType):
    class Meta:
        model = Invoice
        fields = '__all__'

    days_overdue = graphene.Int()

    def resolve_days_overdue(self, info):
        from datetime import date
        if self.status == 'overdue' and self.due_date:
            return (date.today() - self.due_date).days
        return 0

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = '__all__'

class DashboardStatsType(graphene.ObjectType):
    total_companies = graphene.Int()
    total_employees = graphene.Int()
    total_projects = graphene.Int()
    total_products = graphene.Int()
    total_invoices = graphene.Int()
    total_revenue = graphene.Float()
    total_expenses = graphene.Float()
    pending_tasks = graphene.Int()
    overdue_invoices = graphene.Int()
    low_stock_items = graphene.Int()

class SalaryStatsType(graphene.ObjectType):
    avg = graphene.Float()
    min = graphene.Float()
    max = graphene.Float()
    total = graphene.Float()
    count = graphene.Int()

# ============ QUERIES ============
class Query(graphene.ObjectType):
    # Single objects
    company = graphene.Field(CompanyType, id=graphene.ID())
    employee = graphene.Field(EmployeeType, id=graphene.ID())
    project = graphene.Field(ProjectType, id=graphene.ID())
    product = graphene.Field(ProductType, id=graphene.ID())
    invoice = graphene.Field(InvoiceType, id=graphene.ID())

    # Lists with filtering
    companies = graphene.List(CompanyType, search=graphene.String(), is_active=graphene.Boolean())
    employees = graphene.List(EmployeeType, 
        search=graphene.String(),
        company_id=graphene.ID(),
        department_id=graphene.ID(),
        status=graphene.String(),
        min_salary=graphene.Float(),
        max_salary=graphene.Float()
    )
    projects = graphene.List(ProjectType, 
        search=graphene.String(),
        company_id=graphene.ID(),
        status=graphene.String(),
        is_overdue=graphene.Boolean()
    )
    products = graphene.List(ProductType,
        search=graphene.String(),
        warehouse_id=graphene.ID(),
        low_stock=graphene.Boolean(),
        min_price=graphene.Float(),
        max_price=graphene.Float()
    )
    invoices = graphene.List(InvoiceType,
        search=graphene.String(),
        status=graphene.String(),
        invoice_type=graphene.String(),
        overdue=graphene.Boolean(),
        date_from=graphene.Date(),
        date_to=graphene.Date()
    )
    orders = graphene.List(OrderType,
        search=graphene.String(),
        status=graphene.String(),
        customer_id=graphene.ID(),
        date_from=graphene.Date(),
        date_to=graphene.Date()
    )

    # Dashboard
    dashboard_stats = graphene.Field(DashboardStatsType)

    # Aggregation
    employee_salary_stats = graphene.Field(SalaryStatsType)

    # Search across all models
    global_search = graphene.List(graphene.String, query=graphene.String(required=True))

    # Resolvers
    def resolve_company(self, info, id=None):
        if id:
            return Company.objects.filter(id=id).first()
        return None

    def resolve_employee(self, info, id=None):
        if id:
            return Employee.objects.filter(id=id).first()
        return None

    def resolve_project(self, info, id=None):
        if id:
            return Project.objects.filter(id=id).first()
        return None

    def resolve_product(self, info, id=None):
        if id:
            return Product.objects.filter(id=id).first()
        return None

    def resolve_invoice(self, info, id=None):
        if id:
            return Invoice.objects.filter(id=id).first()
        return None

    def resolve_companies(self, info, search=None, is_active=None):
        qs = Company.objects.all()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        return qs

    def resolve_employees(self, info, search=None, company_id=None, department_id=None, 
                          status=None, min_salary=None, max_salary=None):
        qs = Employee.objects.all()
        if search:
            qs = qs.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) | 
                          Q(employee_id__icontains=search) | Q(job_title__icontains=search))
        if company_id:
            qs = qs.filter(company_id=company_id)
        if department_id:
            qs = qs.filter(department_id=department_id)
        if status:
            qs = qs.filter(status=status)
        if min_salary:
            qs = qs.filter(salary__gte=min_salary)
        if max_salary:
            qs = qs.filter(salary__lte=max_salary)
        return qs

    def resolve_projects(self, info, search=None, company_id=None, status=None, is_overdue=None):
        qs = Project.objects.all()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
        if company_id:
            qs = qs.filter(company_id=company_id)
        if status:
            qs = qs.filter(status=status)
        if is_overdue:
            from datetime import date
            qs = qs.filter(end_date__lt=date.today(), status__in=['active', 'on_hold'])
        return qs

    def resolve_products(self, info, search=None, warehouse_id=None, low_stock=None,
                        min_price=None, max_price=None):
        qs = Product.objects.all()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(sku__icontains=search) | 
                          Q(description__icontains=search))
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        if low_stock:
            qs = qs.filter(quantity__lte=models.F('min_stock'))
        if min_price:
            qs = qs.filter(unit_price__gte=min_price)
        if max_price:
            qs = qs.filter(unit_price__lte=max_price)
        return qs

    def resolve_invoices(self, info, search=None, status=None, invoice_type=None,
                        overdue=None, date_from=None, date_to=None):
        qs = Invoice.objects.all()
        if search:
            qs = qs.filter(Q(invoice_number__icontains=search) | Q(customer_name__icontains=search))
        if status:
            qs = qs.filter(status=status)
        if invoice_type:
            qs = qs.filter(invoice_type=invoice_type)
        if overdue:
            from datetime import date
            qs = qs.filter(due_date__lt=date.today(), status__in=['sent', 'draft'])
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs

    def resolve_orders(self, info, search=None, status=None, customer_id=None,
                      date_from=None, date_to=None):
        qs = Order.objects.all()
        if search:
            qs = qs.filter(Q(order_number__icontains=search))
        if status:
            qs = qs.filter(status=status)
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return qs

    def resolve_dashboard_stats(self, info):
        from datetime import date
        stats = DashboardStatsType()
        stats.total_companies = Company.objects.count()
        stats.total_employees = Employee.objects.filter(status='active').count()
        stats.total_projects = Project.objects.count()
        stats.total_products = Product.objects.count()
        stats.total_invoices = Invoice.objects.count()
        stats.total_revenue = sum(i.total for i in Invoice.objects.filter(invoice_type='sales', status='paid'))
        stats.total_expenses = sum(i.total for i in Invoice.objects.filter(invoice_type='purchase', status='paid'))
        stats.pending_tasks = Task.objects.filter(completed=False).count()
        stats.overdue_invoices = Invoice.objects.filter(due_date__lt=date.today(), status__in=['sent', 'draft']).count()
        stats.low_stock_items = Product.objects.filter(quantity__lte=models.F('min_stock')).count()
        return stats

    def resolve_employee_salary_stats(self, info):
        from django.db.models import Avg, Min, Max, Sum, Count
        stats = Employee.objects.filter(status='active').aggregate(
            avg=Avg('salary'),
            min=Min('salary'),
            max=Max('salary'),
            total=Sum('salary'),
            count=Count('id')
        )
        return SalaryStatsType(**stats)

    def resolve_global_search(self, info, query):
        results = []
        # Search companies
        companies = Company.objects.filter(Q(name__icontains=query))[:3]
        for c in companies:
            results.append(f"Company: {c.name}")
        # Search employees
        employees = Employee.objects.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query))[:3]
        for e in employees:
            results.append(f"Employee: {e.full_name}")
        # Search products
        products = Product.objects.filter(Q(name__icontains=query) | Q(sku__icontains=query))[:3]
        for p in products:
            results.append(f"Product: {p.name}")
        # Search projects
        projects = Project.objects.filter(Q(name__icontains=query))[:3]
        for p in projects:
            results.append(f"Project: {p.name}")
        return results

# ============ MUTATIONS ============
class CreateCompany(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()
        address = graphene.String()
        phone = graphene.String()
        email = graphene.String()

    company = graphene.Field(CompanyType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, name, description='', address='', phone='', email=''):
        company = Company.objects.create(
            name=name,
            description=description,
            address=address,
            phone=phone,
            email=email
        )
        return CreateCompany(company=company, success=True, message="Company created successfully")

class UpdateEmployeeStatus(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        status = graphene.String(required=True)

    employee = graphene.Field(EmployeeType)
    success = graphene.Boolean()

    def mutate(self, info, id, status):
        employee = Employee.objects.get(id=id)
        employee.status = status
        employee.save()
        return UpdateEmployeeStatus(employee=employee, success=True)

class CreateInvoice(graphene.Mutation):
    class Arguments:
        invoice_number = graphene.String(required=True)
        customer_name = graphene.String(required=True)
        invoice_type = graphene.String(required=True)
        subtotal = graphene.Float(required=True)
        tax_rate = graphene.Float()

    invoice = graphene.Field(InvoiceType)
    success = graphene.Boolean()

    def mutate(self, info, invoice_number, customer_name, invoice_type, subtotal, tax_rate=0):
        from nexus.apps.core.models import Company
        company = Company.objects.first()
        invoice = Invoice.objects.create(
            invoice_number=invoice_number,
            company=company,
            customer_name=customer_name,
            invoice_type=invoice_type,
            subtotal=subtotal,
            tax_rate=tax_rate,
            total=subtotal * (1 + tax_rate/100)
        )
        return CreateInvoice(invoice=invoice, success=True)

class Mutation(graphene.ObjectType):
    create_company = CreateCompany.Field()
    update_employee_status = UpdateEmployeeStatus.Field()
    create_invoice = CreateInvoice.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
