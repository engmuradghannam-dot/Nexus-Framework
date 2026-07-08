"""Industry URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AircraftViewSet, FlightScheduleViewSet, AircraftMaintenanceViewSet, TicketViewSet,
    PatientViewSet, MedicalRecordViewSet, AppointmentViewSet, PharmacyInventoryViewSet, PrescriptionViewSet,
    HotelRoomViewSet, ReservationViewSet,
    BankAccountViewSet, BankTransactionViewSet,
    GovernmentEntityViewSet, GovernmentContractViewSet,
    EnergyAssetViewSet, EnergyProductionViewSet,
    StudentViewSet, CourseViewSet, EnrollmentViewSet
)

router = DefaultRouter()
router.register(r'aircraft', AircraftViewSet)
router.register(r'flight-schedules', FlightScheduleViewSet)
router.register(r'aircraft-maintenance', AircraftMaintenanceViewSet)
router.register(r'tickets', TicketViewSet)
router.register(r'patients', PatientViewSet)
router.register(r'medical-records', MedicalRecordViewSet)
router.register(r'appointments', AppointmentViewSet)
router.register(r'pharmacy-inventory', PharmacyInventoryViewSet)
router.register(r'prescriptions', PrescriptionViewSet)
router.register(r'hotel-rooms', HotelRoomViewSet)
router.register(r'reservations', ReservationViewSet)
router.register(r'bank-accounts', BankAccountViewSet)
router.register(r'bank-transactions', BankTransactionViewSet)
router.register(r'government-entities', GovernmentEntityViewSet)
router.register(r'government-contracts', GovernmentContractViewSet)
router.register(r'energy-assets', EnergyAssetViewSet)
router.register(r'energy-production', EnergyProductionViewSet)
router.register(r'students', StudentViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'enrollments', EnrollmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
