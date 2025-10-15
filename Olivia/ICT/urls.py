from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="ict_home"),
]