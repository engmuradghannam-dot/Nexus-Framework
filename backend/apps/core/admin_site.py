"""
Nexus Framework - Custom Admin Site
"""
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse


class NexusAdminSite(AdminSite):
    site_header = 'Nexus-Framework Dashboard'
    site_title = 'Nexus ERP Control Center'
    index_title = 'Welcome to your ERP Control Center'
    site_url = '/'

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)

        module_meta = {
            'core': {'icon': '⚙️', 'color': '#3b82f6', 'description': 'Users, Branches & Warehouses'},
            'pmo': {'icon': '📁', 'color': '#8b5cf6', 'description': 'Projects, Tasks & Milestones'},
            'industry': {'icon': '🏭', 'color': '#06b6d4', 'description': 'Sectors, Companies & Metrics'},
            'ai_module': {'icon': '🤖', 'color': '#6366f1', 'description': 'AI Models, Predictions & Insights'},
            'regulatory': {'icon': '⚖️', 'color': '#ec4899', 'description': 'Regulations, Compliance & Risks'},
            'auth': {'icon': '🔐', 'color': '#ef4444', 'description': 'Authentication & Authorization'},
            'authtoken': {'icon': '🎫', 'color': '#f97316', 'description': 'API Token Management'},
        }

        model_icons = {
            'user': '👤', 'branch': '📍', 'warehouse': '🏭',
            'project': '🚀', 'task': '✅', 'milestone': '🎯',
            'sector': '📊', 'company': '🏢', 'metric': '📈',
            'aimodel': '🧠', 'prediction': '🔮', 'insight': '💡',
            'regulation': '📜', 'compliancecheck': '✓', 'risk': '⚠️',
            'group': '👥', 'permission': '🔒',
            'token': '🎫', 'tokenproxy': '🎟️',
        }

        for app in app_list:
            meta = module_meta.get(app['app_label'], {
                'icon': '📦', 'color': '#64748b', 
                'description': f"{len(app.get('models', []))} models"
            })
            app['icon'] = meta['icon']
            app['color'] = meta['color']
            app['description'] = meta['description']

            for model in app.get('models', []):
                model_key = model['object_name'].lower()
                model['icon'] = model_icons.get(model_key, '📄')

        order = ['core', 'pmo', 'industry', 'ai_module', 'regulatory', 'auth', 'authtoken']
        app_list.sort(key=lambda x: order.index(x['app_label']) if x['app_label'] in order else 999)
        return app_list

    def index(self, request, extra_context=None):
        app_list = self.get_app_list(request)
        context = {
            **self.each_context(request),
            'title': self.index_title,
            'app_list': app_list,
            'module_count': len(app_list),
            'total_models': sum(len(a.get('models', [])) for a in app_list),
        }
        context.update(extra_context or {})
        return TemplateResponse(request, 'admin/index.html', context)


admin_site = NexusAdminSite(name='nexus_admin')
