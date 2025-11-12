import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

class SOP(models.Model):
    STATUS = [("draft", "draft"), ("review", "review"), ("published", "published"), ("retired", "retired")]
    MEDIA_CHOICES = [("video", "video"), ("pdf", "pdf"), ("pptx", "pptx"), ("link", "link")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey("accounts.Org", on_delete=models.CASCADE)
    code = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    version_major = models.PositiveIntegerField(default=1)
    version_minor = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS, default="draft")
    content = models.JSONField(default=dict)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="sop_reviews"
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="sop_publishers"
    )
    published_at = models.DateTimeField(null=True, blank=True)
    change_note = models.TextField(blank=True, default="")

    media_type = models.CharField(max_length=10, choices=MEDIA_CHOICES, default="pdf")
    media_file = models.FileField(
        upload_to="sops/",
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["mp4", "mov", "mkv", "pdf", "pptx", "ppt"])],
    )
    external_url = models.URLField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    pages = models.PositiveIntegerField(null=True, blank=True)
    thumbnail = models.ImageField(upload_to="sops/thumbs/", null=True, blank=True)
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # ...existing fields..

    class Meta:
        unique_together = ("org", "code", "version_major", "version_minor")
        ordering = ("-created_at",)  # or ("code",) or whatever you prefer

    def __str__(self):
        return f"{self.code} v{self.version_major}.{self.version_minor} – {self.title}"


class SOPView(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sop = models.ForeignKey(SOP, on_delete=models.CASCADE, related_name="views")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sop_views")
    seconds_viewed = models.PositiveIntegerField(default=0)  # accumulate for video
    pages_viewed = models.PositiveIntegerField(default=0)  # max pages reached for PDF/PPT
    progress = models.FloatField(default=0.0)  # 0..1, client-reported best effort
    completed = models.BooleanField(default=False)
    last_heartbeat = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("sop", "user")
