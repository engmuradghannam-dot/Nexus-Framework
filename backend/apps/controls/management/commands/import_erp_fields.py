"""Import the ERP template form inputs into the FormControl library (idempotent).

Mirrors Nexus_ERP_Template.xlsx so the Controls Library reflects each module's
inputs, including bilingual (Arabic/English) name fields.
"""
from django.core.management.base import BaseCommand

from apps.controls.models import FormControl

# form_name -> list of (input_name, input_type)
ERP_FORMS = {
    "Supplier Master": [
        ("Supplier Code", "Text"), ("Supplier Name", "Text"), ("Arabic Name", "Text"),
        ("CR Number", "Text"), ("VAT Number", "Text"), ("Country", "Select"),
        ("City", "Text"), ("Address", "TextArea"), ("Phone", "Text"), ("Email", "Email"),
        ("Currency", "Select"), ("Payment Terms", "Text"), ("Credit Limit", "Number"),
        ("Bank", "Text"), ("IBAN", "Text"), ("Category", "Text"), ("Status", "Select"),
        ("Risk Level", "Select"), ("Preferred Supplier", "Checkbox"), ("Notes", "TextArea"),
    ],
    "Purchase Requisition": [
        ("PR No", "Text"), ("Date", "Date"), ("Department", "Text"), ("Requester", "Text"),
        ("Cost Center", "Text"), ("Project", "Text"), ("Priority", "Select"),
        ("Required Date", "Date"), ("Status", "Select"), ("Remarks", "TextArea"),
    ],
    "Purchase Order": [
        ("PO No", "Text"), ("Supplier", "Select"), ("PR No", "Text"), ("Currency", "Select"),
        ("Payment Terms", "Text"), ("Delivery Date", "Date"), ("Buyer", "Text"),
        ("Status", "Select"), ("Total", "Number"),
    ],
    "Inventory Items": [
        ("Item Code", "Text"), ("SKU", "Text"), ("Arabic Name", "Text"), ("English Name", "Text"),
        ("Category", "Text"), ("Unit", "Text"), ("Cost", "Number"), ("Selling Price", "Number"),
        ("Min Stock", "Number"), ("Max Stock", "Number"), ("Warehouse", "Select"),
    ],
    "Warehouse": [
        ("Warehouse Code", "Text"), ("Warehouse Name", "Text"), ("Branch", "Select"),
        ("Manager", "Text"), ("Location", "Text"), ("Capacity", "Number"), ("Status", "Select"),
    ],
    "CRM Customers": [
        ("Customer Code", "Text"), ("Customer Name", "Text"), ("Type", "Select"),
        ("Phone", "Text"), ("Email", "Email"), ("City", "Text"), ("Country", "Select"),
        ("Salesperson", "Text"), ("Credit Limit", "Number"), ("Status", "Select"),
    ],
    "Sales Orders": [
        ("SO No", "Text"), ("Customer", "Select"), ("Date", "Date"), ("Currency", "Select"),
        ("Warehouse", "Select"), ("Salesperson", "Text"), ("Status", "Select"), ("Total", "Number"),
    ],
    "HR Employees": [
        ("Employee No", "Text"), ("Name", "Text"), ("Department", "Select"), ("Position", "Text"),
        ("Hire Date", "Date"), ("Nationality", "Text"), ("Manager", "Text"), ("Status", "Select"),
    ],
    "Assets": [
        ("Asset Code", "Text"), ("Asset Name", "Text"), ("Category", "Text"),
        ("Purchase Date", "Date"), ("Cost", "Number"), ("Location", "Text"),
        ("Custodian", "Text"), ("Status", "Select"),
    ],
}


class Command(BaseCommand):
    help = "Import ERP template form inputs into the Controls Library (idempotent)."

    def handle(self, *args, **options):
        n = 0
        for form_name, inputs in ERP_FORMS.items():
            for seq, (input_name, input_type) in enumerate(inputs):
                FormControl.objects.update_or_create(
                    form_name=form_name,
                    input_name=input_name,
                    defaults={
                        "seq": seq,
                        "input_type": input_type,
                        "status": FormControl.STATUS_PRESENT,
                        "priority": "Medium",
                    },
                )
                n += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"ERP form inputs imported: {n} inputs across {len(ERP_FORMS)} forms"
            )
        )
