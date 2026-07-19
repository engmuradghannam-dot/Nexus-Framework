from django.db.models import Q, Count, Sum, Avg, Max, Min, F
from django.apps import apps
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import json

class AdvancedSearchViewSet(viewsets.ViewSet):
    """Advanced search across all models with Elasticsearch-like features"""
    permission_classes = [IsAuthenticated]

    # Define searchable models and fields
    SEARCHABLE_MODELS = {
        'companies': {
            'model': 'core.Company',
            'fields': ['name', 'description', 'address', 'phone', 'email'],
            'filters': ['is_active', 'created_at'],
            'sortable': ['name', 'created_at', 'updated_at']
        },
        'employees': {
            'model': 'hr.Employee',
            'fields': ['first_name', 'last_name', 'employee_id', 'job_title', 'email', 'phone'],
            'filters': ['status', 'department', 'branch', 'company', 'hire_date'],
            'sortable': ['first_name', 'last_name', 'salary', 'hire_date', 'created_at']
        },
        'products': {
            'model': 'industry.Product',
            'fields': ['name', 'sku', 'description', 'category'],
            'filters': ['warehouse', 'quantity', 'unit_price', 'min_stock'],
            'sortable': ['name', 'unit_price', 'quantity', 'created_at']
        },
        'projects': {
            'model': 'pmo.Project',
            'fields': ['name', 'description', 'status'],
            'filters': ['company', 'status', 'priority', 'start_date', 'end_date'],
            'sortable': ['name', 'start_date', 'end_date', 'budget', 'created_at']
        },
        'invoices': {
            'model': 'accounting.Invoice',
            'fields': ['invoice_number', 'customer_name', 'notes'],
            'filters': ['status', 'invoice_type', 'date', 'due_date', 'company'],
            'sortable': ['date', 'due_date', 'total', 'created_at']
        },
        'orders': {
            'model': 'ecommerce.Order',
            'fields': ['order_number', 'shipping_address', 'notes'],
            'filters': ['status', 'payment_status', 'customer', 'date'],
            'sortable': ['date', 'total', 'created_at']
        },
        'tasks': {
            'model': 'pmo.Task',
            'fields': ['name', 'description'],
            'filters': ['project', 'assigned_to', 'completed', 'priority'],
            'sortable': ['name', 'start_date', 'end_date', 'created_at']
        }
    }

    @action(detail=False, methods=['post'])
    def search(self, request):
        """Advanced search with full-text, filters, sorting, pagination"""
        data = request.data
        model_name = data.get('model')
        query = data.get('q', '')
        filters = data.get('filters', {})
        sort = data.get('sort', '-created_at')
        page = data.get('page', 1)
        page_size = min(data.get('page_size', 20), 100)

        if model_name not in self.SEARCHABLE_MODELS:
            return Response({"error": f"Model '{model_name}' not searchable"}, status=status.HTTP_400_BAD_REQUEST)

        config = self.SEARCHABLE_MODELS[model_name]
        model = apps.get_model(config['model'])
        qs = model.objects.all()

        # Full-text search
        if query:
            q_objects = Q()
            for field in config['fields']:
                q_objects |= Q(**{f"{field}__icontains": query})
            qs = qs.filter(q_objects)

        # Apply filters
        for key, value in filters.items():
            if key in config['filters']:
                if '__' in key:
                    qs = qs.filter(**{key: value})
                elif isinstance(value, dict):
                    # Range filters: {'gte': 10, 'lte': 100}
                    if 'gte' in value:
                        qs = qs.filter(**{f"{key}__gte": value['gte']})
                    if 'lte' in value:
                        qs = qs.filter(**{f"{key}__lte": value['lte']})
                    if 'gt' in value:
                        qs = qs.filter(**{f"{key}__gt": value['gt']})
                    if 'lt' in value:
                        qs = qs.filter(**{f"{key}__lt": value['lt']})
                else:
                    qs = qs.filter(**{key: value})

        # Sorting
        if sort.lstrip('-') in config['sortable']:
            qs = qs.order_by(sort)

        # Pagination
        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size
        results = qs[start:end]

        # Serialize results
        from rest_framework import serializers
        class DynamicSerializer(serializers.ModelSerializer):
            class Meta:
                model = model
                fields = '__all__'

        serializer = DynamicSerializer(results, many=True)

        return Response({
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "results": serializer.data
        })

    @action(detail=False, methods=['post'])
    def global_search(self, request):
        """Search across all models simultaneously"""
        query = request.data.get('q', '')
        limit_per_model = request.data.get('limit_per_model', 5)

        if not query:
            return Response({"error": "Query required"}, status=status.HTTP_400_BAD_REQUEST)

        results = {}

        for model_name, config in self.SEARCHABLE_MODELS.items():
            model = apps.get_model(config['model'])
            q_objects = Q()
            for field in config['fields']:
                q_objects |= Q(**{f"{field}__icontains": query})

            qs = model.objects.filter(q_objects)[:limit_per_model]

            from rest_framework import serializers
            class DynamicSerializer(serializers.ModelSerializer):
                class Meta:
                    model = model
                    fields = ['id'] + config['fields'][:3]

            results[model_name] = DynamicSerializer(qs, many=True).data

        return Response({
            "query": query,
            "results": results
        })

    @action(detail=False, methods=['post'])
    def suggest(self, request):
        """Auto-complete suggestions"""
        query = request.data.get('q', '')
        model_name = request.data.get('model', 'companies')
        field = request.data.get('field', 'name')
        limit = min(request.data.get('limit', 10), 20)

        if model_name not in self.SEARCHABLE_MODELS:
            return Response({"error": "Model not found"}, status=status.HTTP_400_BAD_REQUEST)

        config = self.SEARCHABLE_MODELS[model_name]
        if field not in config['fields']:
            return Response({"error": f"Field '{field}' not searchable"}, status=status.HTTP_400_BAD_REQUEST)

        model = apps.get_model(config['model'])
        suggestions = model.objects.filter(
            **{f"{field}__icontains": query}
        ).values_list(field, flat=True).distinct()[:limit]

        return Response({
            "query": query,
            "suggestions": list(suggestions)
        })

    @action(detail=False, methods=['post'])
    def facets(self, request):
        """Get filter facets/counts for a model"""
        model_name = request.data.get('model')

        if model_name not in self.SEARCHABLE_MODELS:
            return Response({"error": "Model not found"}, status=status.HTTP_400_BAD_REQUEST)

        config = self.SEARCHABLE_MODELS[model_name]
        model = apps.get_model(config['model'])

        facets = {}

        # Status facets
        if hasattr(model, 'status'):
            facets['status'] = dict(model.objects.values('status').annotate(count=Count('id')).values_list('status', 'count'))

        # Date facets (by month)
        if hasattr(model, 'created_at'):
            from django.db.models.functions import TruncMonth
            facets['by_month'] = dict(
                model.objects.annotate(month=TruncMonth('created_at'))
                .values('month').annotate(count=Count('id'))
                .values_list('month', 'count')
            )

        return Response({"model": model_name, "facets": facets})


class AggregationAPIViewSet(viewsets.ViewSet):
    """Aggregation and analytics endpoints"""
    permission_classes = [IsAuthenticated]

    AGGREGATION_MODELS = {
        'employees': {
            'model': 'hr.Employee',
            'numeric_fields': ['salary'],
            'group_fields': ['status', 'department', 'branch', 'company'],
            'date_fields': ['hire_date', 'created_at']
        },
        'invoices': {
            'model': 'accounting.Invoice',
            'numeric_fields': ['subtotal', 'tax_amount', 'discount', 'total', 'amount_paid'],
            'group_fields': ['status', 'invoice_type', 'company'],
            'date_fields': ['date', 'due_date', 'created_at']
        },
        'products': {
            'model': 'industry.Product',
            'numeric_fields': ['unit_price', 'quantity', 'min_stock'],
            'group_fields': ['warehouse', 'category'],
            'date_fields': ['created_at']
        },
        'orders': {
            'model': 'ecommerce.Order',
            'numeric_fields': ['subtotal', 'tax_amount', 'discount', 'shipping_cost', 'total'],
            'group_fields': ['status', 'payment_status', 'customer'],
            'date_fields': ['created_at']
        },
        'projects': {
            'model': 'pmo.Project',
            'numeric_fields': ['budget'],
            'group_fields': ['status', 'priority', 'company'],
            'date_fields': ['start_date', 'end_date', 'created_at']
        }
    }

    @action(detail=False, methods=['post'])
    def aggregate(self, request):
        """Dynamic aggregation with group by"""
        data = request.data
        model_name = data.get('model')
        aggregations = data.get('aggregations', [])  # ['sum', 'avg', 'count', 'max', 'min']
        fields = data.get('fields', [])  # ['salary', 'total']
        group_by = data.get('group_by')  # 'department'
        filters = data.get('filters', {})

        if model_name not in self.AGGREGATION_MODELS:
            return Response({"error": f"Model '{model_name}' not supported"}, status=status.HTTP_400_BAD_REQUEST)

        config = self.AGGREGATION_MODELS[model_name]
        model = apps.get_model(config['model'])
        qs = model.objects.all()

        # Apply filters
        for key, value in filters.items():
            qs = qs.filter(**{key: value})

        # Build aggregation
        result = {}

        if group_by and group_by in config['group_fields']:
            grouped = qs.values(group_by)

            for agg in aggregations:
                for field in fields:
                    if field not in config['numeric_fields']:
                        continue

                    if agg == 'sum':
                        data = grouped.annotate(value=Sum(field)).values(group_by, 'value')
                        result[f"{field}__sum"] = list(data)
                    elif agg == 'avg':
                        data = grouped.annotate(value=Avg(field)).values(group_by, 'value')
                        result[f"{field}__avg"] = list(data)
                    elif agg == 'count':
                        data = grouped.annotate(value=Count('id')).values(group_by, 'value')
                        result[f"count"] = list(data)
                    elif agg == 'max':
                        data = grouped.annotate(value=Max(field)).values(group_by, 'value')
                        result[f"{field}__max"] = list(data)
                    elif agg == 'min':
                        data = grouped.annotate(value=Min(field)).values(group_by, 'value')
                        result[f"{field}__min"] = list(data)
        else:
            # Overall aggregation
            for agg in aggregations:
                for field in fields:
                    if field not in config['numeric_fields']:
                        continue

                    if agg == 'sum':
                        result[f"{field}__sum"] = qs.aggregate(v=Sum(field))['v'] or 0
                    elif agg == 'avg':
                        result[f"{field}__avg"] = round(qs.aggregate(v=Avg(field))['v'] or 0, 2)
                    elif agg == 'count':
                        result['count'] = qs.count()
                    elif agg == 'max':
                        result[f"{field}__max"] = qs.aggregate(v=Max(field))['v'] or 0
                    elif agg == 'min':
                        result[f"{field}__min"] = qs.aggregate(v=Min(field))['v'] or 0

        return Response({
            "model": model_name,
            "group_by": group_by,
            "aggregations": result
        })

    @action(detail=False, methods=['post'])
    def time_series(self, request):
        """Time series aggregation"""
        data = request.data
        model_name = data.get('model')
        field = data.get('field')
        date_field = data.get('date_field', 'created_at')
        interval = data.get('interval', 'month')  # day, week, month, year

        if model_name not in self.AGGREGATION_MODELS:
            return Response({"error": "Model not supported"}, status=status.HTTP_400_BAD_REQUEST)

        config = self.AGGREGATION_MODELS[model_name]
        model = apps.get_model(config['model'])

        if date_field not in config['date_fields']:
            return Response({"error": f"Date field '{date_field}' not supported"}, status=status.HTTP_400_BAD_REQUEST)

        from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear

        trunc_map = {
            'day': TruncDay,
            'week': TruncWeek,
            'month': TruncMonth,
            'year': TruncYear
        }

        trunc_func = trunc_map.get(interval, TruncMonth)

        results = model.objects.annotate(
            period=trunc_func(date_field)
        ).values('period').annotate(
            count=Count('id'),
            total=Sum(field) if field else 0
        ).order_by('period')

        return Response({
            "model": model_name,
            "interval": interval,
            "field": field,
            "data": list(results)
        })

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Complete dashboard analytics"""
        from nexus.apps.core.models import Company
        from nexus.apps.hr.models import Employee
        from nexus.apps.pmo.models import Project, Task
        from nexus.apps.industry.models import Product
        from nexus.apps.accounting.models import Invoice, Payment
        from nexus.apps.ecommerce.models import Order
        from django.db.models import Count, Sum, Avg, Q
        from datetime import date, timedelta

        today = date.today()
        month_start = today.replace(day=1)
        last_month = today - timedelta(days=30)

        return Response({
            "overview": {
                "total_companies": Company.objects.count(),
                "total_employees": Employee.objects.filter(status='active').count(),
                "total_projects": Project.objects.count(),
                "total_products": Product.objects.count(),
            },
            "hr": {
                "active_employees": Employee.objects.filter(status='active').count(),
                "on_leave": Employee.objects.filter(status='on_leave').count(),
                "new_hires_this_month": Employee.objects.filter(hire_date__gte=month_start).count(),
                "avg_salary": round(Employee.objects.filter(status='active').aggregate(v=Avg('salary'))['v'] or 0, 2),
                "total_payroll": Employee.objects.filter(status='active').aggregate(v=Sum('salary'))['v'] or 0,
            },
            "finance": {
                "total_revenue": Invoice.objects.filter(invoice_type='sales', status='paid').aggregate(v=Sum('total'))['v'] or 0,
                "total_expenses": Invoice.objects.filter(invoice_type='purchase', status='paid').aggregate(v=Sum('total'))['v'] or 0,
                "outstanding_receivables": Invoice.objects.filter(invoice_type='sales', status__in=['sent', 'overdue']).aggregate(v=Sum('balance_due'))['v'] or 0,
                "overdue_amount": Invoice.objects.filter(status='overdue').aggregate(v=Sum('balance_due'))['v'] or 0,
                "this_month_revenue": Invoice.objects.filter(invoice_type='sales', status='paid', date__gte=month_start).aggregate(v=Sum('total'))['v'] or 0,
            },
            "sales": {
                "total_orders": Order.objects.count(),
                "pending_orders": Order.objects.filter(status='pending').count(),
                "completed_orders": Order.objects.filter(status='delivered').count(),
                "this_month_orders": Order.objects.filter(created_at__date__gte=month_start).count(),
            },
            "inventory": {
                "total_products": Product.objects.count(),
                "low_stock": Product.objects.filter(quantity__lte=F('min_stock')).count(),
                "out_of_stock": Product.objects.filter(quantity=0).count(),
                "total_inventory_value": Product.objects.aggregate(v=Sum(F('quantity') * F('unit_price')))['v'] or 0,
            },
            "projects": {
                "active_projects": Project.objects.filter(status='active').count(),
                "completed_projects": Project.objects.filter(status='completed').count(),
                "overdue_projects": Project.objects.filter(end_date__lt=today, status__in=['active', 'on_hold']).count(),
                "pending_tasks": Task.objects.filter(completed=False).count(),
            }
        })
