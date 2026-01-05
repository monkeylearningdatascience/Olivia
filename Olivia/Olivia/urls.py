"""
URL configuration for Olivia project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from Olivia import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('api/', include('api.urls')),  # Mobile API endpoints
    path('admin/', admin.site.urls),
    path("accounts/", include("accounts.urls")),

    # Login
    path('', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html')),

    # Logout (redirects to login page)
    path('accounts/logout/', views.logout, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Departments
    path('humanresource/', include('HumanResource.urls')),
    path('hardservice/', include('HardService.urls')),
    path('softservice/', include('SoftService.urls')),
    path('utility/', include('Utility.urls')),
    path('fls/', include('FLS.urls')),
    path('logistics/', include('Logistics.urls')),
    path('procurement/', include('Procurement.urls')),
    path('warehouse/', include('Warehouse.urls')),
    path('qhse/', include('QHSE.urls')),
    path('ict/', include('ICT.urls')),
    path('tickets/', include('Tickets.urls')),
    path('training/', include('Training.urls')),
    path('housing/', include('Housing.urls')),
    
]
# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)