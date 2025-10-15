from django.urls import path
from . import views

urlpatterns = [
    path('', views.logistics_home, name="logistics_home"),
    path('<str:tab_name>/', views.logistics_tab_view, name="logistics_tab"),
]
