from django.urls import include, path
from rest_framework.routers import DefaultRouter

# Import ViewSets & function views
from .views import (
    BadgeViewSet,
    DepartmentViewSet,
    JobRoleViewSet,
    LevelDefViewSet,
    ModuleAttemptViewSet,
    ModuleViewSet,
    # --- ViewSets ---
    OrgViewSet,
    RecertRequirementViewSet,
    RoleAssignmentViewSet,
    RoleSkillViewSet,
    SkillViewSet,
    SOPViewSet,
    StartModuleAttemptView,
    manager_dashboard,
    my_dashboard,
    start_module_attempt,
    submit_started_attempt,   # now per-question
    next_question,
    finish_attempt,
    TrainingPathwayViewSet,
    MyTrainingPathwaysView,
    MyModuleAttemptsView,
    MyOverdueSOPsView,
    SupervisorSignoffViewSet,
    TeamMemberViewSet,
    TeamViewSet,
    UserBadgeViewSet,
    UserViewSet,
    XPEventViewSet,
    leaderboard,
    # --- Function endpoints (core) ---
    my_sop_views,
    my_progress,
    sop_view_heartbeat,
    my_overdue_sops, 
    start_module_attempt,
    submit_started_attempt,
    # --- Optional extras (leave commented if not implemented) ---
    leaderboard_csv, xp_events_csv,
    skill_leaderboard, role_leaderboard, org_leaderboard_by_group,
    whoami,
)
app_name = "api"
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
router.register(r"training-pathways", TrainingPathwayViewSet, basename="training-pathways")

urlpatterns = [
    # Router-driven endpoints
    path("", include(router.urls)),
    # --- Core function endpoints ---
    path("my-progress/", my_progress, name="my-progress"),
    path("me/whoami/", whoami, name="whoami"),  # username + role (used by Swagger banner)
    path("me/sop-views/", my_sop_views),
    path(
        "me/overdue-sops/",
        MyOverdueSOPsView.as_view(),
        name="me-overdue-sops",
    ),
    path("me/training-pathways/", MyTrainingPathwaysView.as_view(), name="my-training-pathways"),
    path("", include(router.urls)),
    path("sops/<uuid:sop_id>/view/", sop_view_heartbeat),  # media viewed heartbeat/complete
    # Start → Submit quiz flow (randomised/shuffled/negative marking)
    path("modules/<uuid:module_id>/start/", start_module_attempt),  # returns attempt_id + served questions
    path("modules/<uuid:module_id>/attempt/start/", start_module_attempt, name="start-module-attempt"),
    path("attempts/<uuid:attempt_id>/next/", next_question, name="next-question"),
    path("attempts/<uuid:attempt_id>/submit/", submit_started_attempt, name="submit-question"),
    path("attempts/<uuid:attempt_id>/finish/", finish_attempt, name="finish-attempt"),
    path("manager/dashboard/", manager_dashboard, name="manager-dashboard"),
    path("me/dashboard/", my_dashboard, name="my-dashboard"),
    path("me/module-attempts/", MyModuleAttemptsView.as_view(), name="my-module-attempts"),
    # Simple org leaderboard
    path("leaderboard/", leaderboard),
    # --- Optional extras (uncomment if you added these views) ---
    # CSV exports:
    path("leaderboard.csv", leaderboard_csv),
    path("xp/export.csv", xp_events_csv),
    # Extra leaderboards:
    path("leaderboard/skill/<uuid:skill_id>/", skill_leaderboard),
    path("leaderboard/role/<uuid:role_id>/", role_leaderboard),
    path("leaderboard/group/", org_leaderboard_by_group),   # department/team scoped
]
