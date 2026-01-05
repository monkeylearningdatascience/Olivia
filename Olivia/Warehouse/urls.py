from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path('', views.home, name="warehouse_home"),
    path('receiving/', views.receiving_list, name='receiving'),
    path('dispatch/', views.dispatch_list, name='dispatch'),
    path('closing-stock/', views.closing_stock_list, name='closing_stock'),
    path('inventory/', views.inventory_list, name='inventory'),
    path('stock-movement/', views.stock_movement_list, name='stock_movement'),
    path('stock-adjustment/', views.stock_adjustment_list, name='stock_adjustment'),
    path('stock-alert/', views.stock_alert_list, name='stock_alert'),
    path('material-requisition/', views.material_requisition_list, name='material_requisition'),
    path('label-generator/', views.label_generator, name='label_generator'),
    
    # API endpoints for Receiving
    path('api/receiving/list/', api_views.api_receiving_list, name='api_receiving_list'),
    path('api/receiving/create/', api_views.api_receiving_create, name='api_receiving_create'),
    path('api/receiving/detail/<int:pk>/', api_views.api_receiving_detail, name='api_receiving_detail'),
    path('api/receiving/update/<int:pk>/', api_views.api_receiving_update, name='api_receiving_update'),
    path('api/receiving/delete/', api_views.api_receiving_delete, name='api_receiving_delete'),
    path('api/receiving/import/', api_views.api_receiving_import, name='api_receiving_import'),
    path('api/receiving/export/', api_views.api_receiving_export, name='api_receiving_export'),
    
    # API endpoints for Material Requisition
    path('api/requisition/list/', api_views.api_requisition_list, name='api_requisition_list'),
    path('api/requisition/create/', api_views.api_requisition_create, name='api_requisition_create'),
    path('api/requisition/detail/<int:pk>/', api_views.api_requisition_detail, name='api_requisition_detail'),
    path('api/requisition/update/<int:pk>/', api_views.api_requisition_update, name='api_requisition_update'),
    path('api/requisition/delete/', api_views.api_requisition_delete, name='api_requisition_delete'),
    path('api/requisition/export/', api_views.api_requisition_export, name='api_requisition_export'),
    path('api/products/list/', api_views.api_products_list, name='api_products_list'),
]