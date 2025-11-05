from django.core.management.base import BaseCommand
from django.db.models import Sum
from accounts.models import Org
from learning.models import Badge, UserBadge, XPEvent, TeamMember, Team

class Command(BaseCommand):
    help = "Evaluate and award team/department badges"

    def handle(self, *args, **opts):
        awarded = 0
        for badge in Badge.objects.select_related("team","department","org","skill").all():
            # Team total XP
            if badge.rule_type == "team_total_xp_at_least" and badge.team_id:
                member_ids = TeamMember.objects.filter(team_id=badge.team_id, active=True).values_list("user_id", flat=True)
                total = XPEvent.objects.filter(user_id__in=member_ids).aggregate(s=Sum("amount"))["s"] or 0
                if total >= badge.value:
                    # Award to all active members missing it
                    for uid in member_ids:
                        UserBadge.objects.get_or_create(user_id=uid, badge=badge, defaults={"meta":{"awarded_by":"award_group_badges"}})
                        awarded += 1

            # Department total XP
            elif badge.rule_type == "department_total_xp_at_least" and badge.department_id:
                team_ids = Team.objects.filter(department_id=badge.department_id).values_list("id", flat=True)
                member_ids = TeamMember.objects.filter(team_id__in=team_ids, active=True).values_list("user_id", flat=True)
                total = XPEvent.objects.filter(user_id__in=member_ids).aggregate(s=Sum("amount"))["s"] or 0
                if total >= badge.value:
                    for uid in member_ids:
                        UserBadge.objects.get_or_create(user_id=uid, badge=badge, defaults={"meta":{"awarded_by":"award_group_badges"}})
                        awarded += 1

            # Count of team members meeting a per-user XP threshold (overall)
            elif badge.rule_type == "team_member_count_with_xp_at_least" and badge.team_id:
                member_ids = list(TeamMember.objects.filter(team_id=badge.team_id, active=True).values_list("user_id", flat=True))
                # overall xp per member
                totals = XPEvent.objects.filter(user_id__in=member_ids).values("user_id").annotate(s=Sum("amount"))
                count = sum(1 for t in totals if (t["s"] or 0) >= badge.value)
                if count >= len(member_ids):  # all members met threshold
                    for uid in member_ids:
                        UserBadge.objects.get_or_create(user_id=uid, badge=badge, defaults={"meta":{"awarded_by":"award_group_badges"}})
                        awarded += 1

        self.stdout.write(self.style.SUCCESS(f"Awarded/ensured {awarded} team/department badges"))
