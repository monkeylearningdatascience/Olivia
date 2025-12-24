from django.urls import path
from . import views

urlpatterns = [
    path('', views.housing_home, name="housing_home"),

    # --- Specific Unit URLs ---
    path("units/", views.units_list, name="units_list"),
    path("units/create/", views.create_unit, name="create_unit"),
    path("units/update/<int:unit_id>/", views.update_unit, name="update_unit"), 
    path("units/delete/", views.delete_units, name="delete_units"),
    path('units/import/', views.import_units, name='import_units'),
    path('units/export/', views.export_units, name='export_units'),

    # --- Company and Group URLs ---
    path('company/', views.company_list_view, name="company"),  
    path('company/create/', views.create_company_api, name='api_create_company'),
    path('groups/list/', views.list_company_groups_api, name='list_groups_api'),
    path('groups/create/', views.create_company_group_api, name='create_group_api'),
    path("company/update/<int:pk>/", views.company_update_view, name="company_update"),
    path("company/delete/", views.company_delete_view, name="company_delete"),
    path('company/export/', views.export_companies, name='export_companies'),

    # --- User Management URLs ---
    path('user/', views.users_page, name='user'),

    path('user/create/', views.create_user_api, name='create_user_api'),
    path('user/update/<int:pk>/', views.user_update_view, name='update_user_api'),
    path('user/delete/', views.user_delete_view, name='delete_user_api'),

    path('groups/list/', views.list_company_groups_api, name='groups_list_api'),
    path('companies/list/', views.list_companies_api, name='companies_list_api'),

    path('get_companies/', views.get_companies, name='get_companies'),
    path("user/export/", views.export_users, name="export_users"),

    # --- Allocation URLs ---
    path('allocation/', views.allocation_list_view, name='allocation'),
    path('allocation/create/', views.allocation_create_view, name='allocation_create'),
    path('allocation/update/<int:pk>/', views.allocation_update_view, name='allocation_update'),
    path('allocation/delete/', views.allocation_delete_view, name='allocation_delete'),
    path('allocation/export/', views.allocation_export_view, name='allocation_export'),

    # --- Assignment URLs ---
    path('assigning/', views.assignment_list_view, name='assigning'),
    path('assignment/create/', views.assignment_create_view, name='assignment_create'),
    path('assignment/update/<int:pk>/', views.assignment_update_view, name='assignment_update'),
    path('assignment/delete/', views.assignment_delete_view, name='assignment_delete'),
    path('assignment/export/', views.assignment_export_view, name='assignment_export'),
    path('assignment/get-allocation/', views.get_allocation_by_company_group, name='get_allocation_by_company_group'),
    path('assignment/get-allocations-by-company/', views.get_allocations_by_company, name='get_allocations_by_company'),

    # --- Reservation URLs ---
    path('reservation/', views.reservation_list_view, name='reservation'),
    path('reservation/create/', views.reservation_create_view, name='reservation_create'),
    path('reservation/update/<int:pk>/', views.reservation_update_view, name='reservation_update'),
    path('reservation/delete/', views.reservation_delete_view, name='reservation_delete'),
    path('reservation/export/', views.reservation_export_view, name='reservation_export'),

    # --- Check-In/Check-Out URLs ---
    path('checkin_checkout/', views.checkin_checkout_list_view, name='checkin_checkout'),
    path('checkin/create/', views.checkin_checkout_create_view, name='checkin_checkout_create'),
    path('checkin/update/<int:pk>/', views.checkin_checkout_update_view, name='checkin_checkout_update'),
    path('checkin/delete/', views.checkin_checkout_delete_view, name='checkin_checkout_delete'),
    path('checkin/export/', views.checkin_checkout_export_view, name='checkin_checkout_export'),

    # --- Generic Tab URL (keep last)
    path('<str:tab_name>/', views.housing_tab_view, name="housing_tab"),
    
]
