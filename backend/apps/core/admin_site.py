"""
Nexus Framework - Custom Admin Site
Icons stored as arrays (lists) for easy management
"""
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse


class NexusAdminSite(AdminSite):
    site_header = 'Nexus-Framework Dashboard'
    site_title = 'Nexus ERP Control Center'
    index_title = 'Welcome to your ERP Control Center'
    site_url = '/'

    # ── Module Icons as Array ─────────────────────────
    MODULE_ICONS = [
        # [app_label, icon, color, description]
        ['core', '⚙️', '#3b82f6', 'Users, Branches & Warehouses'],
        ['pmo', '📁', '#8b5cf6', 'Projects, Tasks & Milestones'],
        ['industry', '🏭', '#06b6d4', 'Sectors, Companies & Metrics'],
        ['ai_module', '🤖', '#6366f1', 'AI Models, Predictions & Insights'],
        ['regulatory', '⚖️', '#ec4899', 'Regulations, Compliance & Risks'],
        ['auth', '🔐', '#ef4444', 'Authentication & Authorization'],
        ['authtoken', '🎫', '#f97316', 'API Token Management'],
    ]

    # ── Model Icons as Array ────────────────────────────
    MODEL_ICONS = [
        # [model_name, icon]
        ['user', '👤'],
        ['branch', '📍'],
        ['warehouse', '🏭'],
        ['project', '🚀'],
        ['task', '✅'],
        ['milestone', '🎯'],
        ['sector', '📊'],
        ['company', '🏢'],
        ['metric', '📈'],
        ['aimodel', '🧠'],
        ['prediction', '🔮'],
        ['insight', '💡'],
        ['regulation', '📜'],
        ['compliancecheck', '✓'],
        ['risk', '⚠️'],
        ['group', '👥'],
        ['permission', '🔒'],
        ['token', '🎫'],
        ['tokenproxy', '🎟️'],
    ]

    # ── Module Order Array ─────────────────────────────
    MODULE_ORDER = [
        'core', 'pmo', 'industry', 'ai_module',
        'regulatory', 'auth', 'authtoken'
    ]

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)

        # Convert arrays to lookup dicts for processing
        module_meta = {
            row[0]: {'icon': row[1], 'color': row[2], 'description': row[3]}
            for row in self.MODULE_ICONS
        }
        model_icons = {
            row[0]: row[1]
            for row in self.MODEL_ICONS
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

        app_list.sort(
            key=lambda x: self.MODULE_ORDER.index(x['app_label'])
            if x['app_label'] in self.MODULE_ORDER else 999
        )
        return app_list

    def index(self, request, extra_context=None):
        app_list = self.get_app_list(request)

        # Build icons array for template context
        module_icons_array = [
            {
                'label': row[0],
                'icon': row[1],
                'color': row[2],
                'description': row[3]
            }
            for row in self.MODULE_ICONS
        ]

        model_icons_array = [
            {'name': row[0], 'icon': row[1]}
            for row in self.MODEL_ICONS
        ]

        context = {
            **self.each_context(request),
            'title': self.index_title,
            'app_list': app_list,
            'module_count': len(app_list),
            'total_models': sum(len(a.get('models', [])) for a in app_list),
            # Arrays passed to template
            'module_icons_array': module_icons_array,
            'model_icons_array': model_icons_array,
            'module_order': self.MODULE_ORDER,
        }
        context.update(extra_context or {})
        return TemplateResponse(request, 'admin/index.html', context)


admin_site = NexusAdminSite(name='nexus_admin')
