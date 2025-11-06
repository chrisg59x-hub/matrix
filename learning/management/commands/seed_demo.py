# learning/management/commands/seed_demo.py
import uuid
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Org
from sops.models import SOP
from learning.models import (
    Skill, JobRole, RoleSkill, Module, Question, Choice,
    ModuleAttempt, XPEvent, LevelDef, Badge, UserBadge,
)

User = get_user_model()

class Command(BaseCommand):
    help = "Seed demo data for Matrix SOPRPG (orgs, users, skills, SOPs, modules, etc.)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seeding demo data..."))

        # --- Org ---
        org, _ = Org.objects.get_or_create(name="Matrix Industries")

        # --- Users ---
        admin, _ = User.objects.get_or_create(
            username="admin", defaults={
                "email": "admin@matrix.local",
                "org": org,
                "biz_role": "admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.set_password("admin123")
        admin.save()

        manager, _ = User.objects.get_or_create(
            username="manager", defaults={
                "email": "manager@matrix.local",
                "org": org,
                "biz_role": "manager",
            },
        )
        manager.set_password("manager123")
        manager.save()

        employee, _ = User.objects.get_or_create(
            username="employee", defaults={
                "email": "employee@matrix.local",
                "org": org,
                "biz_role": "employee",
            },
        )
        employee.set_password("employee123")
        employee.save()

        # --- Skills & Roles ---
        safety, _ = Skill.objects.get_or_create(org=org, name="Health & Safety")
        product, _ = Skill.objects.get_or_create(org=org, name="Product Knowledge")
        role, _ = JobRole.objects.get_or_create(org=org, name="Warehouse Operative")

        RoleSkill.objects.get_or_create(role=role, skill=safety, required=True)
        RoleSkill.objects.get_or_create(role=role, skill=product, required=False)

        # --- SOPs ---
        sop, _ = SOP.objects.get_or_create(org=org, title="Safe Lifting Procedures")

        # --- Modules & Questions ---
        module, _ = Module.objects.get_or_create(
            org=org,
            skill=safety,
            sop=sop,
            title="Manual Handling Quiz",
            pass_mark=60,
            active=True,
            shuffle_questions=True,
            shuffle_choices=True,
        )

        if not module.questions.exists():
            for i in range(3):
                q = Question.objects.create(
                    module=module,
                    qtype="single",
                    text=f"What is the correct way to lift object {i+1}?",
                    points=10,
                )
                correct_choice = Choice.objects.create(question=q, text="Bend knees, keep back straight", is_correct=True)
                Choice.objects.create(question=q, text="Bend back, keep legs straight", is_correct=False)
                Choice.objects.create(question=q, text="Ask someone else", is_correct=False)
                Choice.objects.create(question=q, text="Use a forklift unnecessarily", is_correct=False)

        # --- XP Levels ---
        # --- XP Levels ---
    for lvl in range(1, 6):
        LevelDef.objects.get_or_create(
        org=org,
        level=lvl,
        defaults={"total_xp": lvl * 100},  # <-- use total_xp, not min_xp
    )

        # --- Badges ---
        badge, _ = Badge.objects.get_or_create(
        org=org,
        code="SAFEHANDS",
        defaults={
            "name": "Safe Hands",
            "description": "Awarded for passing the safety quiz.",
            "rule_type": "skill_xp",  # adjust to a valid enum in your model
            "value": 100,             # threshold or points depending on your rule
            "skill": safety,
        },
        )
        UserBadge.objects.get_or_create(user=employee, badge=badge)

        # --- XP Events ---
        XPEvent.objects.create(org=org, user=employee, skill=safety, source="quiz", amount=120)

        self.stdout.write(self.style.SUCCESS("✅ Demo data created successfully!"))
        self.stdout.write("Logins:")
        self.stdout.write("  admin / admin123")
        self.stdout.write("  manager / manager123")
        self.stdout.write("  employee / employee123")
