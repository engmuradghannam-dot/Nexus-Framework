"""Industry Admin"""
from django.contrib import admin
from .models import (
    Aircraft, FlightSchedule, AircraftMaintenance, Ticket,
    Patient, MedicalRecord, Appointment, PharmacyInventory, Prescription,
    HotelRoom, Reservation,
    BankAccount, BankTransaction,
    GovernmentEntity, GovernmentContract,
    EnergyAsset, EnergyProduction,
    Student, Course, Enrollment
)

@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ['tail_number', 'aircraft_type', 'manufacturer', 'status', 'total_flight_hours']
    list_filter = ['status', 'aircraft_type', 'manufacturer']
    search_fields = ['tail_number', 'model', 'serial_number']

@admin.register(FlightSchedule)
class FlightScheduleAdmin(admin.ModelAdmin):
    list_display = ['flight_number', 'origin', 'destination', 'departure_time', 'status']
    list_filter = ['status', 'origin', 'destination']

@admin.register(AircraftMaintenance)
class AircraftMaintenanceAdmin(admin.ModelAdmin):
    list_display = ['aircraft', 'maintenance_type', 'scheduled_date', 'status']
    list_filter = ['maintenance_type', 'status']

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'passenger_name', 'flight', 'ticket_class', 'status']
    list_filter = ['ticket_class', 'status']

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'first_name', 'last_name', 'gender', 'blood_type']
    list_filter = ['gender', 'blood_type']
    search_fields = ['first_name', 'last_name', 'patient_id']

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['patient', 'record_type', 'date', 'doctor']
    list_filter = ['record_type']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'appointment_date', 'status']
    list_filter = ['status']

@admin.register(PharmacyInventory)
class PharmacyInventoryAdmin(admin.ModelAdmin):
    list_display = ['drug_code', 'name', 'category', 'quantity_in_stock', 'expiry_date']
    list_filter = ['category', 'prescription_required']

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'prescription_date', 'status']
    list_filter = ['status']

@admin.register(HotelRoom)
class HotelRoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'room_type', 'floor', 'status', 'price_per_night']
    list_filter = ['room_type', 'status']

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['guest_name', 'room', 'check_in_date', 'check_out_date', 'status']
    list_filter = ['status']

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['account_number', 'account_holder', 'account_type', 'bank_name', 'balance', 'status']
    list_filter = ['account_type', 'status', 'currency']

@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'account', 'transaction_type', 'amount', 'status']
    list_filter = ['transaction_type', 'status']

@admin.register(GovernmentEntity)
class GovernmentEntityAdmin(admin.ModelAdmin):
    list_display = ['entity_code', 'entity_name', 'entity_type', 'is_active']
    list_filter = ['entity_type', 'is_active']

@admin.register(GovernmentContract)
class GovernmentContractAdmin(admin.ModelAdmin):
    list_display = ['contract_number', 'title', 'contract_value', 'status']
    list_filter = ['status']

@admin.register(EnergyAsset)
class EnergyAssetAdmin(admin.ModelAdmin):
    list_display = ['asset_code', 'asset_name', 'asset_type', 'location', 'status']
    list_filter = ['asset_type', 'status']

@admin.register(EnergyProduction)
class EnergyProductionAdmin(admin.ModelAdmin):
    list_display = ['asset', 'production_date', 'quantity_produced', 'efficiency_percentage']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'first_name', 'last_name', 'program', 'level', 'gpa']
    list_filter = ['program', 'level', 'status']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'course_name', 'credits', 'semester', 'is_active']
    list_filter = ['semester', 'is_active']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'enrollment_date', 'status']
    list_filter = ['status']
