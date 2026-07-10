from django.contrib import admin

from .models import Asset, AssetCategory

admin.site.register(AssetCategory)
admin.site.register(Asset)
