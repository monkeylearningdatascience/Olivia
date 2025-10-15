from django.contrib.auth.models import User
from django.db import models

class AppAccess(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    allowed_apps = models.ManyToManyField(AppAccess, blank=True)

    def __str__(self):
        return self.user.username
