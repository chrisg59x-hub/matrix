from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import ViewSets & function views
from .views import (
    # --- ViewSets ---
    OrgViewSet, UserViewSet, SOPViewSet, SkillViewSet, JobRoleViewSet, RoleSkillViewSet,
    ModuleViewSet, ModuleAttemptViewSet, XPEventViewSet, SupervisorSignoffViewSet,
    RecertRequirementViewSet, LevelDefViewSet, BadgeViewSet, UserBadgeViewSet,
    DepartmentViewSet, TeamViewSet, TeamMemberViewSet, RoleAssignmentViewSet,
    # --- Function endpoints (core) ---
    my_progress, leaderboard, whoami, sop_view_heartbeat,
    start_module_attempt, submit_started_attempt,
    # --- Optional extras (leave commented if not implemented) ---
    # leaderboard_csv, xp_events_csv,
    # skill_leaderboard, role_leaderboard, org_leaderboard_by_group,
)

router = DefaultRouter()

# --- Core CRUD/API routes (ViewSets) ---
router.register(r"orgs", OrgViewSet)
router.register(r"users", UserViewSet, basename="users")
router.register(r"sops", SOPViewSet)
router.register(r"skills", SkillViewSet)
router.register(r"roles", JobRoleViewSet)
router.register(r"role-skills", RoleSkillViewSet)
router.register(r"modules", ModuleViewSet)
router.register(r"attempts", ModuleAttemptViewSet)
router.register(r"xp", XPEventViewSet, basename="xp")
router.register(r"signoffs", SupervisorSignoffViewSet)
router.register(r"recerts", RecertRequirementViewSet)
router.register(r"levels", LevelDefViewSet, basename="levels")
router.register(r"badges", BadgeViewSet)
router.register(r"user-badges", UserBadgeViewSet)
router.register(r"departments", DepartmentViewSet)
router.register(r"teams", TeamViewSet)
router.register(r"team-members", TeamMemberViewSet)
router.register(r"role-assignments", RoleAssignmentViewSet)

urlpatterns = [
    # Router-driven endpoints
    path("", include(router.urls)),

    # --- Core function endpoints ---
    path("me/progress/", my_progress),                              # current user's XP/level/skills
    path("me/whoami/", whoami),                                     # username + role (used by Swagger banner)
    path("sops/<uuid:sop_id>/view/", sop_view_heartbeat),           # media viewed heartbeat/complete

    # Start → Submit quiz flow (randomised/shuffled/negative marking)
    path("modules/<uuid:module_id>/start/", start_module_attempt),  # returns attempt_id + served questions
    path("attempts/<uuid:attempt_id>/submit/", submit_started_attempt),

    # Simple org leaderboard
    path("leaderboard/", leaderboard),

    # --- Optional extras (uncomment if you added these views) ---
    # CSV exports:
    # path("leaderboard.csv", leaderboard_csv),
    # path("xp/export.csv", xp_events_csv),

    # Extra leaderboards:
    # path("leaderboard/skill/<uuid:skill_id>/", skill_leaderboard),
    # path("leaderboard/role/<uuid:role_id>/", role_leaderboard),
    # path("leaderboard/group/", org_leaderboard_by_group),   # department/team scoped
]
