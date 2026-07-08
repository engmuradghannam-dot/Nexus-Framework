"""
Nexus Framework - Custom Admin Site
Card-based module explorer with icon grids
"""
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import gettext_lazy as _


class NexusAdminSite(AdminSite):
    site_header = 'Nexus-Framework Dashboard'
    site_title = 'Nexus ERP Control Center'
    index_title = 'Welcome to your ERP Control Center'
    site_url = '/'

    def get_app_list(self, request, app_label=None):
        """Override to provide custom app ordering and metadata."""
        app_list = super().get_app_list(request, app_label)

        # Module metadata with icons and colors
        module_meta = {
            'core': {'icon': '⚙️', 'color': '#3b82f6', 'description': 'Users, Branches & Warehouses'},
            'pmo': {'icon': '📁', 'color': '#8b5cf6', 'description': 'Projects, Tasks & Milestones'},
            'industry': {'icon': '🏭', 'color': '#06b6d4', 'description': 'Sectors, Companies & Metrics'},
            'ai_module': {'icon': '🤖', 'color': '#6366f1', 'description': 'AI Models, Predictions & Insights'},
            'regulatory': {'icon': '⚖️', 'color': '#ec4899', 'description': 'Regulations, Compliance & Risks'},
            'auth': {'icon': '🔐', 'color': '#ef4444', 'description': 'Authentication & Authorization'},
            'authtoken': {'icon': '🎫', 'color': '#f97316', 'description': 'API Token Management'},
        }

        for app in app_list:
            meta = module_meta.get(app['app_label'], {})
            app['icon'] = meta.get('icon', '📦')
            app['color'] = meta.get('color', '#64748b')
            app['description'] = meta.get('description', f"{len(app.get('models', []))} models")

            # Model icons
            model_icons = {
                'user': '👤', 'branch': '📍', 'warehouse': '🏭',
                'project': '🚀', 'task': '✅', 'milestone': '🎯',
                'sector': '📊', 'company': '🏢', 'metric': '📈',
                'aimodel': '🧠', 'prediction': '🔮', 'insight': '💡',
                'regulation': '📜', 'compliancecheck': '✓', 'risk': '⚠️',
                'group': '👥', 'permission': '🔒',
                'token': '🎫', 'tokenproxy': '🎟️',
            }
            for model in app.get('models', []):
                model_key = model['object_name'].lower()
                model['icon'] = model_icons.get(model_key, '📄')

        # Custom ordering
        order = ['core', 'pmo', 'industry', 'ai_module', 'regulatory', 'auth', 'authtoken']
        app_list.sort(key=lambda x: order.index(x['app_label']) if x['app_label'] in order else 999)
        return app_list

    def index(self, request, extra_context=None):
        """Custom admin index with card-based layout."""
        app_list = self.get_app_list(request)
        context = {
            **self.each_context(request),
            'title': self.index_title,
            'app_list': app_list,
            'module_count': len(app_list),
            'total_models': sum(len(a.get('models', [])) for a in app_list),
        }
        context.update(extra_context or {})
        return TemplateResponse(request, 'admin/nexus_index.html', context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('nexus-dashboard/', self.admin_view(self.nexus_dashboard), name='nexus_dashboard'),
        ]
        return custom_urls + urls

    def nexus_dashboard(self, request):
        """Full-screen dashboard view."""
        context = {
            **self.each_context(request),
            'app_list': self.get_app_list(request),
        }
        return TemplateResponse(request, 'admin/nexus_dashboard.html', context)


admin_site = NexusAdminSite(name='nexus_admin')
