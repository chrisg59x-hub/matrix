# learning/models.py
import uuid

from django.conf import settings

# import math
from django.db import models

# from django.utils import timezone

QUESTION_TYPES = [("single", "single"), ("multi", "multi"), ("truefalse", "truefalse")]


def xp_for_next_level(level: int) -> int:
    return int(round(200 * (1.35 ** max(0, level - 1)) / 10.0)) * 10


def level_from_total_xp(total: int) -> int:
    lvl, left = 1, total
    while left >= xp_for_next_level(lvl):
        left -= xp_for_next_level(lvl)
        lvl += 1
    return lvl


class JobRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey("accounts.Org", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("org", "name")

    def __str__(self):
        return self.name


class Skill(models.Model):
    RISK = [("low", "low"), ("med", "med"), ("high", "high")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey("accounts.Org", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    risk_level = models.CharField(max_length=10, choices=RISK, default="med")
    valid_for_days = models.PositiveIntegerField(default=365)

    class Meta:
        unique_together = ("org", "name")

    def __str__(self):
        return self.name


class RoleSkill(models.Model):
    role = models.ForeignKey(JobRole, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    required = models.BooleanField(default=True)

    class Meta:
        unique_together = ("role", "skill")


class Module(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey("accounts.Org", on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    sop = models.ForeignKey("sops.SOP", on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    difficulty = models.PositiveSmallIntegerField(default=2)  # 1-5
    active = models.BooleanField(default=True)
    passing_score = models.PositiveSmallIntegerField(default=80)  # keep for backwards compat
    pass_mark = models.PositiveSmallIntegerField(default=80)  # 👈 explicit pass mark (0-100)
    require_viewed = models.BooleanField(default=True)
    question_pool_count = models.PositiveIntegerField(null=True, blank=True)  # if set, sample this many questions
    shuffle_questions = models.BooleanField(default=True)
    shuffle_choices = models.BooleanField(default=True)
    negative_marking = models.BooleanField(default=True)  # applies to multi-select

    def __str__(self):
        return self.title


class ModuleAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="module_attempts",
    )
    module = models.ForeignKey("learning.Module", on_delete=models.CASCADE, related_name="attempts")

    # timing / results
    created_at = models.DateTimeField(auto_now_add=True)
    # created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveSmallIntegerField(default=0)  # percent 0–100
    passed = models.BooleanField(default=False)

    # payloads for randomised pools
    answers = models.JSONField(default=dict, blank=True)  # {question_id:[choice_ids]}
    presented_questions = models.JSONField(default=list, blank=True)  # [question_id,...]
    choice_order = models.JSONField(default=dict, blank=True)  # {question_id:[choice_id,...]}

    class Meta:
        ordering = ["-created_at"]


class XPEvent(models.Model):
    SOURCE = [
        ("module_pass", "module_pass"),
        ("quiz", "quiz"),
        ("streak", "streak"),
        ("supervisor_signoff", "supervisor_signoff"),
        ("evidence", "evidence"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    org = models.ForeignKey("accounts.Org", on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, null=True, blank=True)
    source = models.CharField(max_length=40, choices=SOURCE)
    amount = models.PositiveIntegerField()
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SupervisorSignoff(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="signee")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="signer")
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)


class RecertRequirement(models.Model):
    REASON = [("expiry", "expiry"), ("sop_major_update", "sop_major_update")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    due_date = models.DateField()
    reason = models.CharField(max_length=30, choices=REASON)
    resolved = models.BooleanField(default=False)


# ---- Levels & Badges --------------------------------------------------------
import uuid

from django.conf import settings
from django.db import models


class LevelDef(models.Model):
    """
    Optional lookup so you can show a nice level ladder in UIs.
    total_xp = cumulative XP required to REACH this level.
    """

    level = models.PositiveIntegerField(primary_key=True)
    total_xp = models.PositiveIntegerField()  # cumulative

    class Meta:
        ordering = ["level"]

    def __str__(self):
        return f"Level {self.level} (≥ {self.total_xp} XP)"


class Badge(models.Model):
    RULE_TYPES = [
        ("overall_xp_at_least", "overall_xp_at_least"),
        ("skill_xp_at_least", "skill_xp_at_least"),
        ("signoffs_at_least", "signoffs_at_least"),
        ("team_total_xp_at_least", "team_total_xp_at_least"),  # NEW
        ("department_total_xp_at_least", "department_total_xp_at_least"),  # NEW
        ("team_member_count_with_xp_at_least", "team_member_count_with_xp_at_least"),  # NEW
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey("accounts.Org", on_delete=models.CASCADE)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    rule_type = models.CharField(max_length=40, choices=RULE_TYPES)
    value = models.PositiveIntegerField(default=0)
    skill = models.ForeignKey("learning.Skill", null=True, blank=True, on_delete=models.CASCADE)
    icon = models.CharField(max_length=200, blank=True, default="")
    # NEW targets for team/department badges
    team = models.ForeignKey("learning.Team", null=True, blank=True, on_delete=models.CASCADE)
    department = models.ForeignKey("learning.Department", null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("org", "code")


class UserBadge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("user", "badge")
        ordering = ["-awarded_at"]

    def __str__(self):
        return f"{self.user} → {self.badge}"


class RoleAssignment(models.Model):
    """
    Links a user to a job role (current assignment).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="role_assignments")
    role = models.ForeignKey(JobRole, on_delete=models.CASCADE, related_name="assignments")
    active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "role", "active")


# --- Departments & Teams -----------------------------------------------------
class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey("accounts.Org", on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=120)

    class Meta:
        unique_together = ("org", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.org})"


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey("accounts.Org", on_delete=models.CASCADE, related_name="teams")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="teams")
    name = models.CharField(max_length=120)

    class Meta:
        unique_together = ("org", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.org})"


class TeamMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_memberships")
    active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("team", "user", "active")


# --- Role assignment (who holds which JobRole) -------------------------------
class RoleAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="role_assignments")
    role = models.ForeignKey(JobRole, on_delete=models.CASCADE, related_name="assignments")
    active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "role", "active")


class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="questions")
    qtype = models.CharField(max_length=10, choices=QUESTION_TYPES, default="single")
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True, default="")  # feedback shown after submit

    class Meta:
        ordering = ["order"]


class Choice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=400)
    is_correct = models.BooleanField(default=False)
