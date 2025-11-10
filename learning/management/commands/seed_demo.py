# learning/management/commands/seed_demo.py
import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Org
from sops.models import SOP
from learning.models import (
    Skill, JobRole, RoleSkill, Module, Question, Choice,
    XPEvent, LevelDef, Badge, UserBadge,
)

User = get_user_model()

class Command(BaseCommand):
    help = "Seed demo data for Matrix SOPRPG (org, users, skills, SOPs, module/questions, XP, badges)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seeding demo data…"))

        # --- Org ---
        org, _ = Org.objects.get_or_create(name="Matrix Industries")

        # --- Users ---
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@matrix.local",
                "org": org,
                "biz_role": "admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if not admin.has_usable_password():
            admin.set_password("admin123"); admin.save()

        manager, _ = User.objects.get_or_create(
            username="manager",
            defaults={
                "email": "manager@matrix.local",
                "org": org,
                "biz_role": "manager",
            },
        )
        if not manager.has_usable_password():
            manager.set_password("manager123"); manager.save()

        employee, _ = User.objects.get_or_create(
            username="employee",
            defaults={
                "email": "employee@matrix.local",
                "org": org,
                "biz_role": "employee",
            },
        )
        if not employee.has_usable_password():
            employee.set_password("employee123"); employee.save()

        # --- Skills & Roles ---
        safety, _ = Skill.objects.get_or_create(org=org, name="Health & Safety")
        product, _ = Skill.objects.get_or_create(org=org, name="Product Knowledge")
        role, _ = JobRole.objects.get_or_create(org=org, name="Warehouse Operative")

        RoleSkill.objects.get_or_create(role=role, skill=safety, required=True)
        RoleSkill.objects.get_or_create(role=role, skill=product, required=False)

        # --- SOP ---
        sop, _ = SOP.objects.get_or_create(org=org, title="Safe Lifting Procedures")

        # --- Module & Questions ---
        module, _ = Module.objects.get_or_create(
            org=org,
            skill=safety,
            sop=sop,
            title="Manual Handling Quiz",
            defaults={
                "pass_mark": 60,
                "active": True,
                "shuffle_questions": True,
                "shuffle_choices": True,
                "negative_marking": False,
            },
        )

        if not module.questions.exists():
            q1 = Question.objects.create(module=module, qtype="single", text="Keep your back…", points=10)
            Choice.objects.bulk_create([
                Choice(question=q1, text="Straight; bend at the knees", is_correct=True),
                Choice(question=q1, text="Rounded; lift with your back", is_correct=False),
                Choice(question=q1, text="Twisted to one side", is_correct=False),
            ])

            q2 = Question.objects.create(module=module, qtype="truefalse", text="It is OK to run in aisles.", points=10)
            Choice.objects.bulk_create([
                Choice(question=q2, text="True", is_correct=False),
                Choice(question=q2, text="False", is_correct=True),
            ])

            q3 = Question.objects.create(module=module, qtype="single", text="Best option for a heavy pallet?", points=10)
            Choice.objects.bulk_create([
                Choice(question=q3, text="Use proper equipment", is_correct=True),
                Choice(question=q3, text="Drag it manually", is_correct=False),
                Choice(question=q3, text="Kick it gently", is_correct=False),
            ])

        # --- Levels (LevelDef has fields: org, level, total_xp) ---
        for lvl in range(1, 6):
        LevelDef.objects.get_or_create(
            level=lvl,
            defaults={"total_xp": lvl * 100},
        )

        # --- Badge (use minimal required fields; adjust if your model requires rule_type/value) ---
        badge, _ = Badge.objects.get_or_create(
            org=org,
            code="SAFEHANDS",
            defaults={
                "name": "Safe Hands",
                "description": "Awarded for passing the safety quiz.",
                "skill": safety,   # remove if your Badge.skill is optional and not present
            },
        )

        UserBadge.objects.get_or_create(user=employee, badge=badge)

        # --- XP sample ---
        XPEvent.objects.get_or_create(org=org, user=employee, skill=safety, source="seed", amount=120)

        self.stdout.write(self.style.SUCCESS("✅ Demo data created."))
        self.stdout.write("Logins:")
        self.stdout.write("  admin / admin123")
        self.stdout.write("  manager / manager123")
        self.stdout.write("  employee / employee123")
