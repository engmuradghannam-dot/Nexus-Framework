from django.contrib import admin
from .models import User, Company, Branch, Warehouse

admin.site.register(User)
admin.site.register(Company)
admin.site.register(Branch)
admin.site.register(Warehouse)
