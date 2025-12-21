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


    # --- Generic Tab URL (keep last)
    path('<str:tab_name>/', views.housing_tab_view, name="housing_tab"),
    
]
