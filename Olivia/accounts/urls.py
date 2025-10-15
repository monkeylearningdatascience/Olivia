from django.urls import path
from . import views

urlpatterns = [
    path("no-access/", views.no_access, name="no_access"),
]
