# audits/models.py
from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    when = models.DateTimeField(auto_now_add=True)
    who = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=120)
    obj = models.CharField(max_length=200)
    meta = models.JSONField(default=dict, blank=True)
