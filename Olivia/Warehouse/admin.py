from django.contrib import admin
from .models import (
    Category, UnitOfMeasure, Supplier, Location, Product,
    Receiving, ReceivingItem, Dispatch, DispatchItem,
    Inventory, StockMovement, StockAdjustment,
    MaterialRequisition, MaterialRequisitionItem,
    StockAlert, ClosingStock, ClosingStockItem
)

# Master Data Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_date']
    list_filter = ['is_active']
    search_fields = ['name']

@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ['name', 'abbreviation', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'abbreviation']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'contact_person', 'email']

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'unit', 'reorder_level', 'unit_price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'name']

# Transaction Admin
class ReceivingItemInline(admin.TabularInline):
    model = ReceivingItem
    extra = 1

@admin.register(Receiving)
class ReceivingAdmin(admin.ModelAdmin):
    list_display = ['grn_number', 'date', 'supplier', 'po_number', 'status']
    list_filter = ['status', 'date']
    search_fields = ['grn_number', 'po_number']
    inlines = [ReceivingItemInline]

class DispatchItemInline(admin.TabularInline):
    model = DispatchItem
    extra = 1

@admin.register(Dispatch)
class DispatchAdmin(admin.ModelAdmin):
    list_display = ['dn_number', 'date', 'department', 'requisition_number', 'status']
    list_filter = ['status', 'date']
    search_fields = ['dn_number', 'requisition_number']
    inlines = [DispatchItemInline]

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['product', 'location', 'quantity', 'last_updated']
    list_filter = ['location']
    search_fields = ['product__code', 'product__name']

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['date', 'product', 'movement_type', 'quantity', 'from_location', 'to_location']
    list_filter = ['movement_type', 'date']
    search_fields = ['product__code', 'reference_number']

@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ['adjustment_number', 'date', 'product', 'adjustment_type', 'quantity', 'approved_by']
    list_filter = ['adjustment_type', 'date']
    search_fields = ['adjustment_number', 'product__code']

class MaterialRequisitionItemInline(admin.TabularInline):
    model = MaterialRequisitionItem
    extra = 1

@admin.register(MaterialRequisition)
class MaterialRequisitionAdmin(admin.ModelAdmin):
    list_display = ['mr_number', 'date', 'department', 'requested_by', 'status', 'approved_by']
    list_filter = ['status', 'date']
    search_fields = ['mr_number', 'department']
    inlines = [MaterialRequisitionItemInline]

@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['product', 'current_stock', 'reorder_level', 'status', 'alert_date']
    list_filter = ['status', 'alert_date']
    search_fields = ['product__code', 'product__name']

class ClosingStockItemInline(admin.TabularInline):
    model = ClosingStockItem
    extra = 0

@admin.register(ClosingStock)
class ClosingStockAdmin(admin.ModelAdmin):
    list_display = ['period', 'closing_date', 'status']
    list_filter = ['status', 'closing_date']
    search_fields = ['period']
    inlines = [ClosingStockItemInline]
