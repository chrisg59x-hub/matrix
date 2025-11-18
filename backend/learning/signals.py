# learning/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import ModuleAttempt, SupervisorSignoff, XPEvent, ModuleAttemptQuestion


# ----------------------------------------------------
# NEW: Compute score + update passed before XP triggers
# ----------------------------------------------------
@receiver(post_save, sender=ModuleAttempt)
def calculate_score_and_pass(sender, instance: ModuleAttempt, created, **kwargs):
    """
    Runs when ModuleAttempt is saved.
    If completed_at is set, score the attempt before XP is awarded.
    """

    if not instance.completed_at:
        return  # not done yet

    # Already scored?
    if instance.score > 0 or instance.passed:
        return  # avoid re-scoring

    # Scoring from ModuleAttemptQuestion
    aq_set = instance.attempt_questions.all()

    if not aq_set.exists():
        # no detailed tracking, fallback to existing values
        return

    total_points = 0
    earned_points = 0

    for aq in aq_set:
        total_points += max(aq.points_awarded, 1)

        if aq.correct:
            earned_points += aq.points_awarded

    if total_points == 0:
        instance.score = 0
    else:
        instance.score = int((earned_points / total_points) * 100)

    # Pass/fail logic (respect existing pass_mark)
    instance.passed = instance.score >= instance.module.pass_mark

    # ensure this update doesn't retrigger infinite loops
    ModuleAttempt.objects.filter(id=instance.id).update(
        score=instance.score,
        passed=instance.passed,
    )


# ----------------------------------------------------
# EXISTING: XP awarded for module pass
# (we do not change this)
# ----------------------------------------------------
@receiver(post_save, sender=ModuleAttempt)
def award_xp_on_pass(sender, instance: ModuleAttempt, created, **kwargs):
    if instance.completed_at and instance.passed:
        m = instance.module
        
        # Core awards: 100 for pass + 10*difficulty bonus
        XPEvent.objects.get_or_create(
            user=instance.user,
            org=m.org,
            skill=m.skill,
            source="module_pass",
            meta={"module": str(m.id)},
            defaults={"amount": 100 + 10 * m.difficulty},
        )

        # Extra XP for exceeding pass mark
        if instance.score is not None:
            extra = max(0, (instance.score - m.passing_score) // 5) * 5
            if extra:
                XPEvent.objects.create(
                    user=instance.user,
                    org=m.org,
                    skill=m.skill,
                    source="quiz",
                    amount=extra,
                    meta={"score": instance.score},
                )


# ----------------------------------------------------
# EXISTING: XP awarded for supervisor signoff
# ----------------------------------------------------
@receiver(post_save, sender=SupervisorSignoff)
def award_xp_on_signoff(sender, instance: SupervisorSignoff, created, **kwargs):
    if created:
        XPEvent.objects.create(
            user=instance.user,
            org=instance.user.org,
            skill=instance.skill,
            source="supervisor_signoff",
            amount=150,
            meta={"supervisor": str(instance.supervisor_id)},
        )

