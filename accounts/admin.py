from django.contrib import admin
from .models import Org, User

@admin.register(Org)
class OrgAdmin(admin.ModelAdmin):
    list_display = ("name", "id")

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "org", "biz_role")
