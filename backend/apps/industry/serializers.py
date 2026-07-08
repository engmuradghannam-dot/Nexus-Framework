"""Industry Serializers"""
from rest_framework import serializers
from .models import (
    Aircraft, FlightSchedule, AircraftMaintenance, Ticket,
    Patient, MedicalRecord, Appointment, PharmacyInventory, Prescription,
    HotelRoom, Reservation,
    BankAccount, BankTransaction,
    GovernmentEntity, GovernmentContract,
    EnergyAsset, EnergyProduction,
    Student, Course, Enrollment
)

class AircraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aircraft
        fields = '__all__'

class FlightScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightSchedule
        fields = '__all__'

class AircraftMaintenanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AircraftMaintenance
        fields = '__all__'

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'

class PharmacyInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacyInventory
        fields = '__all__'

class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = '__all__'

class HotelRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotelRoom
        fields = '__all__'

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = '__all__'

class BankTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankTransaction
        fields = '__all__'

class GovernmentEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = GovernmentEntity
        fields = '__all__'

class GovernmentContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = GovernmentContract
        fields = '__all__'

class EnergyAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnergyAsset
        fields = '__all__'

class EnergyProductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnergyProduction
        fields = '__all__'

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = '__all__'
