# audits/signals.py
from typing import TYPE_CHECKING

from django.db.models.signals import post_save
from django.dispatch import receiver
from learning.models import Module, RecertRequirement
from sops.models import SOP

if TYPE_CHECKING:
    pass  # type: ignore[unused-import]
from datetime import timedelta

from django.utils import timezone


@receiver(post_save, sender=SOP)
def create_recert_on_publish(sender, instance: SOP, created, **kwargs):
    if instance.status == "published" and instance.version_minor == 0:  # major publish
        # Everyone with skills tied to modules using this SOP → recert in 30 days
        skill_ids = Module.objects.filter(sop=instance).values_list("skill_id", flat=True)
        if not skill_ids:
            return
        # In a real app: determine affected users via assignments. Here: all users in org with those skills required in any role.
        from accounts.models import User

        users = User.objects.filter(org=instance.org)
        due = timezone.now().date() + timedelta(days=30)
        for user in users:
            for sid in skill_ids:
                RecertRequirement.objects.get_or_create(
                    user=user, skill_id=sid, reason="sop_major_update", defaults={"due_date": due}
                )
