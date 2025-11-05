# learning/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ModuleAttempt, XPEvent, SupervisorSignoff

@receiver(post_save, sender=ModuleAttempt)
def award_xp_on_pass(sender, instance: ModuleAttempt, created, **kwargs):
    if instance.completed_at and instance.passed:
        m = instance.module
        # Core awards: 100 for pass + 10*difficulty bonus
        XPEvent.objects.get_or_create(
            user=instance.user, org=m.org, skill=m.skill, source="module_pass",
            meta={"module": str(m.id)}, defaults={"amount": 100 + 10 * m.difficulty}
        )
        if instance.score is not None:
            extra = max(0, (instance.score - m.passing_score)//5) * 5  # small bonus
            if extra:
                XPEvent.objects.create(user=instance.user, org=m.org, skill=m.skill,
                                       source="quiz", amount=extra, meta={"score": instance.score})

@receiver(post_save, sender=SupervisorSignoff)
def award_xp_on_signoff(sender, instance: SupervisorSignoff, created, **kwargs):
    if created:
        XPEvent.objects.create(user=instance.user, org=instance.user.org,
                               skill=instance.skill, source="supervisor_signoff", amount=150,
                               meta={"supervisor": str(instance.supervisor_id)})
