"""
Example plugin: Zakat Calculator for Saudi Arabia.
Demonstrates the plugin system architecture.
"""
from apps.core.plugin_system import PluginBase, PluginConfig


class Plugin(PluginBase):
    config = PluginConfig(
        name='zakat_calculator',
        version='1.0.0',
        description='Calculate Zakat based on Saudi regulations',
        author='Nexus Team',
        requires=[],
        permissions=['accounts.read', 'inventory.read'],
        settings={
            'nisab_threshold': 85000.00,
            'zakat_rate': 0.025,
            'currency': 'SAR',
            'hawl_period_days': 354,
        },
    )

    def register_hooks(self, hook_manager):
        """Register plugin hooks."""
        hook_manager.register('report.generated', self.on_report_generated, priority=5)
        hook_manager.register('system.startup', self.on_startup, once=True)

    def initialize(self, context):
        """Plugin initialization."""
        print(f"Zakat Calculator v{self.config.version} initialized")
        self.nisab = self.get_setting('nisab_threshold')
        self.rate = self.get_setting('zakat_rate')

    def on_report_generated(self, report_data):
        """Add Zakat calculation to financial reports."""
        if report_data.get('type') == 'financial':
            total_assets = report_data.get('total_assets', 0)
            if total_assets >= self.nisab:
                zakat = total_assets * self.rate
                report_data['zakat'] = {
                    'applicable': True,
                    'amount': zakat,
                    'nisab': self.nisab,
                    'rate': self.rate,
                }
            else:
                report_data['zakat'] = {'applicable': False, 'reason': 'Below Nisab'}

    def on_startup(self, *args):
        """One-time startup hook."""
        print("Zakat Calculator registered and ready")

    def calculate_zakat(self, assets: dict) -> dict:
        """Main plugin functionality."""
        total = sum(assets.values())
        return {
            'total_assets': total,
            'nisab_threshold': self.nisab,
            'zakat_applicable': total >= self.nisab,
            'zakat_amount': total * self.rate if total >= self.nisab else 0,
            'currency': self.get_setting('currency'),
        }
