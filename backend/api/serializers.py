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
        fields = (
            "id",
            "user",
            "module",
            "module_title",
            "completed_at",
            "score",
            "passed",
            "answers",
            "presented_questions",
            "choice_order",
        )


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
    skill_name = serializers.SerializerMethodField()

    class Meta:
        model = RecertRequirement
        fields = [
            "id",
            "due_date",
            "reason",
            "meta",
            "resolved_at",
            "skill",
            "skill_name",
            "sop",
        ]

    def get_skill_name(self, obj):
        return obj.skill.name if obj.skill else None


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
        )


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
