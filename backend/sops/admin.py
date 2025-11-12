from django.contrib import admin

from .models import SOP, SOPView


@admin.register(SOP)
class SOPAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "media_type", "version_major", "version_minor", "status", "org", "published_at")
    list_filter = ("status", "org", "media_type", "active")
    search_fields = ("code", "title", "description")
    ordering = ("-id",)


admin.site.register(SOPView)


from django.contrib import admin
from .models import SOP    