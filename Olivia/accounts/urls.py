from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('api/org-levels/', views.organizational_levels, name='api_org_levels'),
    path('api/org-levels/<int:pk>/', views.organizational_level_detail, name='api_org_level_detail'),

    path('api/permissions/', views.permissions_list, name='api_permissions_list'),
    path('api/permissions/<int:pk>/', views.permission_detail, name='api_permission_detail'),

    path('api/role-permissions/', views.role_permissions, name='api_role_permissions'),
    path('api/role-permissions/<int:pk>/delete/', views.role_permission_delete, name='api_role_permission_delete'),

    path('api/assign-org-level/', views.assign_org_level_to_user, name='api_assign_org_level'),

    # Web admin UI
    path('admin/levels/', views.admin_org_levels, name='admin_org_levels'),
    path('admin/levels/<int:pk>/', views.admin_org_level_edit, name='admin_org_level_edit'),

    path('admin/permissions/', views.admin_permissions, name='admin_permissions'),
    path('admin/permissions/<int:pk>/', views.admin_permission_edit, name='admin_permission_edit'),

    path('admin/role-permissions/', views.admin_role_permissions, name='admin_role_permissions'),
    path('admin/assign-level/', views.admin_assign_level, name='admin_assign_level'),

    # Additional URLs
    path("no-access/", views.no_access, name="no_access"),
]
