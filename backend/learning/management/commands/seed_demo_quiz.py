# backend/learning/management/commands/seed_demo_quiz.py
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Org, User
from learning.models import Skill, Module, Question, Choice


class Command(BaseCommand):
    help = "Seed demo org, user, skill, and two demo quiz modules (immediate vs end feedback)."

    def handle(self, *args, **options):
        # ---------------------------------------------------------------------
        # 1) Org
        # ---------------------------------------------------------------------
        org = Org.objects.first()
        if not org:
            org = Org.objects.create(name="Demo Org")
            self.stdout.write(self.style.SUCCESS(f"Created demo org: {org}"))
        else:
            self.stdout.write(self.style.NOTICE(f"Using existing org: {org}"))

        # ---------------------------------------------------------------------
        # 2) Demo learner user
        # ---------------------------------------------------------------------
        user = (
            User.objects.filter(org=org).first()
            or User.objects.create_user(
                username="demo.learner",
                email="demo@example.com",
                password="demo123",
                org=org,
            )
        )
        self.stdout.write(self.style.SUCCESS(f"Using demo user: {user.username}"))

        # ---------------------------------------------------------------------
        # 3) Skill
        # ---------------------------------------------------------------------
        skill, created = Skill.objects.get_or_create(
            org=org,
            name="Demo Skill: Safety Basics",
            defaults={
                "risk_level": "med",
                "valid_for_days": 365,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created skill: {skill.name}"))
        else:
            self.stdout.write(self.style.NOTICE(f"Using existing skill: {skill.name}"))

        # ---------------------------------------------------------------------
        # 4) Two modules with different feedback modes
        # ---------------------------------------------------------------------
        module1, created1 = Module.objects.get_or_create(
            org=org,
            skill=skill,
            title="Demo: Container Unloading Safety (Immediate Feedback)",
            defaults={
                "difficulty": 2,
                "active": True,
                "passing_score": 80,
                "pass_mark": 80,
                "require_viewed": False,
                "question_pool_count": None,
                "shuffle_questions": True,
                "shuffle_choices": True,
                "negative_marking": True,
                "feedback_mode": "immediate",  # 👈 per-question feedback
            },
        )
        if created1:
            self.stdout.write(self.style.SUCCESS(f"Created module: {module1.title}"))
        else:
            self.stdout.write(self.style.NOTICE(f"Using existing module: {module1.title}"))

        module2, created2 = Module.objects.get_or_create(
            org=org,
            skill=skill,
            title="Demo: Container Unloading Safety (End Feedback)",
            defaults={
                "difficulty": 2,
                "active": True,
                "passing_score": 80,
                "pass_mark": 80,
                "require_viewed": False,
                "question_pool_count": None,
                "shuffle_questions": True,
                "shuffle_choices": True,
                "negative_marking": True,
                "feedback_mode": "end",  # 👈 feedback only at the end
            },
        )
        if created2:
            self.stdout.write(self.style.SUCCESS(f"Created module: {module2.title}"))
        else:
            self.stdout.write(self.style.NOTICE(f"Using existing module: {module2.title}"))

        # ---------------------------------------------------------------------
        # 5) Clear any existing questions on these demo modules
        # ---------------------------------------------------------------------
        module1.questions.all().delete()
        module2.questions.all().delete()
        self.stdout.write(self.style.NOTICE("Cleared existing questions for demo modules."))

        # ---------------------------------------------------------------------
        # 6) Define 5 canonical question specs we’ll reuse for both modules
        # ---------------------------------------------------------------------
        q_specs = [
            {
                "qtype": "single",
                "text": "What is the FIRST thing you should do before opening a container door?",
                "points": 5,
                "explanation": (
                    "Before doing anything else, visually inspect the doors for bulging, "
                    "leaning or damage that might indicate a shifted load."
                ),
                "choices": [
                    ("Stand directly in front and pull quickly.", False),
                    ("Check for bulging, leaning or damage to the doors.", True),
                    ("Climb on top of the container to look inside.", False),
                    ("Ignore the doors and start unloading immediately.", False),
                ],
            },
            {
                "qtype": "multi",
                "text": "Which items of PPE are typically required when unloading a container manually?",
                "points": 10,
                "explanation": "Hi-Vis, safety footwear and suitable gloves are usually minimum PPE.",
                "choices": [
                    ("Hi-Vis vest", True),
                    ("Safety footwear", True),
                    ("Gloves", True),
                    ("Flip flops", False),
                    ("Loose fashion scarf", False),
                ],
            },
            {
                "qtype": "truefalse",
                "text": "It is safe to open a container door alone even if the load looks unstable.",
                "points": 5,
                "explanation": (
                    "If the load looks unstable, you must escalate and use barriers and/or "
                    "mechanical aids – never open it alone."
                ),
                "choices": [
                    ("True", False),
                    ("False", True),
                ],
            },
            {
                "qtype": "single",
                "text": "For a typical two-person manual lift of a carton, what is the safest approach?",
                "points": 5,
                "explanation": (
                    "Use a team lift with good posture, keeping the load close to the body and "
                    "avoiding twisting while carrying."
                ),
                "choices": [
                    ("One person lifts while the other watches.", False),
                    ("Both people lift together with straight backs and the load close in.", True),
                    ("Pull the box across the floor by the straps.", False),
                    ("Lift the box above shoulder height to see better.", False),
                ],
            },
            {
                "qtype": "multi",
                "text": "Which of the following are good practices INSIDE the container during unloading?",
                "points": 10,
                "explanation": (
                    "Keep a clear walkway, stack safely, and avoid climbing on unstable stacks or "
                    "walking under suspended loads."
                ),
                "choices": [
                    ("Keep a clear walkway to the doors.", True),
                    ("Stack goods at a safe, stable height.", True),
                    ("Climb onto unstable stacks to reach higher boxes.", False),
                    ("Walk under suspended loads from lifting equipment.", False),
                    ("Report damaged or leaking cartons immediately.", True),
                ],
            },
        ]

        # ---------------------------------------------------------------------
        # 7) Helper to create questions for a module
        # ---------------------------------------------------------------------
        def create_questions_for_module(module):
            questions = []
            for idx, spec in enumerate(q_specs, start=1):
                q = Question.objects.create(
                    module=module,
                    qtype=spec["qtype"],
                    text=spec["text"],
                    order=idx,
                    points=spec["points"],
                    explanation=spec["explanation"],
                )
                questions.append(q)

                choice_objs = [
                    Choice(
                        question=q,
                        text=label,
                        is_correct=is_correct,
                    )
                    for (label, is_correct) in spec["choices"]
                ]
                Choice.objects.bulk_create(choice_objs)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {len(questions)} questions for module: {module.title}"
                )
            )

        # ---------------------------------------------------------------------
        # 8) Create 5 questions for each module
        # ---------------------------------------------------------------------
        create_questions_for_module(module1)
        create_questions_for_module(module2)

        self.stdout.write(self.style.SUCCESS("Demo quiz data seeded successfully."))
        self.stdout.write(
            self.style.SUCCESS(
                f"Modules created/updated:\n"
                f" - {module1.title} (feedback_mode=immediate)\n"
                f" - {module2.title} (feedback_mode=end)\n"
            )
        )