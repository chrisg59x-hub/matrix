# api/views.py
# -----------------------------------------------------------------------------
# 1) Core imports
# -----------------------------------------------------------------------------
import random
import csv
import io
from datetime import timedelta
# -----------------------------------------------------------------------------
# 2) App model imports Question, Choice
# -----------------------------------------------------------------------------
from django.http import HttpResponse
from django.db import models
from django.db.models import Sum, Q, Exists, OuterRef, IntegerField, Value, Avg, Count
from drf_spectacular.utils import extend_schema    #, OpenApiParameter
from rest_framework.decorators import api_view, permission_classes, action
from accounts.models import Org, User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from learning.models import (
    Badge,
    Department,
    JobRole,
    LevelDef,
    Module,
    ModuleAttempt,
    RecertRequirement,
    RoleAssignment,
    RoleSkill,
    TrainingPathway,
    TrainingPathwayItem,
    Skill,
    SupervisorSignoff,
    Team,
    TeamMember,
    UserBadge,
    XPEvent,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import decorators, permissions, response, status, viewsets, filters, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied, ValidationError
from sops.models import SOP, SOPView

# -----------------------------------------------------------------------------
# 4) Permissions
# -----------------------------------------------------------------------------
from .permissions import IsManagerForWrites, IsManagerOnly

# -----------------------------------------------------------------------------
# 3) Serializer imports
# -----------------------------------------------------------------------------
from .serializers import (
    BadgeSerializer,
    DepartmentSerializer,
    JobRoleSerializer,
    LeaderboardEntrySerializer,
    LevelDefSerializer,
    ModuleAttemptSerializer,
    ModuleAttemptMeSerializer,
    ModuleSerializer,
    OrgSerializer,
    ProgressSerializer,
    QuestionPublicSerializer,
    AttemptReviewSerializer,
    RecertRequirementSerializer,
    RoleAssignmentSerializer,
    RoleSkillSerializer,
    SkillSerializer,
    SOPSerializer,
    SOPViewSerializer,
    StartAttemptSerializer,
    SubmitAttemptRequestSerializer,
    NextQuestionSerializer,
    SingleAnswerRequestSerializer,
    ManagerDashboardSerializer,
    MyDashboardSerializer,  
    SingleAnswerResponseSerializer,
    SupervisorSignoffSerializer,
    TrainingPathwaySerializer,
    TrainingPathwayDetailSerializer,
    TrainingPathwayMeSerializer,
    TeamMemberSerializer,
    TeamSerializer,
    UserBadgeSerializer,
    UserSerializer,
    WhoAmISerializer,
    XPEventSerializer,
)

# -----------------------------------------------------------------------------
# 5) Basic CRUD ViewSets (standard DRF)
# -----------------------------------------------------------------------------
class OrgViewSet(viewsets.ModelViewSet):
    queryset = Org.objects.all()
    serializer_class = OrgSerializer
    permission_classes = [IsManagerForWrites]

class IsOrgManager(permissions.BasePermission):
    """
    Placeholder – adapt to your actual manager permission.
    Allow safe methods to all authenticated users, restrict writes.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        # tweak this to your actual org admin / manager flag
        return getattr(request.user, "is_manager", False)
    
class TrainingPathwayViewSet(viewsets.ModelViewSet):
    """
    CRUD for pathways – mainly for managers.
    """
    queryset = TrainingPathway.objects.all().select_related("org", "job_role", "department", "level")
    serializer_class = TrainingPathwaySerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        # Filter by user's org if you have per-org isolation
        if hasattr(user, "org_id") and user.org_id:
            qs = qs.filter(org=user.org_id)
        return qs

    def get_serializer_class(self):
        if self.action in ("retrieve",):
            return TrainingPathwayDetailSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        org = getattr(self.request.user, "org", None)
        serializer.save(org=org, created_by=self.request.user)

class MyTrainingPathwaysView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        org = getattr(user, "org", None)

        base_qs = TrainingPathway.objects.filter(active=True)
        if org is not None:
            base_qs = base_qs.filter(org=org)

        # For now, just show all active pathways in this org.
        # Later we can get fancy and match labels to user.profile fields.
        base_qs = base_qs.prefetch_related("items", "items__module")

        results = []
        for p in base_qs:
            items = [i for i in p.items.all() if i.required and i.module_id]
            total = len(items)

            if total == 0:
                completed = 0
            else:
                module_ids = [i.module_id for i in items]
                passed_ids = set(
                    ModuleAttempt.objects.filter(
                        user=user,
                        module_id__in=module_ids,
                        passed=True,
                    ).values_list("module_id", flat=True)
                )
                completed = sum(1 for i in items if i.module_id in passed_ids)

            percent = int(round((completed / total) * 100)) if total > 0 else 0

            results.append({
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "total_items": total,
                "completed_items": completed,
                "percent_complete": percent,
            })

        serializer = TrainingPathwayMeSerializer(results, many=True)
        return Response(serializer.data)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsManagerForWrites]

class SOPViewSet(viewsets.ModelViewSet):
    queryset = SOP.objects.all()  # add .order_by(...) if you didn’t set Meta.ordering
    serializer_class = SOPSerializer
    permission_classes = [IsManagerForWrites]
    parser_classes = (MultiPartParser, FormParser, JSONParser)  # <-- add this

    # Nice APIs for list views:
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['org', 'active']  # adjust to your fields
    search_fields = ['title', 'code', 'description']  # adjust
    ordering_fields = ['created_at', 'title', 'id']   # adjust
    ordering = ['-created_at']  # default list order

class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsManagerForWrites]


class JobRoleViewSet(viewsets.ModelViewSet):
    queryset = JobRole.objects.all()
    serializer_class = JobRoleSerializer
    permission_classes = [IsManagerForWrites]


class RoleSkillViewSet(viewsets.ModelViewSet):
    queryset = RoleSkill.objects.select_related("role", "skill")
    serializer_class = RoleSkillSerializer
    permission_classes = [IsManagerForWrites]


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.select_related("skill", "sop")
    serializer_class = ModuleSerializer
    permission_classes = [IsManagerForWrites]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        user = self.request.user

        # ----------------------------------------------------
        # 1) Simple skill filter: ?skill=123
        # ----------------------------------------------------
        skill_id = params.get("skill")
        if skill_id:
            qs = qs.filter(skill_id=skill_id)

        # If we don't have an authenticated user, just return early
        if not user or not user.is_authenticated:
            return qs

        # ----------------------------------------------------
        # 2) Annotate recert info for this user & module
        # ----------------------------------------------------
        today = timezone.localdate()
        now = timezone.now()

        # Base queryset of unresolved recert requirements for this user,
        # tied to the SAME org as the module (OuterRef("org")),
        # and matching either the module's skill OR module's SOP.
        base_reqs = (
            RecertRequirement.objects
            .filter(
                user=user,
                resolved=False,
                org=models.OuterRef("org"),
            )
            .filter(
                Q(skill_id=models.OuterRef("skill_id")) |
                Q(sop_id=models.OuterRef("sop_id"))
            )
        )

        # The “next” requirement (soonest due, regardless of overdue or not)
        upcoming_reqs = base_reqs.order_by("due_date", "due_at")

        # Only overdue requirements, for is_overdue
        overdue_reqs = base_reqs.filter(
            Q(due_date__lt=today) | Q(due_at__lte=now)
        )

        # Annotate each module:
        #   - due_at / due_date: earliest requirement
        #   - is_overdue: does any overdue requirement exist?
        qs = qs.annotate(
            due_at=models.Subquery(upcoming_reqs.values("due_at")[:1]),
            due_date=models.Subquery(upcoming_reqs.values("due_date")[:1]),
            is_overdue=models.Exists(overdue_reqs),
        )

        # ----------------------------------------------------
        # 3) Filter: ?onlyOverdue=1 using the annotation
        # ----------------------------------------------------
        only_overdue = params.get("onlyOverdue")
        if only_overdue == "1":
            qs = qs.filter(is_overdue=True)

        return qs
    
    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """
        Simple stats for a single module:
        - total attempts
        - unique users
        - pass count & pass rate
        - average score
        - timestamps for last attempt / last pass
        """
        module = self.get_object()

        qs = ModuleAttempt.objects.filter(module=module)

        total_attempts = qs.count()
        unique_users = qs.values("user_id").distinct().count()
        pass_count = qs.filter(passed=True).count()
        agg = qs.aggregate(avg_score=Avg("score"))

        last_attempt = qs.order_by("-created_at").values_list("created_at", flat=True).first()
        last_pass = (
            qs.filter(passed=True)
            .order_by("-completed_at")
            .values_list("completed_at", flat=True)
            .first()
        )

        pass_rate = float(round(pass_count * 100.0 / total_attempts, 1)) if total_attempts else 0.0
        avg_score = float(round(agg["avg_score"] or 0.0, 1))

        payload = {
            "module_id": str(module.id),
            "title": module.title,
            "total_attempts": total_attempts,
            "unique_users": unique_users,
            "pass_count": pass_count,
            "pass_rate": pass_rate,
            "avg_score": avg_score,
            "last_attempt": last_attempt,
            "last_pass": last_pass,
        }

        # If you want Swagger to know about it:
        # from .serializers import ModuleStatsSerializer
        # return Response(ModuleStatsSerializer(payload).data)

        return Response(payload)

class ModuleAttemptViewSet(viewsets.ModelViewSet):
    queryset = ModuleAttempt.objects.select_related("module", "user")
    serializer_class = ModuleAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

@extend_schema(responses=AttemptReviewSerializer)
@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def review(request, attempt_id: str):
    """
    Read-only review of a completed attempt.

    Returns the module, overall score/pass flag, and a list of questions
    with choices, showing which ones were selected and which are correct.
    """
    try:
        attempt = ModuleAttempt.objects.select_related("module").get(
            id=attempt_id,
            user=request.user,
        )
    except ModuleAttempt.DoesNotExist:
        raise ValidationError("Attempt not found.")

    module = attempt.module

    # Normalise answers so keys + choice IDs are strings
    # attempt.answers is stored as {question_id: [choice_ids]}
    raw_answers = attempt.answers or {}
    answers_by_qid: dict[str, list[str]] = {}
    for qid, choice_ids in raw_answers.items():
        qid_str = str(qid)
        answers_by_qid[qid_str] = [str(cid) for cid in (choice_ids or [])]

    # Load all questions + choices for this module
    questions = list(module.questions.prefetch_related("choices").all())

    review_questions = []
    for q in questions:
        qid_str = str(q.id)
        selected_ids = set(answers_by_qid.get(qid_str, []))

        choice_payload = []
        for c in q.choices.all():
            cid_str = str(c.id)
            choice_payload.append(
                {
                    "id": c.id,
                    "text": c.text,
                    "is_correct": c.is_correct,
                    "selected": cid_str in selected_ids,
                }
            )

        review_questions.append(
            {
                "id": q.id,
                "text": q.text,
                "qtype": q.qtype,
                "points": float(q.points),
                "explanation": q.explanation or "",
                "choices": choice_payload,
            }
        )

    payload = {
        "attempt_id": str(attempt.id),
        "module_id": str(module.id),
        "module_title": module.title,
        "score_percent": attempt.score,
        "passed": attempt.passed,
        "created_at": attempt.created_at,
        "completed_at": attempt.completed_at,
        "questions": review_questions,
    }

    # You can keep AttemptReviewSerializer for schema, no need to re-serialise
    return response.Response(payload)


class StartModuleAttemptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, format=None):
        module = get_object_or_404(Module, pk=pk, active=True)

        attempt = ModuleAttempt.objects.create(
            user=request.user,
            module=module,
        )

        serializer = ModuleAttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class MyModuleAttemptsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        qs = (
            ModuleAttempt.objects
            .select_related("module", "module__skill", "module__sop")
            .filter(user=request.user)
            .order_by("-created_at")
        )
        serializer = ModuleAttemptMeSerializer(qs, many=True)
        return Response(serializer.data)

class XPEventViewSet(viewsets.ModelViewSet):
    queryset = XPEvent.objects.select_related("user", "skill", "org")
    serializer_class = XPEventSerializer
    permission_classes = [permissions.IsAuthenticated]


class SupervisorSignoffViewSet(viewsets.ModelViewSet):
    queryset = SupervisorSignoff.objects.select_related("skill", "user", "supervisor")
    serializer_class = SupervisorSignoffSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        u = self.request.user
        if getattr(u, "biz_role", "") not in ("manager", "admin"):
            raise PermissionDenied("Only managers/admins can record supervisor sign-offs.")
        serializer.save(supervisor=u)


class RecertRequirementViewSet(viewsets.ModelViewSet):
    queryset = RecertRequirement.objects.select_related("skill", "user")
    serializer_class = RecertRequirementSerializer
    permission_classes = [IsManagerForWrites]


class LevelDefViewSet(viewsets.ModelViewSet):
    queryset = LevelDef.objects.all()
    serializer_class = LevelDefSerializer
    permission_classes = [IsManagerForWrites]


class BadgeViewSet(viewsets.ModelViewSet):
    queryset = Badge.objects.select_related("org", "skill", "team", "department")
    serializer_class = BadgeSerializer
    permission_classes = [IsManagerForWrites]


class UserBadgeViewSet(viewsets.ModelViewSet):
    queryset = UserBadge.objects.select_related("user", "badge")
    serializer_class = UserBadgeSerializer
    permission_classes = [permissions.IsAuthenticated]


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.select_related("org")
    serializer_class = DepartmentSerializer
    permission_classes = [IsManagerForWrites]


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.select_related("org", "department")
    serializer_class = TeamSerializer
    permission_classes = [IsManagerForWrites]


class TeamMemberViewSet(viewsets.ModelViewSet):
    queryset = TeamMember.objects.select_related("team", "user", "team__org", "team__department")
    serializer_class = TeamMemberSerializer
    permission_classes = [IsManagerForWrites]


class RoleAssignmentViewSet(viewsets.ModelViewSet):
    queryset = RoleAssignment.objects.select_related("user", "role")
    serializer_class = RoleAssignmentSerializer
    permission_classes = [IsManagerForWrites]

class MyOverdueSOPsView(generics.ListAPIView):
    """
    Returns only overdue, unresolved recertification requirements
    for the currently authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RecertRequirementSerializer

    def get_queryset(self):
        user = self.request.user
        today = timezone.localdate()
        now = timezone.now()

        qs = RecertRequirement.objects.filter(
            user=user,
            resolved=False,  # unresolved only
        )

        # If your User model has an org FK, keep everything in the same org
        if hasattr(user, "org_id") and user.org_id:
            qs = qs.filter(org=user.org)

        # Past-due by either date or datetime
        qs = qs.filter(
            Q(due_date__lt=today) | Q(due_at__lt=now)
        )

        # Optimise joins for serializer
        return qs.select_related("skill", "sop")
       
class MeOverdueSopsView(generics.ListAPIView):
    """
    Return overdue recertification requirements for the current user.

    Overdue if:
      - resolved == False
      AND
      - (due_date < today) OR (due_at <= now, if due_at is set)
    """
    serializer_class = RecertRequirementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        today = timezone.localdate()
        now = timezone.now()

        return (
            RecertRequirement.objects
            .filter(
                user=user,
                resolved=False,
            )
            .filter(
                Q(due_date__lt=today) | Q(due_at__lte=now)
            )
            .order_by("due_date", "due_at")
        )

# -----------------------------------------------------------------------------
# 6) SOP Media Heartbeat & Completion
# -----------------------------------------------------------------------------
@extend_schema(request=SOPViewSerializer, responses=SOPViewSerializer)
@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.IsAuthenticated])
def sop_view_heartbeat(request, sop_id):
    """Track video/pdf/presentation progress for a SOP."""
    sop = get_object_or_404(SOP, id=sop_id)
    view, _ = SOPView.objects.get_or_create(sop=sop, user=request.user)
    data = request.data or {}

    seconds = int(data.get("seconds_viewed") or 0)
    pages = int(data.get("pages_viewed") or 0)
    progress = float(data.get("progress") or 0)
    completed = bool(data.get("completed") or False)

    if seconds:
        view.seconds_viewed += seconds
    if pages:
        view.pages_viewed = max(view.pages_viewed, pages)
    if progress:
        view.progress = max(view.progress, min(1.0, progress))
    if completed:
        view.completed = True

    view.save()
    return response.Response(SOPViewSerializer(view).data)


# -----------------------------------------------------------------------------
# 7) Gamified XP Progress / Leaderboards
# -----------------------------------------------------------------------------
def level_from_total_xp(xp: int) -> int:
    """Example level curve — tweak as needed."""
    return int((xp or 0) ** 0.5 // 10)


def _org_xp_queryset(request):
    """
    Convenience helper: XPEvent queryset scoped to the current user's org.
    """
    org_id = getattr(request.user, "org_id", None)
    qs = XPEvent.objects.all()
    if org_id:
        qs = qs.filter(org_id=org_id)
    return qs


@extend_schema(responses=ProgressSerializer)
@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def my_progress(request):
    """Current user's XP and level summary."""
    user = request.user
    total_xp = XPEvent.objects.filter(user=user).aggregate(s=Sum("amount"))["s"] or 0
    overall_level = level_from_total_xp(total_xp)
    next_level = overall_level + 1
    xp_next = (next_level * 10) ** 2
    xp_to_next = xp_next - total_xp

    skills = XPEvent.objects.filter(user=user).values("skill_id", "skill__name").annotate(xp=Sum("amount"))

    skills_data = [{"skill_id": s["skill_id"], "skill_name": s["skill__name"], "xp": s["xp"]} for s in skills]
    payload = {
        "overall_xp": total_xp,
        "overall_level": overall_level,
        "next_level": next_level,
        "xp_to_next": xp_to_next,
        "skills": skills_data,
    }
    return response.Response(payload)


@extend_schema(responses=LeaderboardEntrySerializer(many=True))
@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def leaderboard(request):
    """Simple org leaderboard by total XP (JSON)."""
    qs = (
        _org_xp_queryset(request)
        .values("user_id", "user__username")
        .annotate(overall_xp=Sum("amount"))
        .order_by("-overall_xp")
    )

    results = []
    for rank, row in enumerate(qs, start=1):
        results.append({
            "rank": rank,
            "user_id": row["user_id"],
            "username": row["user__username"],
            "overall_xp": row["overall_xp"] or 0,
            "level": level_from_total_xp(row["overall_xp"]),
        })
    return response.Response(results)

@extend_schema(responses=MyDashboardSerializer)
@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def my_dashboard(request):
    """
    Personal dashboard for the current user.
    Combines XP, level, attempt stats and overdue recertification info.
    """
    user = request.user

    # --- XP + level (same curve as my_progress) -----------------------------
    total_xp = XPEvent.objects.filter(user=user).aggregate(s=Sum("amount"))["s"] or 0
    overall_level = level_from_total_xp(total_xp)
    next_level = overall_level + 1
    xp_next = (next_level * 10) ** 2
    xp_to_next = max(0, xp_next - total_xp)

    # --- Attempts -----------------------------------------------------------
    attempts_qs = ModuleAttempt.objects.filter(user=user)
    attempts_total = attempts_qs.count()
    attempts_passed = attempts_qs.filter(passed=True).count()

    now = timezone.now()
    since_30 = now - timedelta(days=30)
    attempts_last_30 = attempts_qs.filter(created_at__gte=since_30).count()

    avg_score_val = attempts_qs.aggregate(avg=Avg("score"))["avg"] or 0.0
    avg_score_val = float(round(avg_score_val, 1))

    # --- Overdue recert requirements ---------------------------------------
    today = timezone.localdate()
    overdue_qs = (
        RecertRequirement.objects
        .select_related("skill", "sop")
        .filter(
            user=user,
            resolved=False,
        )
        .filter(
            Q(due_date__lt=today) | Q(due_at__lte=now)
        )
        .order_by("due_date", "due_at")
    )

    overdue_recerts = []
    for r in overdue_qs:
        overdue_recerts.append(
            {
                "id": r.id,
                "skill_name": getattr(r.skill, "name", None),
                "sop_title": getattr(r.sop, "title", None),
                "reason": r.reason,
                "due_date": r.due_date,
                "due_at": r.due_at,
            }
        )

    payload = {
        "overall_xp": int(total_xp),
        "overall_level": int(overall_level),
        "next_level": int(next_level),
        "xp_to_next": int(xp_to_next),
        "attempts_total": int(attempts_total),
        "attempts_passed": int(attempts_passed),
        "attempts_last_30_days": int(attempts_last_30),
        "avg_score": avg_score_val,
        "overdue_recerts": overdue_recerts,
    }

    ser = MyDashboardSerializer(payload)
    return response.Response(ser.data)








# -----------------------------------------------------------------------------
# 8) Quizzes / Module Attempts
#    (uses start_module_attempt & submit_started_attempt already implemented)
# -----------------------------------------------------------------------------
# NOTE: your detailed implementations for start_module_attempt() and
#       submit_started_attempt() remain unchanged — keep them here below.
#       Include @extend_schema annotations as shown earlier.

@extend_schema(responses=AttemptReviewSerializer)
@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def attempt_review(request, attempt_id: str):
    """
    Read-only review of a completed attempt.

    Returns the module, overall score/pass flag, and a list of questions
    with choices, showing which ones were selected and which are correct.
    """
    try:
        attempt = ModuleAttempt.objects.select_related("module").get(
            id=attempt_id,
            user=request.user,
        )
    except ModuleAttempt.DoesNotExist:
        raise ValidationError("Attempt not found.")

    module = attempt.module

    # Load all questions + choices for this module
    questions = list(module.questions.prefetch_related("choices").all())
    q_map = {str(q.id): q for q in questions}

    # answers is stored as {question_id: [choice_ids]}
    answers = attempt.answers or {}

    review_questions = []
    for qid, q in q_map.items():
        selected_ids = set(str(cid) for cid in answers.get(qid, []))

        choice_payload = []
        for c in q.choices.all():
            choice_payload.append(
                {
                    "id": c.id,
                    "text": c.text,
                    "is_correct": c.is_correct,
                    "selected": str(c.id) in selected_ids,
                }
            )

        review_questions.append(
            {
                "id": q.id,
                "text": q.text,
                "qtype": q.qtype,
                "points": float(q.points),
                "explanation": q.explanation or "",
                "choices": choice_payload,
            }
        )

    payload = {
        "attempt_id": attempt.id,
        "module_id": module.id,
        "module_title": module.title,
        "score_percent": attempt.score,
        "passed": attempt.passed,
        "created_at": attempt.created_at,
        "completed_at": attempt.completed_at,
        "questions": review_questions,
    }

    ser = AttemptReviewSerializer(payload)
    return response.Response(ser.data)




def _get_next_unanswered_question(attempt: ModuleAttempt):
    """
    Returns (Question or None, remaining_count, total_count) based on
    presented_questions and existing ModuleAttemptQuestion rows.
    """
    presented_ids = [str(qid) for qid in (attempt.presented_questions or [])]
    total = len(presented_ids)
    if total == 0:
        return None, 0, 0

    answered_ids = set(
        attempt.attempt_questions.values_list("question_id", flat=True)
    )

    # preserve order from presented_questions
    for qid in presented_ids:
        if qid not in {str(aid) for aid in answered_ids}:
            # next unanswered
            q = attempt.module.questions.prefetch_related("choices").filter(id=qid).first()
            if not q:
                continue
            remaining = len([x for x in presented_ids if x not in {str(aid) for aid in answered_ids}])
            return q, remaining, total

    # none left
    return None, 0, total

def _require_manager(request):
    u = request.user
    if getattr(u, "biz_role", "") not in ("manager", "admin"):
        raise PermissionDenied("Managers/admins only.")
    return u

def _org_id(request):
    return getattr(request.user, "org_id", None)

def _csv_response(filename: str, rows, header: list[str]):
    buf = io.StringIO()
    w = csv.writer(buf)
    if header:
        w.writerow(header)
    for r in rows:
        w.writerow(r)
    resp = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp

# --- CSV: ORG Leaderboard --------------------------------------------------

@extend_schema(
    responses={200: {"type": "string", "format": "binary"}},
    description="Download organisation leaderboard as CSV (rank, user, XP, level).",
)
@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def leaderboard_csv(request):
    """
    CSV export of org leaderboard by total XP.
    """
    qs = (
        _org_xp_queryset(request)
        .values("user_id", "user__username")
        .annotate(overall_xp=Sum("amount"))
        .order_by("-overall_xp")
    )

    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="leaderboard.csv"'

    writer = csv.writer(resp)
    writer.writerow(["rank", "user_id", "username", "overall_xp", "level"])

    for rank, row in enumerate(qs, start=1):
        xp = row["overall_xp"] or 0
        writer.writerow([
            rank,
            row["user_id"],
            row["user__username"],
            xp,
            level_from_total_xp(xp),
        ])

    return resp

# --- CSV: Raw XP export (manager/admin only) -------------------------------

@extend_schema(
    responses={200: {"type": "string", "format": "binary"}},
    description=(
        "Download raw XP events as CSV for the current org. "
        "Optional query params: ?since_days=30 to limit to recent events."
    ),
)
@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def xp_events_csv(request):
    """
    CSV dump of XPEvent rows for the current org.
    """
    qs = _org_xp_queryset(request).select_related("user", "skill")

    # Optional simple time filter: ?since_days=30
    since_days = request.GET.get("since_days")
    if since_days:
        try:
            days = int(since_days)
            cutoff = timezone.now() - timedelta(days=days)
            qs = qs.filter(created_at__gte=cutoff)
        except ValueError:
            pass  # ignore bad input, just return full queryset

    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="xp_events.csv"'

    writer = csv.writer(resp)
    writer.writerow([
        "id",
        "created_at",
        "user_id",
        "username",
        "skill_id",
        "skill_name",
        "amount",
        "source",
        "reason",
    ])

    for ev in qs.order_by("-created_at"):
        writer.writerow([
            ev.id,
            ev.created_at.isoformat(),
            ev.user_id,
            getattr(ev.user, "username", ""),
            ev.skill_id,
            getattr(ev.skill, "name", "") if ev.skill_id else "",
            ev.amount,
            getattr(ev, "source", ""),
            getattr(ev, "reason", ""),
        ])

    return resp

# --- Skill Leaderboard -----------------------------------------------------

@extend_schema(responses=LeaderboardEntrySerializer(many=True))
@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def skill_leaderboard(request, skill_id):
    """
    Leaderboard for a single skill within the current org.
    """
    qs = (
        _org_xp_queryset(request)
        .filter(skill_id=skill_id)
        .values("user_id", "user__username")
        .annotate(overall_xp=Sum("amount"))
        .order_by("-overall_xp")
    )

    results = []
    for rank, row in enumerate(qs, start=1):
        xp = row["overall_xp"] or 0
        results.append({
            "rank": rank,
            "user_id": row["user_id"],
            "username": row["user__username"],
            "overall_xp": xp,
            "level": level_from_total_xp(xp),
        })
    return response.Response(results)

# --- Role Leaderboard ------------------------------------------------------

@extend_schema(responses=LeaderboardEntrySerializer(many=True))
@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def role_leaderboard(request, role_id):
    """
    Leaderboard for users assigned to a given JobRole (all skills).
    """
    # Import here to avoid circulars
    from learning.models import RoleAssignment

    user_ids = list(
        RoleAssignment.objects
        .filter(role_id=role_id)
        .values_list("user_id", flat=True)
    )

    qs = (
        _org_xp_queryset(request)
        .filter(user_id__in=user_ids)
        .values("user_id", "user__username")
        .annotate(overall_xp=Sum("amount"))
        .order_by("-overall_xp")
    )

    results = []
    for rank, row in enumerate(qs, start=1):
        xp = row["overall_xp"] or 0
        results.append({
            "rank": rank,
            "user_id": row["user_id"],
            "username": row["user__username"],
            "overall_xp": xp,
            "level": level_from_total_xp(xp),
        })
    return response.Response(results)

# --- Group (Department/Team) Leaderboard -----------------------------------

@extend_schema(
    description="Leaderboard grouped by Department and Team (within current org).",
    responses={"200": {"type": "object", "properties": {
        "departments": {"type": "array", "items": {"type": "object"}},
        "teams": {"type": "array", "items": {"type": "object"}},
    }}},
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def org_leaderboard_by_group(request):
    org_id = _org_id(request)
    # Teams: sum XP of active members
    team_rows = (XPEvent.objects
                 .filter(org_id=org_id)
                 .values("user_id")
                 .annotate(xp=Sum("amount")))
    # Map user -> xp
    user_xp = {r["user_id"]: r["xp"] or 0 for r in team_rows}

    # Team XP
    teams = (Team.objects
             .select_related("department")
             .filter(org_id=org_id))
    team_payload = []
    for t in teams:
        member_ids = list(TeamMember.objects.filter(team=t, active=True).values_list("user_id", flat=True))
        total = sum(user_xp.get(uid, 0) for uid in member_ids)
        team_payload.append({
            "team_id": str(t.id),
            "team_name": t.name,
            "department_id": str(getattr(t.department, "id", "")) if t.department_id else None,
            "department_name": getattr(t.department, "name", None),
            "overall_xp": total,
            "level": level_from_total_xp(total),
        })

    # Department XP = sum of its teams (or members)
    # Faster to roll-up from team_payload:
    dept_map = {}
    for tp in team_payload:
        did = tp["department_id"]
        if not did:
            continue
        if did not in dept_map:
            dept_map[did] = {
                "department_id": did,
                "department_name": tp["department_name"],
                "overall_xp": 0,
            }
        dept_map[did]["overall_xp"] += tp["overall_xp"]
    dept_payload = []
    for did, d in dept_map.items():
        d["level"] = level_from_total_xp(d["overall_xp"])
        dept_payload.append(d)

    # Order both by xp desc
    team_payload.sort(key=lambda x: x["overall_xp"], reverse=True)
    dept_payload.sort(key=lambda x: x["overall_xp"], reverse=True)

    return response.Response({
        "departments": dept_payload,
        "teams": team_payload,
    })
# -----------------------------------------------------------------------------
# 9) WhoAmI endpoint for Swagger banner / UI
# -----------------------------------------------------------------------------
@extend_schema(responses=WhoAmISerializer)
@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def whoami(request):
    """Return logged-in user's username and biz_role."""
    return response.Response(
        {
            "username": request.user.username,
            "biz_role": getattr(request.user, "biz_role", None),
        }
    )

@extend_schema(
    responses=RecertRequirementSerializer(many=True),
    description="List recert requirements for the current user that are overdue (due_at < now)."
)
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def my_overdue_sops(request):
    """
    Return recertification requirements that are past their due date for the
    currently authenticated user.
    """
    now = timezone.now()

    qs = (
        RecertRequirement.objects
        .select_related("user", "skill", "org")
        .filter(
            user=request.user,
            org=getattr(request.user, "org", None),
            due_at__lt=now,
        )
        .order_by("due_at")
    )

    data = RecertRequirementSerializer(qs, many=True).data
    return response.Response(data)



@extend_schema(
    responses=StartAttemptSerializer,
    description="Start a quiz attempt: backend selects & shuffles questions/choices. Returns attempt_id and the served questions.",
)
@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.IsAuthenticated])
def start_module_attempt(request, module_id: str):
    """
    Gated by SOP view completion (if module.require_viewed).
    Randomises question pool and choice order; stores them on the attempt.
    """
    try:
        module = Module.objects.get(id=module_id, active=True)
    except Module.DoesNotExist:
        raise ValidationError("Module not found or inactive.")

    # Require viewed SOP?
    if module.require_viewed and module.sop_id:
        viewed_ok = SOPView.objects.filter(sop_id=module.sop_id, user=request.user, completed=True).exists()
        if not viewed_ok:
            raise PermissionDenied("Please view the SOP media before starting the quiz.")

    # Load questions + choices
    qs = list(module.questions.prefetch_related("choices").all())

    # Pool selection
    if module.question_pool_count and module.question_pool_count < len(qs):
        qs = random.sample(qs, k=module.question_pool_count)

    # Shuffle questions
    if module.shuffle_questions:
        random.shuffle(qs)

    # Build deterministic choice order per question (possibly shuffled)
    choice_order = {}
    for q in qs:
        choices = list(q.choices.all())
        if module.shuffle_choices:
            random.shuffle(choices)
        choice_order[str(q.id)] = [str(c.id) for c in choices]

    # Create attempt
    attempt = ModuleAttempt.objects.create(
        user=request.user,
        module=module,
        answers={},  # will fill on submit
        presented_questions=[str(q.id) for q in qs],
        choice_order=choice_order,
    )

    # Serialize questions in the chosen order (without exposing is_correct)
    # Reorder choices to match choice_order
    public_questions = []
    for q in qs:
        ordered_ids = choice_order[str(q.id)]
        ordered_choices = [c for cid in ordered_ids for c in q.choices.all() if str(c.id) == cid]
        # hint serializer to use the ordered choices
        q._prefetched_objects_cache = {"choices": ordered_choices}
        public_questions.append(q)

    payload = {
        "attempt_id": attempt.id,
        "module_id": module.id,
        "questions": QuestionPublicSerializer(public_questions, many=True).data,
    }
    return response.Response(payload, status=status.HTTP_200_OK)

@extend_schema(
    responses=NextQuestionSerializer,
    description="Get the next unanswered question for an attempt, based on presented_questions."
)
@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def next_question(request, attempt_id: str):
    try:
        attempt = ModuleAttempt.objects.select_related("module").get(
            id=attempt_id, user=request.user
        )
    except ModuleAttempt.DoesNotExist:
        raise ValidationError("Attempt not found.")

    q, remaining, total = _get_next_unanswered_question(attempt)

    if not q:
        # No more questions
        payload = {
            "attempt_id": attempt.id,
            "question": None,
            "remaining": 0,
            "total": total,
        }
        return response.Response(payload, status=status.HTTP_200_OK)

    # Respect stored choice order from attempt.choice_order
    choice_order = attempt.choice_order or {}
    ordered_ids = choice_order.get(str(q.id)) or [str(c.id) for c in q.choices.all()]
    ordered_choices = [c for cid in ordered_ids for c in q.choices.all() if str(c.id) == cid]
    q._prefetched_objects_cache = {"choices": ordered_choices}

    payload = {
        "attempt_id": attempt.id,
        "question": QuestionPublicSerializer(q).data,
        "remaining": remaining,
        "total": total,
    }
    return response.Response(payload, status=status.HTTP_200_OK)

@extend_schema(responses=SOPViewSerializer(many=True))
@decorators.api_view(["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
def my_sop_views(request):
    """
    Return SOPView records for the current user (per-SOP progress).
    """
    qs = SOPView.objects.filter(user=request.user).select_related("sop")
    return response.Response(SOPViewSerializer(qs, many=True).data)

@extend_schema(
    request=SubmitAttemptRequestSerializer,  # legacy; new flow also works
    responses={
        "200": {
            "type": "object",
            "properties": {
                "attempt_id": {"type": "string", "format": "uuid"},
                "percent": {"type": "integer"},
                "passed": {"type": "boolean"},
                "score": {"type": "number"},
                "max_score": {"type": "number"},
                "feedback": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question_id": {"type": "string", "format": "uuid"},
                            "earned": {"type": "number"},
                            "max": {"type": "number"},
                            "correct": {"type": "boolean"},
                            "message": {"type": "string"},
                        },
                    },
                },
            },
        }
    },
    description=(
        "Submit answers for an attempt. "
        "Supports both legacy all-at-once payloads (answers=[...]) "
        "and new per-question payloads (question_id + choice_ids)."
    ),
)
@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.IsAuthenticated])
def submit_started_attempt(request, attempt_id: str):
    """
    Hybrid submit endpoint:

    - If request.data contains 'answers' (list) -> legacy all-at-once scoring
    - Else expects single-question payload:
        {question_id, choice_ids, time_taken?}
    """
    try:
        attempt = ModuleAttempt.objects.select_related("module").get(
            id=attempt_id, user=request.user
        )
    except ModuleAttempt.DoesNotExist:
        raise ValidationError("Attempt not found.")

    module = attempt.module
    data = request.data or {}

    # ------------------------------------------------------------------
    # 1) Legacy mode: answers = [...]
    # ------------------------------------------------------------------
    if isinstance(data.get("answers"), list):
        answers = data["answers"]

        presented_ids = [str(x) for x in (attempt.presented_questions or [])]
        if not presented_ids:
            raise ValidationError("Attempt has no presented questions. Start again.")

        # Map question_id -> Question with choices
        questions = list(
            module.questions.prefetch_related("choices").filter(id__in=presented_ids)
        )
        q_map = {str(q.id): q for q in questions}

        chosen_map = {}
        for a in answers:
            qid = str(a.get("question_id"))
            cids = [str(cid) for cid in (a.get("choice_ids") or [])]
            chosen_map[qid] = set(cids)

        total_earned = 0.0
        total_max = 0.0
        feedback = []

        for qid in presented_ids:
            q = q_map.get(qid)
            if not q:
                continue

            max_pts = float(q.points)
            total_max += max_pts

            correct_ids = {str(c.id) for c in q.choices.filter(is_correct=True)}
            wrong_ids = {str(c.id) for c in q.choices.filter(is_correct=False)}
            chosen = chosen_map.get(qid, set())

            earned = 0.0
            correct_flag = False
            msg = ""

            if q.qtype in ("single", "truefalse"):
                if len(chosen) == 1 and next(iter(chosen)) in correct_ids:
                    earned = max_pts
                    correct_flag = True
                else:
                    earned = 0.0
                msg = q.explanation or ("Correct." if correct_flag else "Incorrect.")
            else:
                total_correct = len(correct_ids)
                sel_correct = len(chosen & correct_ids)
                sel_wrong = len(chosen & wrong_ids)

                if total_correct == 0:
                    earned = 0.0
                    correct_flag = False
                    msg = "No correct choices configured."
                else:
                    fraction = sel_correct / total_correct
                    if module.negative_marking:
                        fraction -= sel_wrong / max(1, len(wrong_ids))
                    fraction = max(0.0, min(1.0, fraction))
                    earned = round(max_pts * fraction, 2)
                    correct_flag = fraction == 1.0 and sel_wrong == 0

                    if sel_wrong and module.negative_marking:
                        msg = "Some incorrect choices selected."
                    elif sel_correct < total_correct:
                        msg = "You missed some correct choices."
                    else:
                        msg = "Correct."
                    if q.explanation:
                        msg = f"{msg} {q.explanation}"

            total_earned += earned
            feedback.append(
                {
                    "question_id": qid,
                    "earned": earned,
                    "max": max_pts,
                    "correct": correct_flag,
                    "message": msg,
                }
            )

        percent = int(round((total_earned / total_max) * 100)) if total_max > 0 else 0
        passed = percent >= (module.pass_mark or module.passing_score)

        attempt.completed_at = timezone.now()
        attempt.passed = passed
        attempt.score = percent
        attempt.answers = {
            qid: list(chosen_map.get(qid, set())) for qid in presented_ids
        }
        attempt.save()

        return response.Response(
            {
                "attempt_id": str(attempt.id),
                "percent": percent,
                "passed": passed,
                "score": total_earned,
                "max_score": total_max,
                "feedback": feedback,
            },
            status=status.HTTP_200_OK,
        )

    # ------------------------------------------------------------------
    # 2) New mode: single-question submit
    # ------------------------------------------------------------------
    # At this point, we expect question_id + choice_ids
    from learning.models import ModuleAttemptQuestion  # local import to avoid circular

    req = SingleAnswerRequestSerializer(data=data)
    req.is_valid(raise_exception=True)

    qid_str = str(req.validated_data["question_id"])
    choice_ids = [str(cid) for cid in req.validated_data.get("choice_ids") or []]
    time_taken = float(req.validated_data.get("time_taken") or 0.0)

    presented_ids = [str(x) for x in (attempt.presented_questions or [])]
    if qid_str not in presented_ids:
        raise ValidationError("Question not part of this attempt.")

    try:
        q = module.questions.prefetch_related("choices").get(id=qid_str)
    except Question.DoesNotExist:
        raise ValidationError("Question not found for this module.")

    max_pts = float(q.points)
    correct_ids = {str(c.id) for c in q.choices.filter(is_correct=True)}
    wrong_ids = {str(c.id) for c in q.choices.filter(is_correct=False)}
    chosen = set(choice_ids)

    earned = 0.0
    correct_flag = False
    msg = ""

    if q.qtype in ("single", "truefalse"):
        if len(chosen) == 1 and next(iter(chosen)) in correct_ids:
            earned = max_pts
            correct_flag = True
        else:
            earned = 0.0
        msg = q.explanation or ("Correct." if correct_flag else "Incorrect.")
    else:
        total_correct = len(correct_ids)
        sel_correct = len(chosen & correct_ids)
        sel_wrong = len(chosen & wrong_ids)

        if total_correct == 0:
            earned = 0.0
            correct_flag = False
            msg = "No correct choices configured."
        else:
            fraction = sel_correct / total_correct
            if module.negative_marking:
                fraction -= sel_wrong / max(1, len(wrong_ids))
            fraction = max(0.0, min(1.0, fraction))
            earned = round(max_pts * fraction, 2)
            correct_flag = fraction == 1.0 and sel_wrong == 0

            if sel_wrong and module.negative_marking:
                msg = "Some incorrect choices selected."
            elif sel_correct < total_correct:
                msg = "You missed some correct choices."
            else:
                msg = "Correct."
            if q.explanation:
                msg = f"{msg} {q.explanation}"

    # Upsert ModuleAttemptQuestion
    maq, created = ModuleAttemptQuestion.objects.get_or_create(
        attempt=attempt,
        question=q,
        defaults={
            "selection_history": [],
            "final_choices": [],
            "correct": False,
            "points_awarded": 0,
            "time_taken": 0.0,
            "changed_answer": False,
        },
    )

    history = maq.selection_history or []
    history.append(
        {
            "choice_ids": choice_ids,
            "timestamp": timezone.now().isoformat(),
            "time_taken": time_taken,
        }
    )

    maq.selection_history = history
    maq.final_choices = choice_ids
    maq.correct = correct_flag
    maq.points_awarded = earned
    maq.time_taken = (maq.time_taken or 0.0) + time_taken
    maq.changed_answer = len(history) > 1
    maq.save()

    # Update attempt.answers for backwards compatibility
    answers_map = attempt.answers or {}
    answers_map[qid_str] = choice_ids
    attempt.answers = answers_map
    attempt.save(update_fields=["answers"])

    # Check if all questions answered
    presented_set = set(presented_ids)
    answered_set = set(str(x) for x in attempt.attempt_questions.values_list("question_id", flat=True))
    all_answered = presented_set.issubset(answered_set)

    completed = False
    if all_answered and not attempt.completed_at:
        # Compute overall score from ModuleAttemptQuestion
        aqs = list(attempt.attempt_questions.select_related("question").all())
        total_earned = sum(aq.points_awarded for aq in aqs)
        total_max = sum(float(aq.question.points) for aq in aqs) or 1.0
        percent = int(round((total_earned / total_max) * 100))

        attempt.score = percent
        attempt.passed = percent >= (module.pass_mark or module.passing_score)
        attempt.completed_at = timezone.now()
        attempt.save(update_fields=["score", "passed", "completed_at"])
        completed = True  # XP awarded by ModuleAttempt post_save signal

    # Apply feedback_mode
    mode = module.feedback_mode or "end"
    include_feedback = False

    if mode == "immediate":
        include_feedback = True
    elif mode == "mixed" and q.qtype in ("single", "truefalse"):
        include_feedback = True
    elif mode == "none":
        include_feedback = False
    # mode == "end" → no per-question feedback, only final summary

    resp_payload = {
        "attempt_id": str(attempt.id),
        "question_id": qid_str,
        "completed": completed,
        "remaining": max(0, len(presented_ids) - len(answered_set)),
    }

    if include_feedback:
        resp_payload.update(
            {
                "correct": correct_flag,
                "earned": earned,
                "max_points": max_pts,
                "message": msg,
            }
        )

    return response.Response(resp_payload, status=status.HTTP_200_OK)

@extend_schema(
    responses={
        "200": {
            "type": "object",
            "properties": {
                "attempt_id": {"type": "string", "format": "uuid"},
                "percent": {"type": "integer"},
                "passed": {"type": "boolean"},
                "score": {"type": "number"},
                "max_score": {"type": "number"},
                "feedback": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question_id": {"type": "string", "format": "uuid"},
                            "earned": {"type": "number"},
                            "max": {"type": "number"},
                            "correct": {"type": "boolean"},
                            "message": {"type": "string"},
                        },
                    },
                },
            },
        }
    },
    description="Finalise an attempt and return overall result + per-question feedback.",
)
@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.IsAuthenticated])
def finish_attempt(request, attempt_id: str):
    """
    Finalise an attempt (if not already) and return a full feedback summary.

    Uses ModuleAttemptQuestion for per-question scores and correctness.
    """
    try:
        attempt = ModuleAttempt.objects.select_related("module").get(
            id=attempt_id, user=request.user
        )
    except ModuleAttempt.DoesNotExist:
        raise ValidationError("Attempt not found.")

    module = attempt.module
    presented_ids = [str(x) for x in (attempt.presented_questions or [])]
    if not presented_ids:
        raise ValidationError("Attempt has no presented questions.")

    # Load questions with choices
    questions = list(
        module.questions.prefetch_related("choices").filter(id__in=presented_ids)
    )
    q_map = {str(q.id): q for q in questions}

    # Map question_id -> ModuleAttemptQuestion
    from learning.models import ModuleAttemptQuestion

    maq_qs = ModuleAttemptQuestion.objects.filter(attempt=attempt)
    maq_map = {str(aq.question_id): aq for aq in maq_qs}

    total_earned = 0.0
    total_max = 0.0
    feedback = []

    for qid in presented_ids:
        q = q_map.get(qid)
        if not q:
            continue

        max_pts = float(q.points)
        total_max += max_pts

        aq = maq_map.get(qid)
        if not aq:
            # unanswered question
            feedback.append(
                {
                    "question_id": qid,
                    "earned": 0.0,
                    "max": max_pts,
                    "correct": False,
                    "message": "Not answered.",
                }
            )
            continue

        total_earned += aq.points_awarded
        correct_flag = aq.correct
        chosen = set(aq.final_choices or [])

        correct_ids = {str(c.id) for c in q.choices.filter(is_correct=True)}
        wrong_ids = {str(c.id) for c in q.choices.filter(is_correct=False)}

        # Rebuild a human message, similar to old submit_started_attempt
        if q.qtype in ("single", "truefalse"):
            msg = q.explanation or ("Correct." if correct_flag else "Incorrect.")
        else:
            total_correct = len(correct_ids)
            sel_correct = len(chosen & correct_ids)
            sel_wrong = len(chosen & wrong_ids)

            if total_correct == 0:
                msg = "No correct choices configured."
            else:
                if sel_wrong and module.negative_marking:
                    msg = "Some incorrect choices selected."
                elif sel_correct < total_correct:
                    msg = "You missed some correct choices."
                else:
                    msg = "Correct."
                if q.explanation:
                    msg = f"{msg} {q.explanation}"

        feedback.append(
            {
                "question_id": qid,
                "earned": aq.points_awarded,
                "max": max_pts,
                "correct": correct_flag,
                "message": msg,
            }
        )

    percent = int(round((total_earned / total_max) * 100)) if total_max > 0 else 0
    passed = percent >= (module.pass_mark or module.passing_score)

    # Finalise attempt if not already done
    if not attempt.completed_at:
        attempt.score = percent
        attempt.passed = passed
        attempt.completed_at = timezone.now()
        attempt.save(update_fields=["score", "passed", "completed_at"])
        # XP is still awarded by your existing post_save signal on ModuleAttempt

    return response.Response(
        {
            "attempt_id": str(attempt.id),
            "percent": percent,
            "passed": passed,
            "score": total_earned,
            "max_score": total_max,
            "feedback": feedback,
        },
        status=status.HTTP_200_OK,
    )

@extend_schema(responses=ManagerDashboardSerializer)
@decorators.api_view(["GET"])
@decorators.permission_classes([IsManagerOnly])
def manager_dashboard(request):
    """
    Simple org-level dashboard for managers/admins.
    Shows high-level training and XP stats for the current org.
    """
    user = request.user
    org_id = getattr(user, "org_id", None)

    users_qs = User.objects.all()
    modules_qs = Module.objects.all()
    attempts_qs = ModuleAttempt.objects.all()
    xp_qs = XPEvent.objects.all()

    if org_id:
        users_qs = users_qs.filter(org_id=org_id)
        modules_qs = modules_qs.filter(org_id=org_id)
        attempts_qs = attempts_qs.filter(module__org_id=org_id)
        xp_qs = xp_qs.filter(org_id=org_id)

    now = timezone.now()
    since_30 = now - timedelta(days=30)

    total_users = users_qs.count()
    active_modules = modules_qs.filter(active=True).count()
    total_attempts = attempts_qs.count()
    pass_count = attempts_qs.filter(passed=True).count()
    pass_rate = float(round(pass_count * 100.0 / total_attempts, 1)) if total_attempts else 0.0
    attempts_last_30 = attempts_qs.filter(created_at__gte=since_30).count()
    total_xp = xp_qs.aggregate(s=Sum("amount"))["s"] or 0
    avg_score_all = attempts_qs.aggregate(avg=Avg("score"))["avg"] or 0.0
    avg_score_all = float(round(avg_score_all, 1))

    payload = {
        "total_users": total_users,
        "active_modules": active_modules,
        "total_attempts": total_attempts,
        "pass_count": pass_count,
        "pass_rate": pass_rate,
        "attempts_last_30_days": attempts_last_30,
        "total_xp": int(total_xp),
        "avg_score": avg_score_all,
    }

    ser = ManagerDashboardSerializer(payload)
    return response.Response(ser.data)

##### Badges
@extend_schema(
    description="Summary of badge rules in this org, including how many users hold each badge."
)
@api_view(["GET"])
@permission_classes([IsManagerForWrites])
def manager_badge_rules(request):
    """
    For managers: see all badge rules plus holder counts and sample users.
    """
    user = request.user
    org = getattr(user, "org", None)

    qs = (
        Badge.objects
        .select_related("skill", "team", "department")
    )

    # Scope to manager's org if present
    if org is not None:
        qs = qs.filter(org=org)

    # Annotate with how many users hold each badge
    qs = qs.annotate(holder_count=Count("userbadge"))

    rows = []
    for badge in qs:
        # Grab up to 3 example holders (newest first)
        holders_qs = (
            UserBadge.objects
            .filter(badge=badge)
            .select_related("user")
            .order_by("-awarded_at")[:3]
        )
        sample_holders = [ub.user.username for ub in holders_qs]

        rows.append(
            {
                "badge": BadgeSerializer(badge).data,
                "holder_count": badge.holder_count or 0,
                "sample_holders": sample_holders,
            }
        )

    return response.Response(rows)

@extend_schema(
    responses=UserBadgeSerializer(many=True),
    description="List badges awarded to the current user."
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_badges(request):
    """
    Return all UserBadge records for the currently authenticated user.
    """
    qs = (
        UserBadge.objects
        .filter(user=request.user)
        .select_related("badge", "badge__skill", "badge__team", "badge__department")
        .order_by("-awarded_at")
    )
    serializer = UserBadgeSerializer(qs, many=True)
    return response.Response(serializer.data)

    @extend_schema(
        responses=UserBadgeSerializer(many=True),
        description="List badges awarded to the currently authenticated user.",
    )
    @api_view(["GET"])
    @permission_classes([permissions.IsAuthenticated])
    def my_badges(request):
        """
        Return UserBadge rows for the current user.
        """
        qs = (
            UserBadge.objects
            .filter(user=request.user)
            .select_related("badge", "badge__skill", "badge__team", "badge__department")
            .order_by("-awarded_at")
        )
        data = UserBadgeSerializer(qs, many=True).data
        return response.Response(data)
