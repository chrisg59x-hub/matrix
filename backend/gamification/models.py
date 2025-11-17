
from django.db import models
from django.conf import settings

class XPEvent(models.Model):
    code=models.CharField(max_length=100, unique=True)
    description=models.TextField()
    amount=models.IntegerField()

class XPLedger(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    event=models.ForeignKey(XPEvent,on_delete=models.CASCADE)
    amount=models.IntegerField()
    created_at=models.DateTimeField(auto_now_add=True)

class Skill(models.Model):
    name=models.CharField(max_length=100)
    description=models.TextField(blank=True)

class UserSkillProgress(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    skill=models.ForeignKey(Skill,on_delete=models.CASCADE)
    xp=models.IntegerField(default=0)

class Achievement(models.Model):
    code=models.CharField(max_length=100, unique=True)
    name=models.CharField(max_length=200)
    description=models.TextField()

class UserAchievement(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    achievement=models.ForeignKey(Achievement,on_delete=models.CASCADE)
    unlocked_at=models.DateTimeField(auto_now_add=True)

class SOP(models.Model):
    title=models.CharField(max_length=200)
    video_url=models.URLField()
    description=models.TextField(blank=True)

class SOPProgress(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    sop=models.ForeignKey(SOP,on_delete=models.CASCADE)
    progress=models.FloatField(default=0.0)
    completed=models.BooleanField(default=False)
