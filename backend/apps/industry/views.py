"""Industry Views"""
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import (
    Aircraft, FlightSchedule, AircraftMaintenance, Ticket,
    Patient, MedicalRecord, Appointment, PharmacyInventory, Prescription,
    HotelRoom, Reservation,
    BankAccount, BankTransaction,
    GovernmentEntity, GovernmentContract,
    EnergyAsset, EnergyProduction,
    Student, Course, Enrollment
)
from .serializers import (
    AircraftSerializer, FlightScheduleSerializer, AircraftMaintenanceSerializer, TicketSerializer,
    PatientSerializer, MedicalRecordSerializer, AppointmentSerializer, PharmacyInventorySerializer, PrescriptionSerializer,
    HotelRoomSerializer, ReservationSerializer,
    BankAccountSerializer, BankTransactionSerializer,
    GovernmentEntitySerializer, GovernmentContractSerializer,
    EnergyAssetSerializer, EnergyProductionSerializer,
    StudentSerializer, CourseSerializer, EnrollmentSerializer
)

class AircraftViewSet(viewsets.ModelViewSet):
    queryset = Aircraft.objects.all()
    serializer_class = AircraftSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status', 'aircraft_type', 'manufacturer']
    search_fields = ['tail_number', 'model']

class FlightScheduleViewSet(viewsets.ModelViewSet):
    queryset = FlightSchedule.objects.all()
    serializer_class = FlightScheduleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'origin', 'destination']

class AircraftMaintenanceViewSet(viewsets.ModelViewSet):
    queryset = AircraftMaintenance.objects.all()
    serializer_class = AircraftMaintenanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['maintenance_type', 'status']

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'ticket_class']

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['gender', 'blood_type']
    search_fields = ['first_name', 'last_name', 'patient_id']

class MedicalRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['record_type']

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

class PharmacyInventoryViewSet(viewsets.ModelViewSet):
    queryset = PharmacyInventory.objects.all()
    serializer_class = PharmacyInventorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category', 'prescription_required']
    search_fields = ['name', 'drug_code']

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

class HotelRoomViewSet(viewsets.ModelViewSet):
    queryset = HotelRoom.objects.all()
    serializer_class = HotelRoomSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['room_type', 'status']

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

class BankAccountViewSet(viewsets.ModelViewSet):
    queryset = BankAccount.objects.all()
    serializer_class = BankAccountSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['account_type', 'status', 'currency']

class BankTransactionViewSet(viewsets.ModelViewSet):
    queryset = BankTransaction.objects.all()
    serializer_class = BankTransactionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['transaction_type', 'status']

class GovernmentEntityViewSet(viewsets.ModelViewSet):
    queryset = GovernmentEntity.objects.all()
    serializer_class = GovernmentEntitySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['entity_type']

class GovernmentContractViewSet(viewsets.ModelViewSet):
    queryset = GovernmentContract.objects.all()
    serializer_class = GovernmentContractSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

class EnergyAssetViewSet(viewsets.ModelViewSet):
    queryset = EnergyAsset.objects.all()
    serializer_class = EnergyAssetSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['asset_type', 'status']

class EnergyProductionViewSet(viewsets.ModelViewSet):
    queryset = EnergyProduction.objects.all()
    serializer_class = EnergyProductionSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['gender', 'status']
    search_fields = ['first_name', 'last_name', 'student_id']

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['semester', 'is_active']

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
