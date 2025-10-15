from django.urls import path
from . import views

urlpatterns = [
    path('', views.qhse_home, name="qhse_home"),
    path('<str:tab_name>/', views.qhse_tab_view, name="qhse_tab"), 
]