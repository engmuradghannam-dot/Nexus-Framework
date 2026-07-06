"""
Plugin registry for managing installed plugins.
"""
import os
import json
import importlib
from typing import Dict, List, Optional, Type
from pathlib import Path
from .base import PluginBase, PluginConfig
from .hooks import HookManager


class PluginRegistry:
    """
    Central registry for all Nexus ERP plugins.

    Usage:
        registry = PluginRegistry()
        registry.discover('/path/to/plugins')
        registry.load_all()

        # Get plugin
        plugin = registry.get('my_plugin')

        # Enable/disable
        registry.enable('my_plugin')
        registry.disable('my_plugin')
    """

    def __init__(self, hook_manager: Optional[HookManager] = None):
        self._plugins: Dict[str, PluginBase] = {}
        self._configs: Dict[str, dict] = {}
        self._hook_manager = hook_manager or HookManager()
        self._plugin_dir = os.path.join(os.path.dirname(__file__), '../../../plugins')

    def discover(self, plugin_dir: Optional[str] = None) -> List[str]:
        """Discover available plugins in directory."""
        directory = plugin_dir or self._plugin_dir
        discovered = []

        if not os.path.exists(directory):
            return discovered

        for item in os.listdir(directory):
            plugin_path = os.path.join(directory, item)
            config_path = os.path.join(plugin_path, 'plugin.json')

            if os.path.isdir(plugin_path) and os.path.exists(config_path):
                with open(config_path) as f:
                    config = json.load(f)
                self._configs[config['name']] = config
                discovered.append(config['name'])

        return discovered

    def load(self, plugin_name: str, context: Optional[dict] = None) -> Optional[PluginBase]:
        """Load and initialize a plugin."""
        if plugin_name in self._plugins:
            return self._plugins[plugin_name]

        config = self._configs.get(plugin_name)
        if not config:
            raise ValueError(f"Plugin {plugin_name} not found. Run discover() first.")

        if not config.get('enabled', True):
            return None

        # Check dependencies
        for req in config.get('requires', []):
            if req not in self._plugins:
                raise RuntimeError(f"Plugin {plugin_name} requires {req}")

        # Import plugin module
        plugin_module = importlib.import_module(f"plugins.{plugin_name}.plugin")
        plugin_class = getattr(plugin_module, 'Plugin')

        instance = plugin_class()
        instance.config = PluginConfig(**config)

        # Initialize
        instance.initialize(context or {})

        # Register hooks
        instance.register_hooks(self._hook_manager)

        self._plugins[plugin_name] = instance

        # Fire system hook
        self._hook_manager.do_action('plugin.loaded', instance)

        return instance

    def load_all(self, context: Optional[dict] = None):
        """Load all discovered plugins."""
        for name in self._configs:
            try:
                self.load(name, context)
            except Exception as e:
                print(f"Failed to load plugin {name}: {e}")

    def unload(self, plugin_name: str):
        """Unload a plugin."""
        if plugin_name in self._plugins:
            plugin = self._plugins[plugin_name]
            plugin.shutdown()

            # Unregister hooks
            self._hook_manager.unregister(plugin_name)

            del self._plugins[plugin_name]
            self._hook_manager.do_action('plugin.unloaded', plugin_name)

    def get(self, plugin_name: str) -> Optional[PluginBase]:
        """Get loaded plugin by name."""
        return self._plugins.get(plugin_name)

    def list_plugins(self) -> List[dict]:
        """List all plugins with status."""
        result = []
        for name, config in self._configs.items():
            result.append({
                'name': name,
                'version': config.get('version'),
                'enabled': config.get('enabled', True),
                'loaded': name in self._plugins,
                'description': config.get('description', ''),
            })
        return result

    def enable(self, plugin_name: str):
        """Enable a plugin."""
        if plugin_name in self._configs:
            self._configs[plugin_name]['enabled'] = True

    def disable(self, plugin_name: str):
        """Disable a plugin."""
        if plugin_name in self._configs:
            self._configs[plugin_name]['enabled'] = False
        self.unload(plugin_name)

    @property
    def hook_manager(self) -> HookManager:
        return self._hook_manager
