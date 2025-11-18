
from learning.models import XPEvent, Skill
from django.utils import timezone

def award_xp(user, org, skill, amount, source, meta=None):
    meta = meta or {}
    return XPEvent.objects.create(
        user=user,
        org=org,
        skill=skill,
        amount=amount,
        source=source,
        meta=meta,
    )


def score_attempt(attempt):
    # Placeholder scoring logic
    total = 0
    earned = 0
    for aq in attempt.attempt_questions.all():
        total += max(aq.points_awarded, 1)
        if aq.correct:
            earned += aq.points_awarded
    if total == 0:
        return 0
    return int((earned / total) * 100)


def update_skill_progress(user, skill, xp_amount, org):
    return award_xp(user, org, skill, xp_amount, "module_pass")


def check_badges(user, org):
    # Placeholder
    return
