from django.db import models
from django.contrib.auth.models import User


class Authentication(models.Model):
    token = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Kernels(models.Model):
    kernel_id = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kernel_name = models.CharField(max_length=30)
