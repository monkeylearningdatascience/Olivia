from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django_countries.fields import CountryField  

# ====================================================================
# Auditing Mixin (Recommended for cleaner code)
# ====================================================================
class AuditModel(models.Model):
    """Abstract base class for auditing fields."""
    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)s_created')
    modified_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)s_modified')

    class Meta:
        abstract = True


# ====================================================================
# NEW MODEL: CompanyGroup
# ====================================================================
class CompanyGroup(AuditModel): # Inherits AuditModel
    """
    Stores the names of various company groups.
    """
    company_name = models.CharField(
        max_length=255, 
        unique=True, 
        verbose_name="Company Group Name"
    )

    class Meta:
        verbose_name = "Company Group"
        verbose_name_plural = "Company Groups"
        ordering = ['company_name']

    def __str__(self):
        return self.company_name


# ====================================================================
# NEW MODEL: UserCompany
# ====================================================================
class UserCompany(AuditModel): # Inherits AuditModel
    """
    Stores detailed information for a specific company, linked to a group.
    """
    company_name = models.CharField(max_length=255, verbose_name="Company Name")
    
    company_group = models.ForeignKey(
        CompanyGroup,
        on_delete=models.SET_NULL,  # Good practice: don't delete companies if a group is deleted
        null=True,
        blank=True,
        verbose_name="Company Group"
    )
    
    company_details = models.TextField(blank=True, verbose_name="Company Details")
    cr_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="CR Number")
    vat_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="VAT Number")
    address_text = models.TextField(blank=True, verbose_name="Address")
    contact_name = models.CharField(max_length=255, blank=True, verbose_name="Contact Name")
    email_address = models.EmailField(max_length=255, blank=True, verbose_name="Email Address")
    mobile = models.CharField(max_length=20, blank=True, verbose_name="Mobile")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Phone")

    # *** FINAL FIX: Explicitly assign the default manager ***
    objects = models.Manager() 

    class Meta:
        verbose_name = "User Company"
        verbose_name_plural = "User Companies"
        ordering = ['company_group']

    def __str__(self):
        return self.company_name
    
# ====================================================================
# Unit Model (Updated to inherit AuditModel)
# ====================================================================
class Unit(AuditModel): # CHANGED: Inherit AuditModel instead of models.Model
    # Choices (kept for context)
    BED_NUMBER_CHOICES = [(str(i), str(i)) for i in range(1, 5)]
    ZONE_CHOICES = [
        ("NZ", "NZ"),
        ("CZ", "CZ"),
        ("FZ", "FZ"),
    ]
    ACCOMMODATION_TYPE_CHOICES = [
        ("A (1 * 1)", "A (1 * 1)"),
        ("B (1 * 1)", "B (1 * 1)"),
        ("C (2 * 1)", "C (2 * 1)"),
        ("D (4 * 1)", "D (4 * 1)"),
    ]
    SEPARABLE_CHOICES = [(f"SP{i}", f"SP{i}") for i in range(1, 6)]
    WAVE_CHOICES = [(f"Wave {i}", f"Wave {i}") for i in range(1, 20)] + [
        ("FM Wave 1", "FM Wave 1"),
        ("FM Wave 2", "FM Wave 2"),
    ]
    AREA_CHOICES = [
        ("NA1", "NA1"), ("NB1", "NB1"), ("NB2", "NB2"),
        ("CA1", "CA1"), ("CA2", "CA2"),
        ("CB1", "CB1"), ("CB2", "CB2"), ("CB3", "CB3"), ("CB4", "CB4"), ("CB5", "CB5"), ("CB6", "CB6"), ("CB7", "CB7"),
        ("CC1", "CC1"), ("CC2", "CC2"), ("CC3", "CC3"), ("CC4", "CC4"),
        ("CD1", "CD1"), ("CD2", "CD2"), ("CD3", "CD3"), ("CD4", "CD4"), ("CD5", "CD5"), ("CD6", "CD6"),
        ("FMA1", "FMA1"), ("FMB1", "FMB1"), ("FMC1", "FMC1"), ("FMD1", "FMD1"),
    ]
    BLOCK_CHOICES = [(f"Blk{i}", f"Blk{i}") for i in range(1, 10)]
    BUILDING_CHOICES = [(f"Bld{i}", f"Bld{i}") for i in range(1, 5)]
    FLOOR_CHOICES = [
        ("GF", "GF"),
        ("FF", "FF"),
        ("SF", "SF"),
    ]
    ROOM_UTILIZATION_TYPE_CHOICES = [
        ("Commercial", "Commercial"),
        ("Non-Commercial (DBFOM)", "Non-Commercial (DBFOM)"),
        ("Non-Commercial (FM)", "Non-Commercial (FM)"),
    ]
    ACTUAL_TYPE_CHOICES = [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]
    CURRENT_TYPE_CHOICES = [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]
    OCCUPANCY_STATUS_CHOICES = [
        ("Assigned", "Assigned"),
        ("Hold", "Hold"),
        ("Occupied", "Occupied"),
        ("Out of Order", "Out of Order"),
        ("To be Received", "To be Received"),
        ("Vacant Dirty", "Vacant Dirty"),
        ("Vacant Ready", "Vacant Ready"),
    ]
    ROOM_PHYSICAL_STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    ]

    # Fields
    unit_number = models.CharField(max_length=50)
    bed_number = models.CharField(max_length=50, choices=BED_NUMBER_CHOICES, blank=True, null=True)
    unit_location = models.CharField(max_length=255, blank=True, null=True, editable=False)  # auto-generated
    zone = models.CharField(max_length=100, choices=ZONE_CHOICES, blank=True, null=True)
    accomodation_type = models.CharField(max_length=100, choices=ACCOMMODATION_TYPE_CHOICES, blank=True, null=True)
    separable = models.CharField(max_length=100, choices=SEPARABLE_CHOICES, blank=True, null=True)
    wave = models.CharField(max_length=100, choices=WAVE_CHOICES, blank=True, null=True)
    area = models.CharField(max_length=100, choices=AREA_CHOICES, blank=True, null=True)
    block = models.CharField(max_length=100, choices=BLOCK_CHOICES, blank=True, null=True)
    building = models.CharField(max_length=100, choices=BUILDING_CHOICES, blank=True, null=True)
    floor = models.CharField(max_length=100, choices=FLOOR_CHOICES, blank=True, null=True)
    room_utilization_type = models.CharField(max_length=100, choices=ROOM_UTILIZATION_TYPE_CHOICES, blank=True, null=True)
    actual_type = models.CharField(max_length=100, choices=ACTUAL_TYPE_CHOICES, blank=True, null=True)
    current_type = models.CharField(max_length=100, choices=CURRENT_TYPE_CHOICES, blank=True, null=True)
    occupancy_status = models.CharField(max_length=100, choices=OCCUPANCY_STATUS_CHOICES, blank=True, null=True)
    room_physical_status = models.CharField(max_length=100, choices=ROOM_PHYSICAL_STATUS_CHOICES, blank=True, null=True)


    def save(self, *args, **kwargs):
        """Auto-generate unit_location from Area - Block - Building - Floor"""
        parts = [self.area, self.block, self.building, self.floor]
        self.unit_location = " - ".join([p for p in parts if p])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unit_number} - {self.unit_location}"
    
# ====================================================================
class HousingUser(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Pending', 'Pending'),
    ]
    RELIGION_CHOICES = [
        ('Muslim', 'Muslim'),
        ('Non Muslim', 'Non Muslim'),
    ]

    username = models.CharField(max_length=100)

    group = models.ForeignKey('CompanyGroup', on_delete=models.SET_NULL, null=True, related_name='users_in_group')
    company = models.ForeignKey('UserCompany', on_delete=models.SET_NULL, null=True, related_name='users_in_company')

    government_id = models.CharField(max_length=50, blank=True, null=True)
    id_type = models.CharField(max_length=50, blank=True, null=True)
    neom_id = models.CharField(max_length=50, blank=True, null=True)

    dob = models.DateField(null=True, blank=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    nationality = CountryField(blank_label='(Select Nationality)', null=True, blank=True)

    religion = models.CharField(max_length=20, choices=RELIGION_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_housingusers')
    modified_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modified_housingusers')

    def __str__(self):
        return self.username


class UnitAllocation(AuditModel):
    """Tracks allocation of housing units to companies with room/bed capacity"""
    ALLOCATION_TYPE_CHOICES = [
        ('UUA', 'UUA'),
        ('Non UUA', 'Non UUA'),
    ]
    
    ALLOCATION_STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Closed', 'Closed'),
        ('Revised', 'Revised'),
        ('Extended', 'Extended'),
        ('Cancelled', 'Cancelled'),
    ]
    
    allocation_type = models.CharField(max_length=20, choices=ALLOCATION_TYPE_CHOICES)
    uua_number = models.CharField(max_length=50, unique=True, verbose_name="UUA Number")
    company_group = models.ForeignKey(CompanyGroup, on_delete=models.CASCADE, related_name='allocations')
    company = models.ForeignKey(UserCompany, on_delete=models.CASCADE, related_name='allocations')
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Format: "rooms/beds" e.g. "2/4" means 2 rooms, 4 beds
    a_rooms_beds = models.CharField(max_length=20, verbose_name="A (Rooms/Beds)", blank=True)
    b_rooms_beds = models.CharField(max_length=20, verbose_name="B (Rooms/Beds)", blank=True)
    c_rooms_beds = models.CharField(max_length=20, verbose_name="C (Rooms/Beds)", blank=True)
    d_rooms_beds = models.CharField(max_length=20, verbose_name="D (Rooms/Beds)", blank=True)
    total_rooms_beds = models.CharField(max_length=20, verbose_name="Total (Rooms/Beds)", blank=True)
    
    allocation_status = models.CharField(max_length=20, choices=ALLOCATION_STATUS_CHOICES, default='Active')
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def calculate_total_rooms_beds(self):
        """Calculate total rooms and beds from A/B/C/D entries"""
        total_rooms = 0
        total_beds = 0
        
        for field in [self.a_rooms_beds, self.b_rooms_beds, self.c_rooms_beds, self.d_rooms_beds]:
            if field and '/' in field:
                rooms, beds = field.split('/')
                total_rooms += int(rooms) if rooms.strip().isdigit() else 0
                total_beds += int(beds) if beds.strip().isdigit() else 0
        
        return f"{total_rooms}/{total_beds}"
    
    def save(self, *args, **kwargs):
        self.total_rooms_beds = self.calculate_total_rooms_beds()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_date']
        verbose_name = "Unit Allocation"
        verbose_name_plural = "Unit Allocations"
    
    def __str__(self):
        return f"{self.uua_number} - {self.company.company_name}"


class UnitAssignment(AuditModel):
    """Links specific units to allocations with accommodation type"""
    ACCOMMODATION_TYPE_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]
    
    allocation = models.ForeignKey(UnitAllocation, on_delete=models.CASCADE, related_name='unit_assignments')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='assignments')
    accommodation_type = models.CharField(max_length=1, choices=ACCOMMODATION_TYPE_CHOICES)
    
    class Meta:
        ordering = ['-created_date']
        verbose_name = "Unit Assignment"
        verbose_name_plural = "Unit Assignments"
        unique_together = [['allocation', 'unit', 'accommodation_type']]
    
    def __str__(self):
        return f"{self.unit.unit_number} - {self.accommodation_type} ({self.allocation.uua_number})"


class Reservation(AuditModel):
    """Tracks reservation of housing users to assigned units"""
    OCCUPANCY_STATUS_CHOICES = [
        ('Reserved', 'Reserved'),
        ('Hold', 'Hold'),
        ('Assigned', 'Assigned'),
        ('Occupied', 'Occupied'),
        ('Checked In', 'Checked In'),
        ('Checked Out', 'Checked Out'),
    ]
    
    # From Assignment
    assignment = models.ForeignKey(UnitAssignment, on_delete=models.CASCADE, related_name='reservations')
    allocation_type = models.CharField(max_length=255, blank=True)
    uua_number = models.CharField(max_length=255, blank=True)
    company_group = models.ForeignKey(CompanyGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    company = models.ForeignKey(UserCompany, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    accomodation_type = models.CharField(max_length=50, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    unit_location_code = models.CharField(max_length=255, blank=True)
    
    # From Housing User
    housing_user = models.ForeignKey(HousingUser, on_delete=models.CASCADE, related_name='reservations')
    govt_id_number = models.CharField(max_length=255, blank=True)
    id_type = models.CharField(max_length=50, blank=True)
    neom_id = models.CharField(max_length=255, blank=True)
    dob = models.DateField(null=True, blank=True)
    mobile_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    nationality = CountryField(blank=True)
    religion = models.CharField(max_length=50, blank=True)
    
    # Reservation Specific
    intended_checkin_date = models.DateField()
    intended_checkout_date = models.DateField()
    intended_stay_duration = models.IntegerField(help_text="Duration in days", null=True, blank=True)
    
    occupancy_status = models.CharField(max_length=20, choices=OCCUPANCY_STATUS_CHOICES, default='Reserved')
    remarks = models.TextField(blank=True)
    
    def calculate_duration(self):
        """Calculate duration in days between intended check-in and check-out"""
        if self.intended_checkin_date and self.intended_checkout_date:
            delta = self.intended_checkout_date - self.intended_checkin_date
            return delta.days
        return 0
    
    def save(self, *args, **kwargs):
        self.intended_stay_duration = self.calculate_duration()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_date']
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
    
    def __str__(self):
        return f"{self.housing_user.username} - {self.unit.unit_number if self.unit else 'No Unit'}"


class CheckInCheckOut(AuditModel):
    """Tracks actual check-in and check-out with datetime stamps"""
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='checkins')
    
    actual_checkin_datetime = models.DateTimeField(null=True, blank=True)
    actual_checkout_datetime = models.DateTimeField(null=True, blank=True)
    actual_stay_duration = models.IntegerField(help_text="Duration in days", null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    
    def calculate_actual_duration(self):
        """Calculate actual duration in days between check-in and check-out"""
        if self.actual_checkin_datetime and self.actual_checkout_datetime:
            delta = self.actual_checkout_datetime - self.actual_checkin_datetime
            return delta.days
        return 0
    
    def save(self, *args, **kwargs):
        if self.actual_checkin_datetime and self.actual_checkout_datetime:
            self.actual_stay_duration = self.calculate_actual_duration()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created_date']
        verbose_name = "Check-In/Check-Out"
        verbose_name_plural = "Check-Ins/Check-Outs"
    
    def __str__(self):
        return f"{self.reservation.housing_user.username} - Check-In/Out"
