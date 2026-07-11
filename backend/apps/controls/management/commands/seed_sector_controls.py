"""Seed sector-specific controls/entities for the company-setup flow.

Idempotent. Each sector maps to the business entities that matter for it,
so selecting a sector during company setup reveals the right controls
(e.g. Hospitality -> Rooms, Bookings, Guests).
"""
from django.core.management.base import BaseCommand

from apps.controls.models import SectorControl

# sector -> list of (entity, description, [fields], module, icon)
SECTOR_CONTROLS = {
    "Hospitality": [
        ("Rooms", "Room inventory and status", ["Room Number", "Room Type", "Floor", "Status", "Rate/Night", "Capacity"], "Front Office", "bed"),
        ("Room Types", "Categories of rooms", ["Name", "Base Rate", "Max Occupancy", "Amenities"], "Front Office", "layout-grid"),
        ("Bookings", "Reservations and stays", ["Booking No", "Guest", "Room", "Check-in Date", "Check-out Date", "Status", "Total"], "Reservations", "calendar-check"),
        ("Guests", "Guest profiles", ["Name", "ID/Passport", "Phone", "Email", "Nationality", "VIP"], "Front Office", "user"),
        ("Rate Plans", "Seasonal and package rates", ["Plan Name", "Season", "Rate", "Valid From", "Valid To"], "Revenue", "tag"),
        ("Housekeeping", "Room cleaning tasks", ["Room", "Status", "Assigned To", "Priority", "Notes"], "Operations", "sparkles"),
    ],
    "Healthcare": [
        ("Patients", "Patient records", ["MRN", "Name", "DOB", "Gender", "Phone", "Blood Type", "Insurance"], "Clinical", "user"),
        ("Appointments", "Scheduled visits", ["Appointment No", "Patient", "Doctor", "Date", "Time", "Department", "Status"], "Scheduling", "calendar-clock"),
        ("Doctors", "Medical staff", ["Name", "Specialty", "License No", "Department", "Availability"], "Staff", "stethoscope"),
        ("Medical Records", "Diagnoses and history", ["Patient", "Visit Date", "Diagnosis", "Notes", "Attachments"], "Clinical", "file-text"),
        ("Prescriptions", "Medication orders", ["Patient", "Medication", "Dosage", "Duration", "Prescribed By"], "Pharmacy", "pill"),
        ("Wards / Beds", "Inpatient capacity", ["Ward", "Bed No", "Status", "Patient", "Department"], "Inpatient", "bed"),
        ("Billing", "Invoices and claims", ["Invoice No", "Patient", "Amount", "Insurance", "Status"], "Finance", "receipt"),
    ],
    "Manufacturing": [
        ("Bill of Materials", "Product component structure", ["Product", "Component", "Quantity", "UoM", "Cost"], "Production", "layers"),
        ("Work Orders", "Production orders", ["MO No", "Product", "Quantity", "Due Date", "Status", "Progress"], "Production", "factory"),
        ("Production Lines", "Manufacturing lines", ["Line", "Capacity", "Status", "Current Order"], "Production", "cog"),
        ("Raw Materials", "Input inventory", ["Material", "Stock", "UoM", "Reorder Level", "Supplier"], "Inventory", "package"),
        ("Quality Control", "Inspections and checks", ["Order", "Check", "Result", "Inspector", "Date"], "Quality", "check-circle"),
        ("Machines", "Equipment and maintenance", ["Machine", "Type", "Status", "Last Maintenance"], "Maintenance", "settings"),
    ],
    "Retail": [
        ("Products", "Sellable items", ["SKU", "Name", "Category", "Price", "Stock", "Barcode"], "Catalog", "package"),
        ("Point of Sale", "Sales transactions", ["Receipt No", "Cashier", "Items", "Total", "Payment", "Date"], "Sales", "shopping-cart"),
        ("Inventory", "Stock across stores", ["Product", "Store", "On Hand", "Reserved", "Reorder Level"], "Inventory", "boxes"),
        ("Promotions", "Discounts and offers", ["Name", "Type", "Value", "Start", "End", "Products"], "Marketing", "tag"),
        ("Loyalty", "Customer rewards", ["Member", "Points", "Tier", "Since"], "CRM", "star"),
        ("Stores", "Retail locations", ["Store", "Location", "Manager", "Status"], "Operations", "store"),
    ],
    "Aviation": [
        ("Flights", "Flight schedule", ["Flight No", "Origin", "Destination", "Departure", "Arrival", "Aircraft", "Status"], "Operations", "plane"),
        ("Aircraft", "Fleet management", ["Registration", "Model", "Capacity", "Status", "Last Check"], "Fleet", "plane"),
        ("Bookings", "Passenger reservations", ["PNR", "Passenger", "Flight", "Seat", "Class", "Status"], "Reservations", "ticket"),
        ("Crew", "Flight crew", ["Name", "Role", "License", "Base", "Availability"], "Staff", "users"),
        ("Schedules", "Route timetables", ["Route", "Frequency", "Departure", "Duration"], "Planning", "calendar"),
    ],
    "Education": [
        ("Students", "Student records", ["Student ID", "Name", "Grade/Level", "Guardian", "Status"], "Academic", "user"),
        ("Courses", "Offered courses", ["Code", "Name", "Credits", "Instructor", "Term"], "Academic", "book"),
        ("Enrollment", "Course registration", ["Student", "Course", "Term", "Status"], "Academic", "clipboard"),
        ("Attendance", "Class attendance", ["Student", "Course", "Date", "Status"], "Academic", "check-square"),
        ("Grades", "Assessment results", ["Student", "Course", "Assessment", "Score", "Grade"], "Academic", "award"),
    ],
    "Real Estate": [
        ("Properties", "Property portfolio", ["Property", "Type", "Location", "Area", "Status", "Value"], "Assets", "building"),
        ("Units", "Rentable units", ["Unit", "Property", "Type", "Area", "Rent", "Status"], "Assets", "home"),
        ("Leases", "Rental contracts", ["Lease No", "Unit", "Tenant", "Start", "End", "Rent", "Status"], "Leasing", "file-text"),
        ("Tenants", "Tenant profiles", ["Name", "ID", "Phone", "Unit", "Balance"], "Leasing", "user"),
        ("Maintenance", "Property maintenance", ["Property/Unit", "Issue", "Priority", "Assigned", "Status"], "Operations", "wrench"),
    ],
    "Restaurant": [
        ("Menu Items", "Dishes and pricing", ["Item", "Category", "Price", "Cost", "Available"], "Menu", "utensils"),
        ("Tables", "Dining tables", ["Table No", "Capacity", "Section", "Status"], "Front", "grid"),
        ("Orders", "Customer orders", ["Order No", "Table", "Items", "Total", "Status", "Time"], "Service", "clipboard-list"),
        ("Reservations", "Table bookings", ["Name", "Date", "Time", "Guests", "Table", "Status"], "Front", "calendar-check"),
        ("Kitchen", "Kitchen tickets (KDS)", ["Order", "Items", "Station", "Status", "Time"], "Kitchen", "chef-hat"),
    ],
    "Logistics": [
        ("Shipments", "Freight and parcels", ["Tracking No", "Origin", "Destination", "Status", "ETA"], "Operations", "truck"),
        ("Fleet", "Vehicles", ["Vehicle", "Type", "Driver", "Status", "Location"], "Fleet", "truck"),
        ("Routes", "Delivery routes", ["Route", "Stops", "Distance", "Driver", "Status"], "Planning", "map"),
        ("Deliveries", "Delivery jobs", ["Job No", "Customer", "Address", "Status", "Delivered At"], "Operations", "package-check"),
    ],
    "Construction": [
        ("Projects", "Construction projects", ["Project", "Client", "Location", "Budget", "Progress", "Status"], "Projects", "hard-hat"),
        ("Sites", "Work sites", ["Site", "Project", "Location", "Supervisor", "Status"], "Operations", "map-pin"),
        ("Contractors", "Subcontractors", ["Name", "Trade", "Contract Value", "Status"], "Procurement", "users"),
        ("Materials", "Site materials", ["Material", "Quantity", "UoM", "Supplier", "Cost"], "Inventory", "package"),
        ("Progress", "Milestone tracking", ["Project", "Milestone", "Planned", "Actual", "Status"], "Projects", "trending-up"),
    ],
}


class Command(BaseCommand):
    help = "Seed sector-specific controls (idempotent)."

    def handle(self, *args, **options):
        n = 0
        for sector, entities in SECTOR_CONTROLS.items():
            for order, (entity, desc, fields, module, icon) in enumerate(entities):
                SectorControl.objects.update_or_create(
                    sector=sector,
                    entity=entity,
                    defaults={
                        "description": desc,
                        "fields": fields,
                        "module": module,
                        "icon": icon,
                        "order": order,
                    },
                )
                n += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Sector controls seeded: {n} entries across "
                f"{len(SECTOR_CONTROLS)} sectors"
            )
        )
