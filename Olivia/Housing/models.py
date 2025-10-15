from django.db import models
from django.contrib.auth.models import User

# ====================================================================
# Auditing Mixin (Recommended for cleaner code)
# ====================================================================
class AuditModel(models.Model):
    """Abstract base class for auditing fields."""
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=255, blank=True, null=True)
    modified_date = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=255, blank=True, null=True)

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