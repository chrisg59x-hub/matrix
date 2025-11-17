# api/serializers.py
# -----------------------------------------------------------------------------
# Recommended structure & tidy imports:
# 1) stdlib / third-party imports
# 2) model imports (grouped by app)
# 3) "simple" model serializers (flat)
# 4) "nested/public" serializers (for read-only, safe exposure)
# 5) request/response schema serializers (non-model)
# -----------------------------------------------------------------------------

# --- Accounts ----------------------------------------------------------------
from accounts.models import Org, User

# --- Learning (roles/skills/modules/quizzes/xp) ------------------------------
from learning.models import (
    Badge,
    Choice,
    Department,
    JobRole,
    LevelDef,
    Module,
    ModuleAttempt,
    Question,
    RecertRequirement,
    RoleAssignment,
    RoleSkill,
    Skill,
    SupervisorSignoff,
    TrainingPathway,
    TrainingPathwayItem,
    Team,
    TeamMember,
    UserBadge,
    XPEvent,
)
from rest_framework import serializers

# --- SOPs (media + viewing) --------------------------------------------------
from sops.models import SOP, SOPView

# -----------------------------------------------------------------------------
# 3) SIMPLE / FLAT MODEL SERIALIZERS
#    Keep these minimal; add nested fields only where it won’t cause recursion.
# -----------------------------------------------------------------------------


class OrgSerializer(serializers.ModelSerializer):
    class Meta:
        model = Org
        fields = ("id", "name")


class UserSerializer(serializers.ModelSerializer):
    org_name = serializers.CharField(source="org.name", read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "org", "org_name", "biz_role")


class SOPSerializer(serializers.ModelSerializer):
    """Includes media fields for video/pdf/pptx/link."""
    media_url = serializers.SerializerMethodField()
    class Meta:
        model = SOP
        fields = "__all__"

    def get_media_url(self, obj):
        request = self.context.get('request')
        f = getattr(obj, 'media_file', None)  # adjust field name
        if f and hasattr(f, 'url') and request:
            return request.build_absolute_uri(f.url)
        return None


class SOPViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = SOPView
        fields = ("id", "sop", "user", "seconds_viewed", "pages_viewed", "progress", "completed", "last_heartbeat")
        read_only_fields = ("id", "user", "last_heartbeat")


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = "__all__"

class TrainingPathwayModuleMiniSerializer(serializers.ModelSerializer):
    """Lightweight module summary used inside pathway items."""
    class Meta:
        model = Module
        fields = ("id", "title", "skill")


class TrainingPathwayItemSerializer(serializers.ModelSerializer):
    module = TrainingPathwayModuleMiniSerializer(read_only=True)

    class Meta:
        model = TrainingPathwayItem
        fields = (
            "id",
            "required",
            "order",
            "notes",
            "module",
            "skill",
            "sop_label",
        )


class TrainingPathwaySerializer(serializers.ModelSerializer):
    """Basic pathway info (used in admin / manager UIs)."""

    class Meta:
        model = TrainingPathway
        fields = (
            "id",
            "name",
            "description",
            "job_role_label",
            "department_label",
            "level_label",
            "active",
        )


class TrainingPathwayDetailSerializer(serializers.ModelSerializer):
    """Full pathway details including items."""
    items = TrainingPathwayItemSerializer(many=True, read_only=True)

    class Meta:
        model = TrainingPathway
        fields = (
            "id",
            "name",
            "description",
            "job_role_label",
            "department_label",
            "level_label",
            "active",
            "items",
        )


class TrainingPathwayMeSerializer(serializers.Serializer):
    """
    Per-user view of pathways with progress.
    We feed it plain dicts from MyTrainingPathwaysView, so it's a plain Serializer,
    not a ModelSerializer.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True, allow_null=True)
    total_items = serializers.IntegerField()
    completed_items = serializers.IntegerField()
    percent_complete = serializers.IntegerField()

class JobRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRole
        fields = "__all__"


class RoleSkillSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)
    skill_name = serializers.CharField(source="skill.name", read_only=True)

    class Meta:
        model = RoleSkill
        fields = ("id", "role", "role_name", "skill", "skill_name", "required")


class ModuleAttemptSerializer(serializers.ModelSerializer):
    module_title = serializers.CharField(source="module.title", read_only=True)

    class Meta:
        model = ModuleAttempt
        fields = [
            "id",
            "module",
            "module_title",
            "user",
            "created_at",
            "completed_at",
            "score",
            "passed",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "completed_at",
            "score",
            "passed",
        ]


class XPEventSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source="skill.name", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = XPEvent
        fields = ("id", "created_at", "org", "user", "username", "skill", "skill_name", "source", "amount", "meta")


class SupervisorSignoffSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source="skill.name", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)
    supervisor_name = serializers.CharField(source="supervisor.username", read_only=True)

    class Meta:
        model = SupervisorSignoff
        fields = (
            "id",
            "user",
            "user_name",
            "skill",
            "skill_name",
            "supervisor",
            "supervisor_name",
            "note",
            "created_at",
        )


class RecertRequirementSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source="skill.name", read_only=True)
    sop_title = serializers.CharField(source="sop.title", read_only=True)

    # New: recommended module for this requirement
    module_id = serializers.SerializerMethodField()
    module_title = serializers.SerializerMethodField()

    # ids so the frontend can build links
    skill_id = serializers.IntegerField(source="skill.id", read_only=True)
    sop_id = serializers.UUIDField(source="sop.id", read_only=True)

    class Meta:
        model = RecertRequirement
        fields = [
            "id",
            "user",
            "skill",
            "sop",
            "reason",
            "due_at",
            "due_date",
            "meta",
            "resolved",
            "skill_name",
            "sop_title",
            "module_id",
            "module_title",
        ]
        read_only_fields = [
            "id",
            "user",
            "skill",
            "sop",
            "resolved",
        ]

    # helper: pick the “primary” module for this recert
    def _get_primary_module(self, obj):
        Module = apps.get_model("learning", "Module")

        qs = Module.objects.filter(
            skill=obj.skill,
            active=True,
        )

        # If this recert is tied to a specific SOP, prefer modules for that SOP
        if obj.sop_id:
            qs = qs.filter(sop=obj.sop)

        # simple rule: lowest difficulty, then alphabetical
        return qs.order_by("difficulty", "title").first()

    def get_module_id(self, obj):
        module = self._get_primary_module(obj)
        return str(module.id) if module else None

    def get_module_title(self, obj):
        module = self._get_primary_module(obj)
        return module.title if module else None


class LevelDefSerializer(serializers.ModelSerializer):
    class Meta:
        model = LevelDef
        fields = "__all__"


class BadgeSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source="skill.name", read_only=True)
    team_name = serializers.CharField(source="team.name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Badge
        fields = (
            "id",
            "org",
            "code",
            "name",
            "description",
            "rule_type",
            "value",
            "skill",
            "skill_name",
            "team",
            "team_name",
            "department",
            "department_name",
            "icon",
        )


class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)
    badge_id = serializers.PrimaryKeyRelatedField(source="badge", queryset=Badge.objects.all(), write_only=True)

    class Meta:
        model = UserBadge
        fields = ("id", "user", "badge", "badge_id", "awarded_at", "meta")


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"


class TeamSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Team
        fields = ("id", "org", "department", "department_name", "name")


class TeamMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(source="user", queryset=User.objects.all(), write_only=True)

    class Meta:
        model = TeamMember
        fields = ("id", "team", "user", "user_id", "username", "active", "joined_at")


class RoleAssignmentSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(source="user", queryset=User.objects.all(), write_only=True)

    class Meta:
        model = RoleAssignment
        fields = ("id", "user", "user_id", "username", "role", "role_name", "active", "assigned_at")


# -----------------------------------------------------------------------------
# 4) NESTED / PUBLIC QUIZ SERIALIZERS
#    These are used to *serve* questions safely (hide is_correct).
# -----------------------------------------------------------------------------


class ChoicePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ("id", "text")  # don't expose is_correct to learners


class QuestionPublicSerializer(serializers.ModelSerializer):
    choices = ChoicePublicSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ("id", "qtype", "text", "points", "choices")


class ModuleSerializer(serializers.ModelSerializer):
    """Expose module with (read-only) public questions for dashboard/preview."""

    questions = QuestionPublicSerializer(many=True, read_only=True)

    # New: recertification info per-module, per-user
    due_at = serializers.DateTimeField(read_only=True)
    due_date = serializers.DateField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Module
        fields = (
            "id",
            "org",
            "skill",
            "sop",
            "title",
            "difficulty",
            "active",
            "pass_mark",
            "questions",
            "passing_score",
            "require_viewed",
            "question_pool_count",
            "shuffle_questions",
            "shuffle_choices",
            "negative_marking",
            # new fields from the annotation:
            "due_at",
            "due_date",
            "is_overdue",
        )

class ModuleSummarySerializer(serializers.ModelSerializer):
    """Lightweight module summary for attempts list."""

    class Meta:
        model = Module
        fields = ("id", "title", "skill", "sop")


class ModuleAttemptMeSerializer(serializers.ModelSerializer):
    module = ModuleSummarySerializer(read_only=True)

    class Meta:
        model = ModuleAttempt
        fields = (
            "id",
            "module",
            "created_at",
            "completed_at",
            "score",
            "passed",
        )
        read_only_fields = fields

# -----------------------------------------------------------------------------
# 5) REQUEST/RESPONSE SCHEMAS (non-model; for endpoints)
# -----------------------------------------------------------------------------


# Progress & leaderboard
class ProgressSkillSerializer(serializers.Serializer):
    skill_id = serializers.UUIDField(allow_null=True)
    skill_name = serializers.CharField(allow_null=True)
    xp = serializers.IntegerField()


class ProgressSerializer(serializers.Serializer):
    overall_xp = serializers.IntegerField()
    overall_level = serializers.IntegerField()
    next_level = serializers.IntegerField()
    xp_to_next = serializers.IntegerField()
    skills = ProgressSkillSerializer(many=True)


class LeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    user_id = serializers.UUIDField()
    username = serializers.CharField()
    overall_xp = serializers.IntegerField()
    level = serializers.IntegerField()


# Who am I (for Swagger banner / UI)
class WhoAmISerializer(serializers.Serializer):
    username = serializers.CharField()
    biz_role = serializers.CharField(allow_null=True)


# Start/Submit attempt (controlled question delivery)
class StartAttemptSerializer(serializers.Serializer):
    attempt_id = serializers.UUIDField()
    module_id = serializers.UUIDField()
    questions = QuestionPublicSerializer(many=True)


class SubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    choice_ids = serializers.ListField(child=serializers.UUIDField())


class SubmitAttemptRequestSerializer(serializers.Serializer):
    answers = SubmitAnswerSerializer(many=True)
