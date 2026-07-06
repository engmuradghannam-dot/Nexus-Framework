"""
Base classes for Nexus ERP plugins.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
import uuid


@dataclass
class PluginConfig:
    """Plugin configuration schema."""
    name: str
    version: str
    description: str = ""
    author: str = ""
    requires: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def to_dict(self):
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'requires': self.requires,
            'permissions': self.permissions,
            'settings': self.settings,
            'enabled': self.enabled,
        }


class PluginBase(ABC):
    """
    Base class for all Nexus ERP plugins.

    Example:
        class MyPlugin(PluginBase):
            config = PluginConfig(
                name='my_plugin',
                version='1.0.0',
                description='My custom plugin',
            )

            def register_hooks(self, hook_manager):
                hook_manager.register('invoice.created', self.on_invoice_created)

            def on_invoice_created(self, invoice_data):
                # Custom logic
                pass
    """

    config: PluginConfig = None
    id: str = None

    def __init__(self):
        self.id = str(uuid.uuid4())
        if self.config is None:
            raise ValueError("Plugin must define a config")

    @abstractmethod
    def register_hooks(self, hook_manager):
        """Register plugin hooks. Called during plugin initialization."""
        pass

    def initialize(self, context: Dict[str, Any]):
        """Called when plugin is loaded. Override for setup logic."""
        pass

    def shutdown(self):
        """Called when plugin is unloaded. Override for cleanup."""
        pass

    def get_setting(self, key: str, default=None):
        """Get plugin setting value."""
        return self.config.settings.get(key, default)

    def has_permission(self, permission: str) -> bool:
        """Check if plugin has required permission."""
        return permission in self.config.permissions

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.config.name} v{self.config.version})>"
