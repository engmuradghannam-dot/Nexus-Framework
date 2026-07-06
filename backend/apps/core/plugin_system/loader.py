"""
Dynamic plugin loader with hot-reload support.
"""
import os
import sys
import importlib
import importlib.util
from typing import Optional, Type
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .base import PluginBase


class PluginReloadHandler(FileSystemEventHandler):
    """Watchdog handler for plugin file changes."""

    def __init__(self, registry, plugin_name):
        self.registry = registry
        self.plugin_name = plugin_name

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"Plugin {self.plugin_name} modified, reloading...")
            self.registry.unload(self.plugin_name)
            self.registry.load(self.plugin_name)


class PluginLoader:
    """
    Dynamic plugin loader with optional hot-reload.

    Usage:
        loader = PluginLoader(registry)
        loader.load_from_path('/path/to/custom_plugin')
        loader.enable_hot_reload()
    """

    def __init__(self, registry):
        self.registry = registry
        self._observer: Optional[Observer] = None
        self._watchers = {}

    def load_from_path(self, plugin_path: str) -> Optional[PluginBase]:
        """Load a plugin from a file path."""
        plugin_dir = os.path.dirname(plugin_path)
        plugin_file = os.path.basename(plugin_path)
        plugin_name = os.path.splitext(plugin_file)[0]

        # Add to path
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)

        # Load module
        spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find Plugin class
        plugin_class = getattr(module, 'Plugin', None)
        if plugin_class and issubclass(plugin_class, PluginBase):
            instance = plugin_class()
            instance.initialize({})
            instance.register_hooks(self.registry.hook_manager)
            self.registry._plugins[instance.config.name] = instance
            return instance

        return None

    def enable_hot_reload(self, plugin_dir: str):
        """Enable hot-reload for plugins in directory."""
        self._observer = Observer()

        for plugin_name in self.registry._configs:
            plugin_path = os.path.join(plugin_dir, plugin_name)
            if os.path.exists(plugin_path):
                handler = PluginReloadHandler(self.registry, plugin_name)
                watcher = self._observer.schedule(handler, plugin_path, recursive=True)
                self._watchers[plugin_name] = watcher

        self._observer.start()

    def disable_hot_reload(self):
        """Disable hot-reload."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
