from django.db import models
from django.conf import settings

class HelseIDProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255, unique=True)
    hpr_number = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"HPR: {self.hpr_number}"