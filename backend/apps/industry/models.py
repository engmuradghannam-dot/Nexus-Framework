"""Industry Verticals Module - 10 Industries"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import Company, Branch
User = get_user_model()

# AVIATION
class Aircraft(models.Model):
    STATUS = [('Active','Active'),('Maintenance','Maintenance'),('Retired','Retired')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='aircraft')
    tail_number = models.CharField(max_length=50, unique=True)
    aircraft_type = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, unique=True)
    year_manufactured = models.PositiveIntegerField()
    total_flight_hours = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_due = models.DateField(null=True, blank=True)
    maintenance_cycle_hours = models.DecimalField(max_digits=8, decimal_places=2, default=500)
    status = models.CharField(max_length=20, choices=STATUS, default='Active')
    seating_capacity = models.PositiveIntegerField(default=0)
    fuel_capacity_liters = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_range_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class FlightSchedule(models.Model):
    STATUS = [('Scheduled','Scheduled'),('Boarding','Boarding'),('Departed','Departed'),('Arrived','Arrived'),('Delayed','Delayed'),('Cancelled','Cancelled')]
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name='flights')
    flight_number = models.CharField(max_length=20)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    actual_departure = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Scheduled')
    gate = models.CharField(max_length=20, blank=True)
    terminal = models.CharField(max_length=20, blank=True)
    available_seats = models.PositiveIntegerField(default=0)
    booked_seats = models.PositiveIntegerField(default=0)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    crew_required = models.JSONField(default=list)
    notes = models.TextField(blank=True)
    class Meta:
        ordering = ['departure_time']

class AircraftMaintenance(models.Model):
    TYPE = [('A-Check','A-Check'),('B-Check','B-Check'),('C-Check','C-Check'),('D-Check','D-Check'),('Line','Line Maintenance'),('Emergency','Emergency')]
    STATUS = [('Scheduled','Scheduled'),('In Progress','In Progress'),('Completed','Completed'),('Overdue','Overdue')]
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=20, choices=TYPE)
    scheduled_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Scheduled')
    description = models.TextField()
    parts_replaced = models.JSONField(default=list, blank=True)
    labor_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    performed_by = models.CharField(max_length=255, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    next_due_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    documents = models.JSONField(default=list, blank=True)

class Ticket(models.Model):
    CLASS = [('Economy','Economy'),('Business','Business'),('First','First')]
    STATUS = [('Booked','Booked'),('Checked-in','Checked-in'),('Boarded','Boarded'),('Flown','Flown'),('Cancelled','Cancelled'),('Refunded','Refunded')]
    flight = models.ForeignKey(FlightSchedule, on_delete=models.CASCADE, related_name='tickets')
    ticket_number = models.CharField(max_length=50, unique=True)
    passenger_name = models.CharField(max_length=255)
    passenger_email = models.EmailField(blank=True)
    passenger_phone = models.CharField(max_length=50, blank=True)
    seat_number = models.CharField(max_length=10, blank=True)
    ticket_class = models.CharField(max_length=20, choices=CLASS, default='Economy')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default='Booked')
    booking_date = models.DateTimeField(auto_now_add=True)
    baggage_allowance_kg = models.DecimalField(max_digits=5, decimal_places=2, default=23)
    special_requests = models.TextField(blank=True)
    pnr = models.CharField(max_length=10, unique=True)

# HEALTHCARE
class Patient(models.Model):
    GENDER = [('Male','Male'),('Female','Female'),('Other','Other')]
    BLOOD = [('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='patients')
    patient_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER)
    blood_type = models.CharField(max_length=5, choices=BLOOD, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=50, blank=True)
    insurance_provider = models.CharField(max_length=255, blank=True)
    insurance_number = models.CharField(max_length=100, blank=True)
    allergies = models.JSONField(default=list, blank=True)
    chronic_conditions = models.JSONField(default=list, blank=True)
    current_medications = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.patient_id} - {self.first_name} {self.last_name}"

class MedicalRecord(models.Model):
    RECORD = [('Consultation','Consultation'),('Lab','Lab Result'),('Imaging','Imaging'),('Surgery','Surgery'),('Prescription','Prescription'),('Discharge','Discharge Summary')]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    record_type = models.CharField(max_length=20, choices=RECORD)
    date = models.DateTimeField()
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='medical_records')
    chief_complaint = models.TextField(blank=True)
    diagnosis = models.TextField()
    treatment = models.TextField(blank=True)
    prescriptions = models.JSONField(default=list, blank=True)
    lab_results = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    attachments = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Appointment(models.Model):
    STATUS = [('Scheduled','Scheduled'),('Confirmed','Confirmed'),('In Progress','In Progress'),('Completed','Completed'),('Cancelled','Cancelled'),('No Show','No Show')]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='doctor_appointments')
    appointment_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    status = models.CharField(max_length=20, choices=STATUS, default='Scheduled')
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    room = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class PharmacyInventory(models.Model):
    CATEGORY = [('Tablet','Tablet'),('Capsule','Capsule'),('Syrup','Syrup'),('Injection','Injection'),('Cream','Cream'),('Equipment','Equipment')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='pharmacy_inventory')
    drug_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY)
    manufacturer = models.CharField(max_length=255, blank=True)
    batch_number = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField()
    quantity_in_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=10)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    storage_conditions = models.CharField(max_length=255, blank=True)
    prescription_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Prescription(models.Model):
    STATUS = [('Active','Active'),('Dispensed','Dispensed'),('Completed','Completed'),('Cancelled','Cancelled')]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    prescription_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Active')
    items = models.JSONField(default=list)
    instructions = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)

# HOTELS
class HotelRoom(models.Model):
    TYPE = [('Standard','Standard'),('Deluxe','Deluxe'),('Suite','Suite'),('Presidential','Presidential'),('Family','Family')]
    STATUS = [('Available','Available'),('Occupied','Occupied'),('Cleaning','Cleaning'),('Maintenance','Maintenance'),('Reserved','Reserved')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='hotel_rooms')
    room_number = models.CharField(max_length=20)
    room_type = models.CharField(max_length=20, choices=TYPE, default='Standard')
    floor = models.PositiveIntegerField(default=1)
    bed_count = models.PositiveIntegerField(default=1)
    max_occupancy = models.PositiveIntegerField(default=2)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amenities = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Available')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        unique_together = ['company', 'room_number']

class Reservation(models.Model):
    STATUS = [('Pending','Pending'),('Confirmed','Confirmed'),('Checked-in','Checked-in'),('Checked-out','Checked-out'),('Cancelled','Cancelled'),('No Show','No Show')]
    room = models.ForeignKey(HotelRoom, on_delete=models.CASCADE, related_name='reservations')
    guest_name = models.CharField(max_length=255)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=50, blank=True)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS, default='Pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    special_requests = models.TextField(blank=True)
    booking_date = models.DateTimeField(auto_now_add=True)
    confirmation_number = models.CharField(max_length=20, unique=True)

# BANKING
class BankAccount(models.Model):
    TYPE = [('Checking','Checking'),('Savings','Savings'),('Loan','Loan'),('Credit','Credit Card'),('Investment','Investment')]
    STATUS = [('Active','Active'),('Frozen','Frozen'),('Closed','Closed'),('Pending','Pending')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bank_accounts')
    account_number = models.CharField(max_length=50, unique=True)
    account_holder = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=TYPE)
    bank_name = models.CharField(max_length=255)
    branch = models.CharField(max_length=255, blank=True)
    swift_code = models.CharField(max_length=20, blank=True)
    iban = models.CharField(max_length=50, blank=True)
    currency = models.CharField(max_length=10, default='USD')
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default='Active')
    opening_date = models.DateField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overdraft_limit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

class BankTransaction(models.Model):
    TYPE = [('Deposit','Deposit'),('Withdrawal','Withdrawal'),('Transfer','Transfer'),('Payment','Payment'),('Fee','Fee'),('Interest','Interest')]
    STATUS = [('Pending','Pending'),('Completed','Completed'),('Failed','Failed'),('Reversed','Reversed')]
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.CharField(max_length=50, unique=True)
    transaction_type = models.CharField(max_length=20, choices=TYPE)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Pending')
    transaction_date = models.DateTimeField()
    counterparty = models.CharField(max_length=255, blank=True)
    counterparty_account = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

# GOVERNMENT
class GovernmentEntity(models.Model):
    TYPE = [('Ministry','Ministry'),('Department','Department'),('Agency','Agency'),('Municipality','Municipality'),('Authority','Authority')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='gov_entities')
    entity_code = models.CharField(max_length=50, unique=True)
    entity_name = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=20, choices=TYPE)
    parent_entity = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    budget_allocation = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

class GovernmentContract(models.Model):
    STATUS = [('Draft','Draft'),('Published','Published'),('Open','Open'),('Closed','Closed'),('Awarded','Awarded'),('Cancelled','Cancelled')]
    entity = models.ForeignKey(GovernmentEntity, on_delete=models.CASCADE, related_name='contracts')
    contract_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    contract_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default='Draft')
    publication_date = models.DateField(null=True, blank=True)
    closing_date = models.DateField(null=True, blank=True)
    award_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    terms = models.TextField(blank=True)
    documents = models.JSONField(default=list, blank=True)
    winning_bidder = models.CharField(max_length=255, blank=True)

# ENERGY
class EnergyAsset(models.Model):
    TYPE = [('Oil Well','Oil Well'),('Gas Field','Gas Field'),('Solar Farm','Solar Farm'),('Wind Farm','Wind Farm'),('Refinery','Refinery'),('Pipeline','Pipeline'),('Storage','Storage Facility'),('Power Plant','Power Plant')]
    STATUS = [('Active','Active'),('Maintenance','Maintenance'),('Decommissioned','Decommissioned')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='energy_assets')
    asset_code = models.CharField(max_length=50, unique=True)
    asset_name = models.CharField(max_length=255)
    asset_type = models.CharField(max_length=20, choices=TYPE)
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    capacity = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    capacity_unit = models.CharField(max_length=20, default='barrels/day')
    commissioning_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS, default='Active')
    operator = models.CharField(max_length=255, blank=True)
    maintenance_schedule = models.JSONField(default=list, blank=True)
    production_data = models.JSONField(default=dict, blank=True)

class EnergyProduction(models.Model):
    asset = models.ForeignKey(EnergyAsset, on_delete=models.CASCADE, related_name='production_records')
    production_date = models.DateField()
    quantity_produced = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, default='barrels')
    efficiency_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    downtime_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    class Meta:
        unique_together = ['asset', 'production_date']

# EDUCATION
class Student(models.Model):
    GENDER = [('Male','Male'),('Female','Female'),('Other','Other')]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='students')
    student_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    enrollment_date = models.DateField()
    program = models.CharField(max_length=255)
    level = models.CharField(max_length=50)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='Active')
    guardian_name = models.CharField(max_length=255, blank=True)
    guardian_phone = models.CharField(max_length=50, blank=True)

class Course(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='courses')
    course_code = models.CharField(max_length=50, unique=True)
    course_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    credits = models.PositiveIntegerField(default=3)
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    semester = models.CharField(max_length=50)
    schedule = models.JSONField(default=dict, blank=True)
    max_students = models.PositiveIntegerField(default=30)
    enrolled_students = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

class Enrollment(models.Model):
    STATUS = [('Enrolled','Enrolled'),('Completed','Completed'),('Dropped','Dropped'),('Failed','Failed')]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Enrolled')
    grade = models.CharField(max_length=5, blank=True)
    grade_points = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
