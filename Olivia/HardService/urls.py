from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="hardservice_home"),
]