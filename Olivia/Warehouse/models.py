from django.db import models
from django.contrib.auth.models import User

# Base Audit Model
class AuditModel(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="%(class)s_created")
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_modified")
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# Master Data Models
class Category(AuditModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class UnitOfMeasure(AuditModel):
    name = models.CharField(max_length=50, unique=True)
    abbreviation = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Unit of Measure"
        verbose_name_plural = "Units of Measure"

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

class Supplier(AuditModel):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Location(AuditModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

class Product(AuditModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def current_stock(self):
        """Get current stock from Inventory"""
        inventory = self.inventory_set.first()
        return inventory.quantity if inventory else 0

    @property
    def is_below_reorder_level(self):
        return self.current_stock < self.reorder_level

# Transaction Models
class Receiving(AuditModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    PURCHASE_TYPE_CHOICES = [
        ('LOCAL', 'Local Purchase'),
        ('HQ', 'Head Quarters'),
    ]
    DEPARTMENT_CHOICES = [
        ('SOFT SERVICE', 'Soft Service'),
        ('HARD SERVICE', 'Hard Service'),
        ('ICT', 'ICT'),
        ('FLS', 'FLS'),
    ]
    date = models.DateField(verbose_name='Receive Date')
    pr_number = models.CharField(max_length=50, blank=True, verbose_name='PR No')
    po_number = models.CharField(max_length=50, blank=True, verbose_name='PO No')
    po_date = models.DateField(null=True, blank=True, verbose_name='PO Date')
    grn_number = models.CharField(max_length=50, verbose_name='GRN No')
    invoice_number = models.CharField(max_length=50, blank=True, verbose_name='Invoice No')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    purchase_type = models.CharField(max_length=20, choices=PURCHASE_TYPE_CHOICES, default='LOCAL', verbose_name='Purchase Type')
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, blank=True, verbose_name='Department')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"GRN-{self.grn_number}"

    @property
    def total_amount(self):
        return sum(item.total_price for item in self.receivingitem_set.all())

class ReceivingItem(AuditModel):
    receiving = models.ForeignKey(Receiving, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True, blank=True)
    item_code = models.CharField(max_length=100, blank=True)
    item_description = models.TextField(blank=True)
    model_number = models.CharField(max_length=100, blank=True, verbose_name='Model No')
    serial_number = models.CharField(max_length=100, blank=True, verbose_name='Serial No')
    country_of_origin = models.CharField(max_length=100, blank=True)
    uom = models.CharField(max_length=50, blank=True, verbose_name='UOM')
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    vat_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='VAT%')
    production_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['id']

    @property
    def total_price(self):
        return self.quantity * self.unit_price
    
    @property
    def subtotal(self):
        return self.quantity * self.unit_price
    
    @property
    def vat_amount(self):
        return self.subtotal * (self.vat_percentage / 100)
    
    @property
    def total(self):
        return self.subtotal + self.vat_amount
    
    @property
    def product_life(self):
        """Calculate product life as today - expiry date (negative means expired)"""
        if self.expiry_date:
            from datetime import date
            delta = self.expiry_date - date.today()
            return delta.days
        return None
    
    @property
    def product_status(self):
        if self.expiry_date:
            from datetime import date
            if self.expiry_date <= date.today():
                return 'Expired'
            return 'Good'
        return 'N/A'

class Dispatch(AuditModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ISSUED', 'Issued'),
        ('CANCELLED', 'Cancelled'),
    ]
    dn_number = models.CharField(max_length=50, unique=True, verbose_name='Delivery No')
    date = models.DateField(verbose_name='Date')
    department = models.CharField(max_length=100)
    requisition_number = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Dispatches"

    def __str__(self):
        return f"DN-{self.dn_number}"

    @property
    def total_amount(self):
        return sum(item.total_price for item in self.dispatchitem_set.all())

class DispatchItem(AuditModel):
    dispatch = models.ForeignKey(Dispatch, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    item_code = models.CharField(max_length=100, blank=True, verbose_name='Item Code')
    item_description = models.TextField(blank=True, verbose_name='Item Description')
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Price')
    staff_id = models.CharField(max_length=50, blank=True, verbose_name='Staff ID')
    staff_name = models.CharField(max_length=200, blank=True, verbose_name='Name')
    staff_department = models.CharField(max_length=100, blank=True, verbose_name='Department')
    brand_name = models.CharField(max_length=100, blank=True, verbose_name='Brand Name')
    serial_number = models.CharField(max_length=100, blank=True, verbose_name='Serial Number')
    country_of_origin = models.CharField(max_length=100, blank=True, verbose_name='Country of Origin')
    
    class Meta:
        ordering = ['id']

    @property
    def total_price(self):
        return self.quantity * self.unit_price

# Inventory Model
class Inventory(AuditModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Inventories"
        unique_together = ['product', 'location']
        ordering = ['product__code']

    def __str__(self):
        return f"{self.product.code} @ {self.location.code}: {self.quantity}"

# Stock Movement
class StockMovement(AuditModel):
    MOVEMENT_TYPES = [
        ('IN', 'Inward'),
        ('OUT', 'Outward'),
        ('TRANSFER', 'Transfer'),
    ]
    date = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    from_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='movements_from', null=True, blank=True)
    to_location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='movements_to')
    reference_number = models.CharField(max_length=50)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.movement_type} - {self.product.code} - {self.quantity}"

# Stock Adjustment
class StockAdjustment(AuditModel):
    ADJUSTMENT_TYPES = [
        ('ADD', 'Addition'),
        ('SUBTRACT', 'Subtraction'),
    ]
    date = models.DateField()
    adjustment_number = models.CharField(max_length=50, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    location = models.ForeignKey(Location, on_delete=models.PROTECT)
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stock_adjustments_approved')

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.adjustment_number} - {self.product.code}"

# Material Requisition
class MaterialRequisition(AuditModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('ISSUED', 'Issued'),
        ('REJECTED', 'Rejected'),
    ]
    mr_number = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    department = models.CharField(max_length=100)
    requested_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='material_requisitions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    remarks = models.TextField(blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='requisitions_approved')
    approved_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"MR-{self.mr_number}"

class MaterialRequisitionItem(AuditModel):
    requisition = models.ForeignKey(MaterialRequisition, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    requested_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    issued_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.requisition.mr_number} - {self.product.code}"

# Stock Alert
class StockAlert(AuditModel):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('RESOLVED', 'Resolved'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    alert_date = models.DateTimeField(auto_now_add=True)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    resolved_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-alert_date']

    def __str__(self):
        return f"Alert: {self.product.code} - Stock: {self.current_stock}"

# Closing Stock
class ClosingStock(AuditModel):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    ]
    period = models.CharField(max_length=50)  # e.g., "2024-01" or "Q1-2024"
    closing_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')

    class Meta:
        ordering = ['-closing_date']

    def __str__(self):
        return f"Closing Stock - {self.period}"

class ClosingStockItem(AuditModel):
    closing_stock = models.ForeignKey(ClosingStock, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True, blank=True)
    item_code = models.CharField(max_length=50, blank=True, verbose_name='Item Code')
    item_description = models.CharField(max_length=255, blank=True, verbose_name='Item Description')
    uom = models.CharField(max_length=20, blank=True, verbose_name='UOM')
    location = models.ForeignKey(Location, on_delete=models.PROTECT, verbose_name='Storage Location')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Quantity')
    min_inventory = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Min Inventory')
    max_capacity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Max Capacity')
    po_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='PO Quantity')
    opening_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    received_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    issued_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    adjustment_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['product__code']
        unique_together = ['closing_stock', 'product', 'location']

    @property
    def closing_quantity(self):
        return self.opening_quantity + self.received_quantity - self.issued_quantity + self.adjustment_quantity

    @property
    def total_value(self):
        return self.closing_quantity * self.unit_price

    def __str__(self):
        return f"{self.closing_stock.period} - {self.product.code}"
