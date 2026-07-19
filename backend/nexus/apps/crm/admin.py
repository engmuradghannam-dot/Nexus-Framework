from django.contrib import admin

from .models import Contact, Customer, CustomerInteraction, Opportunity

admin.site.register(Customer)
admin.site.register(Contact)
admin.site.register(CustomerInteraction)
admin.site.register(Opportunity)
