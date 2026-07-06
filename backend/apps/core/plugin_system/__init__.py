"""
Plugin system for Nexus ERP.
Provides hooks, dynamic loading, and extensibility architecture.
"""
from .registry import PluginRegistry
from .hooks import HookManager, Hook
from .loader import PluginLoader
from .base import PluginBase, PluginConfig

__all__ = [
    'PluginRegistry', 'HookManager', 'Hook',
    'PluginLoader', 'PluginBase', 'PluginConfig',
]
