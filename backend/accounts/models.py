import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Org(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey(Org, on_delete=models.CASCADE, null=True, blank=True)
    biz_role = models.CharField(max_length=20, default="employee")  # employee | manager | admin
