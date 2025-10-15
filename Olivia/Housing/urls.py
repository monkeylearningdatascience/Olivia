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

    # --- Generic Tab URL (keep last)
    path('<str:tab_name>/', views.housing_tab_view, name="housing_tab"),
]
