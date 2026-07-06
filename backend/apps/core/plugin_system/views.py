from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
import os
import json


class PluginViewSet(viewsets.ViewSet):
    """Plugin management API."""
    permission_classes = [permissions.IsAdminUser]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from apps.core.plugin_system import PluginRegistry
        self.registry = PluginRegistry()
        plugin_dir = getattr(settings, 'PLUGIN_DIR', os.path.join(settings.BASE_DIR, 'plugins'))
        self.registry.discover(plugin_dir)

    def list(self, request):
        """List all plugins."""
        return Response(self.registry.list_plugins())

    @action(detail=False, methods=['post'])
    def load(self, request):
        """Load a plugin."""
        plugin_name = request.data.get('name')
        if not plugin_name:
            return Response({'error': 'Plugin name required'}, status=400)

        try:
            plugin = self.registry.load(plugin_name)
            return Response({
                'status': 'loaded',
                'plugin': plugin.config.to_dict()
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=False, methods=['post'])
    def unload(self, request):
        """Unload a plugin."""
        plugin_name = request.data.get('name')
        self.registry.unload(plugin_name)
        return Response({'status': 'unloaded'})

    @action(detail=False, methods=['post'])
    def enable(self, request):
        """Enable a plugin."""
        plugin_name = request.data.get('name')
        self.registry.enable(plugin_name)
        return Response({'status': 'enabled'})

    @action(detail=False, methods=['post'])
    def disable(self, request):
        """Disable a plugin."""
        plugin_name = request.data.get('name')
        self.registry.disable(plugin_name)
        return Response({'status': 'disabled'})

    @action(detail=False, methods=['get'])
    def hooks(self, request):
        """List all registered hooks."""
        return Response(self.registry.hook_manager.list_hooks())

    @action(detail=False, methods=['post'])
    def install(self, request):
        """Install plugin from uploaded package."""
        # Implementation for plugin upload/install
        return Response({'status': 'not_implemented'})
