"""
Hook system for plugin event-driven architecture.
"""
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import threading
import traceback


@dataclass
class Hook:
    """Represents a registered hook callback."""
    name: str
    callback: Callable
    priority: int = 10  # Lower = higher priority
    plugin_id: Optional[str] = None
    once: bool = False  # Remove after first call
    _called: bool = field(default=False, repr=False)

    def __post_init__(self):
        self.created_at = datetime.utcnow()

    def call(self, *args, **kwargs) -> Any:
        """Execute hook callback."""
        if self.once and self._called:
            return None
        self._called = True
        try:
            return self.callback(*args, **kwargs)
        except Exception as e:
            # Log but don't break hook chain
            print(f"Hook {self.name} error: {e}")
            traceback.print_exc()
            return None


class HookManager:
    """
    Central hook manager for plugin system.

    Usage:
        hooks = HookManager()

        # Register
        hooks.register('invoice.created', my_callback, priority=5)

        # Fire
        hooks.do_action('invoice.created', invoice_data)

        # Filter
        result = hooks.apply_filter('invoice.total', invoice, 100.0)
    """

    def __init__(self):
        self._hooks: Dict[str, List[Hook]] = {}
        self._lock = threading.RLock()

    def register(self, hook_name: str, callback: Callable, priority: int = 10, 
                 plugin_id: Optional[str] = None, once: bool = False) -> Hook:
        """Register a hook callback."""
        with self._lock:
            hook = Hook(
                name=hook_name,
                callback=callback,
                priority=priority,
                plugin_id=plugin_id,
                once=once
            )

            if hook_name not in self._hooks:
                self._hooks[hook_name] = []

            self._hooks[hook_name].append(hook)
            # Sort by priority
            self._hooks[hook_name].sort(key=lambda h: h.priority)

            return hook

    def unregister(self, hook_name: str, callback: Optional[Callable] = None):
        """Unregister hook(s). If callback is None, remove all for hook_name."""
        with self._lock:
            if hook_name not in self._hooks:
                return

            if callback is None:
                del self._hooks[hook_name]
            else:
                self._hooks[hook_name] = [
                    h for h in self._hooks[hook_name] 
                    if h.callback != callback
                ]

    def do_action(self, hook_name: str, *args, **kwargs):
        """Execute all callbacks for an action hook."""
        with self._lock:
            hooks = self._hooks.get(hook_name, [])

        for hook in hooks:
            hook.call(*args, **kwargs)

    def apply_filter(self, hook_name: str, value: Any, *args, **kwargs) -> Any:
        """Apply all callbacks as filters, passing value through each."""
        with self._lock:
            hooks = self._hooks.get(hook_name, [])

        for hook in hooks:
            result = hook.call(value, *args, **kwargs)
            if result is not None:
                value = result

        return value

    def has_hook(self, hook_name: str) -> bool:
        """Check if any hooks are registered."""
        return hook_name in self._hooks and len(self._hooks[hook_name]) > 0

    def get_hooks(self, hook_name: str) -> List[Hook]:
        """Get all hooks for a name."""
        return self._hooks.get(hook_name, [])

    def list_hooks(self) -> Dict[str, int]:
        """List all registered hooks with count."""
        return {name: len(hooks) for name, hooks in self._hooks.items()}


# Pre-defined system hooks
SYSTEM_HOOKS = [
    # Authentication
    'user.authenticated',
    'user.created',
    'user.updated',
    'user.deleted',

    # Tenant
    'tenant.created',
    'tenant.switched',
    'tenant.suspended',
    'tenant.activated',

    # Billing
    'invoice.created',
    'invoice.paid',
    'subscription.created',
    'subscription.cancelled',
    'payment.received',
    'payment.failed',

    # Inventory
    'item.created',
    'item.updated',
    'stock.moved',
    'stock.low',

    # Orders
    'purchase_order.created',
    'purchase_order.submitted',
    'sales_order.created',
    'sales_order.confirmed',

    # Manufacturing
    'work_order.created',
    'work_order.completed',

    # HR
    'employee.hired',
    'employee.terminated',
    'leave.approved',
    'payroll.processed',

    # Reports
    'report.generated',
    'export.completed',

    # System
    'system.startup',
    'system.shutdown',
    'error.occurred',
]
