from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import Org, User
from learning.models import Skill, Module, Question, Choice

class Command(BaseCommand):
    help = "Seed demo org, users, skills, module, questions"

    def handle(self, *args, **opts):
        org, _ = Org.objects.get_or_create(name="Demo Org")
        # users
        admin, _ = User.objects.get_or_create(username="admin", defaults={"email":"admin@example.com","org":org,"biz_role":"admin"})
        if not admin.has_usable_password():
            admin.set_password("admin123"); admin.save()
        learner, _ = User.objects.get_or_create(username="learner", defaults={"email":"learner@example.com","org":org,"biz_role":"employee"})
        if not learner.has_usable_password():
            learner.set_password("learner123"); learner.save()

        # skill
        picking, _ = Skill.objects.get_or_create(org=org, name="Safe Picking")

        # module
        mod, _ = Module.objects.get_or_create(
            org=org, skill=picking, title="Warehouse Safety Basics",
            defaults={"active": True, "pass_mark": 60, "shuffle_questions": True, "shuffle_choices": True, "negative_marking": False},
        )

        # questions
        if not mod.questions.exists():
            q1 = Question.objects.create(module=mod, qtype="single", text="When lifting, keep your back…", points=10)
            Choice.objects.bulk_create([
                Choice(question=q1, text="Straight and bend at the knees", is_correct=True),
                Choice(question=q1, text="Rounded, lift with your back", is_correct=False),
                Choice(question=q1, text="Twisted to one side", is_correct=False),
            ])

            q2 = Question.objects.create(module=mod, qtype="truefalse", text="It’s OK to run in picking aisles.", points=10)
            Choice.objects.bulk_create([
                Choice(question=q2, text="True", is_correct=False),
                Choice(question=q2, text="False", is_correct=True),
            ])

        self.stdout.write(self.style.SUCCESS("Seeded demo data:\n- admin/admin123\n- learner/learner123"))
