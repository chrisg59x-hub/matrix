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
from django.db.models import Sum #Count, F
from drf_spectacular.utils import extend_schema    #, OpenApiParameter
from rest_framework.decorators import api_view, permission_classes
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
    Skill,
    SupervisorSignoff,
    Team,
    TeamMember,
    UserBadge,
    XPEvent,
)
from rest_framework import decorators, permissions, response, status, viewsets, filters
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied, ValidationError
from sops.models import SOP, SOPView

# -----------------------------------------------------------------------------
# 4) Permissions
# -----------------------------------------------------------------------------
from .permissions import IsManagerForWrites

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
    ModuleSerializer,
    OrgSerializer,
    ProgressSerializer,
    QuestionPublicSerializer,
    RecertRequirementSerializer,
    RoleAssignmentSerializer,
    RoleSkillSerializer,
    SkillSerializer,
    SOPSerializer,
    SOPViewSerializer,
    StartAttemptSerializer,
    SubmitAttemptRequestSerializer,
    SupervisorSignoffSerializer,
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


class ModuleAttemptViewSet(viewsets.ModelViewSet):
    queryset = ModuleAttempt.objects.select_related("module", "user")
    serializer_class = ModuleAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]


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










# -----------------------------------------------------------------------------
# 8) Quizzes / Module Attempts
#    (uses start_module_attempt & submit_started_attempt already implemented)
# -----------------------------------------------------------------------------
# NOTE: your detailed implementations for start_module_attempt() and
#       submit_started_attempt() remain unchanged — keep them here below.
#       Include @extend_schema annotations as shown earlier.

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
    request=SubmitAttemptRequestSerializer,
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
)
@decorators.api_view(["POST"])
@decorators.permission_classes([permissions.IsAuthenticated])
def submit_started_attempt(request, attempt_id: str):
    """
    Submit answers for a started attempt.
    Supports negative marking for multi-select & returns per-question feedback.
    """
    try:
        attempt = ModuleAttempt.objects.select_related("module").get(id=attempt_id, user=request.user)
    except ModuleAttempt.DoesNotExist:
        raise ValidationError("Attempt not found.")

    module = attempt.module

    presented_ids = [str(x) for x in (attempt.presented_questions or [])]
    if not presented_ids:
        raise ValidationError("Attempt has no presented questions. Start again.")

    # Build map question_id -> Question (with choices)
    questions = list(module.questions.prefetch_related("choices").filter(id__in=presented_ids))
    q_map = {str(q.id): q for q in questions}

    # Payload
    data = request.data or {}
    answers = data.get("answers", [])
    if not isinstance(answers, list):
        raise ValidationError("answers must be an array.")

    # Normalize choices selected
    chosen_map = {}
    for a in answers:
        qid = str(a.get("question_id"))
        cids = [str(cid) for cid in (a.get("choice_ids") or [])]
        chosen_map[qid] = set(cids)

    # Score
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
            # Multi-select with optional negative marking
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

    # Finalise attempt
    attempt.completed_at = timezone.now()
    attempt.passed = passed
    attempt.score = percent
    attempt.answers = {qid: list(chosen_map.get(qid, set())) for qid in presented_ids}
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
