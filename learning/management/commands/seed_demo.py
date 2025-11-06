# learning/management/commands/seed_demo.py
# import itertools
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from learning.models import Department, Team, TeamMember, RoleAssignment


from accounts.models import Org
from learning.models import (
    JobRole, Skill, RoleSkill, Module, ModuleAttempt, XPEvent, SupervisorSignoff,
    LevelDef, Badge, UserBadge, xp_for_next_level
)
from sops.models import SOP

User = get_user_model()




def cumulative_levels(max_level=10):
    total = 0
    for lvl in range(1, max_level + 1):
        total += xp_for_next_level(lvl)
        yield lvl, total


class Command(BaseCommand):
    help = "Populate the Matrix training platform with demo data, levels & badges"

    def handle(self, *args, **options):
        # --- Org & Users ----------------------------------------------------
        org, _ = Org.objects.get_or_create(name="Matrix Training Co.")
        manager, _ = User.objects.get_or_create(
            username="manager",
            defaults={"email": "manager@matrix.local", "org": org, "biz_role": "manager", "is_staff": True},
        )
        if not manager.has_usable_password():
            manager.set_password("manager123"), manager.save()

        employee, _ = User.objects.get_or_create(
            username="employee",
            defaults={"email": "employee@matrix.local", "org": org, "biz_role": "employee", "is_staff": False},
        )
        if not employee.has_usable_password():
            employee.set_password("employee123"), employee.save()

        self.stdout.write(self.style.SUCCESS("✔ Org & users ready"))

        # --- Role & Skills --------------------------------------------------
        role, _ = JobRole.objects.get_or_create(org=org, name="Warehouse Operative")
        safety, _ = Skill.objects.get_or_create(org=org, name="Manual Handling", risk_level="high")
        picking, _ = Skill.objects.get_or_create(org=org, name="Order Picking", risk_level="med")

        RoleSkill.objects.get_or_create(role=role, skill=safety, required=True)
        RoleSkill.objects.get_or_create(role=role, skill=picking, required=True)
        ops, _ = Department.objects.get_or_create(org=org, name="Operations")
        team_a, _ = Team.objects.get_or_create(org=org, department=ops, name="Inbound Team A")
        team_b, _ = Team.objects.get_or_create(org=org, department=ops, name="Outbound Team B")

        # Team memberships
        TeamMember.objects.get_or_create(team=team_a, user=manager, active=True)
        TeamMember.objects.get_or_create(team=team_a, user=employee, active=True)

        # Role assignments
        RoleAssignment.objects.get_or_create(user=manager, role=role, active=True)
        RoleAssignment.objects.get_or_create(user=employee, role=role, active=True)

        # --- SOPs -----------------------------------------------------------
        now = timezone.now()
        sop1, _ = SOP.objects.get_or_create(
            org=org, code="SOP-WH-001", title="Safe Manual Lifting",
            defaults={"version_major":1, "version_minor":0, "status":"published",
                      "content":{"steps":["Plan the lift","Bend knees","Keep back straight"]},
                      "published_at": now - timedelta(days=10), "published_by": manager}
        )
        sop2, _ = SOP.objects.get_or_create(
            org=org, code="SOP-WH-002", title="Order Picking Procedure",
            defaults={"version_major":1, "version_minor":0, "status":"published",
                      "content":{"steps":["Scan location","Confirm item","Place on pallet"]},
                      "published_at": now - timedelta(days=5), "published_by": manager}
        )

        # --- Modules --------------------------------------------------------
        mod1, _ = Module.objects.get_or_create(org=org, skill=safety, sop=sop1,
                                               title="Manual Handling Basics",
                                               defaults={"difficulty":2,"passing_score":80,"active":True})
        mod2, _ = Module.objects.get_or_create(org=org, skill=picking, sop=sop2,
                                               title="Order Picking Refresher",
                                               defaults={"difficulty":3,"passing_score":85,"active":True})

        # --- Attempts & XP (employee) --------------------------------------
        ModuleAttempt.objects.get_or_create(
            user=employee, module=mod1, passed=True, score=88, completed_at=now - timedelta(days=2),
            defaults={"answers": {"q1":"A","q2":"B"}}
        )
        XPEvent.objects.get_or_create(user=employee, org=org, skill=safety,
                                      source="module_pass", amount=120, meta={"module": mod1.title})
        XPEvent.objects.get_or_create(user=employee, org=org, skill=picking,
                                      source="module_pass", amount=160, meta={"module": mod2.title})

        SupervisorSignoff.objects.get_or_create(
            user=employee, skill=safety, supervisor=manager, note="Observed correct technique"
        )

        # --- Level ladder ---------------------------------------------------
        LevelDef.objects.all().delete()
        for lvl, total in cumulative_levels(10):
            LevelDef.objects.get_or_create(level=lvl, total_xp=total)
        self.stdout.write(self.style.SUCCESS("✔ Level ladder (1–10) created"))

        # --- Badges ---------------------------------------------------------
        # Clear demo badges for idempotency (org scope)
        Badge.objects.filter(org=org).delete()

        badges = {
            "RISING_STAR": dict(code="RISING_STAR", name="Rising Star",
                                description="Reached 300 overall XP.",
                                rule_type="overall_xp_at_least", value=300, skill=None, icon="⭐"),
            "SAFETY_CHAMP": dict(code="SAFETY_CHAMP", name="Safety Champion",
                                 description="300+ XP in Manual Handling.",
                                 rule_type="skill_xp_at_least", value=300, skill=safety, icon="🛡️"),
            "EXPERT_PICKER": dict(code="EXPERT_PICKER", name="Expert Picker",
                                  description="300+ XP in Order Picking.",
                                  rule_type="skill_xp_at_least", value=300, skill=picking, icon="📦"),
            "MENTOR": dict(code="MENTOR", name="Mentor",
                           description="Completed at least one supervisor sign-off.",
                           rule_type="signoffs_at_least", value=1, skill=None, icon="🎓"),
        }

        created_badges = []
        for b in badges.values():
            obj = Badge.objects.create(org=org, **b)
            created_badges.append(obj)
        self.stdout.write(self.style.SUCCESS(f"✔ Badges created: {', '.join(b.code for b in created_badges)}"))

        # --- Auto-award badges to employee ---------------------------------
        # Compute totals
        from django.db.models import Sum
        totals = XPEvent.objects.filter(user=employee).aggregate(total=Sum("amount"))
        overall_xp = totals["total"] or 0
        skill_xp = {
            row["skill_id"]: row["sum_xp"]
            for row in XPEvent.objects.filter(user=employee).values("skill_id").annotate(sum_xp=Sum("amount"))
        }
        signoffs = SupervisorSignoff.objects.filter(user=employee).count()

        def has_badge(badge: Badge) -> bool:
            return UserBadge.objects.filter(user=employee, badge=badge).exists()

        awarded = []
        for badge in created_badges:
            ok = False
            if badge.rule_type == "overall_xp_at_least":
                ok = overall_xp >= badge.value
            elif badge.rule_type == "skill_xp_at_least" and badge.skill_id:
                ok = (skill_xp.get(badge.skill_id, 0) >= badge.value)
            elif badge.rule_type == "signoffs_at_least":
                ok = (signoffs >= badge.value)

            if ok and not has_badge(badge):
                UserBadge.objects.create(user=employee, badge=badge, meta={"awarded_by": "seed_demo"})
                awarded.append(badge.code)

        if awarded:
            self.stdout.write(self.style.SUCCESS(f"✔ Awarded to employee: {', '.join(awarded)}"))
        else:
            self.stdout.write("No badges awarded (criteria not met yet).")

        self.stdout.write(self.style.SUCCESS("\nDemo with levels & badges complete! 🎉"))
        self.stdout.write("Login:")
        self.stdout.write("  manager / manager123")
        self.stdout.write("  employee / employee123")
