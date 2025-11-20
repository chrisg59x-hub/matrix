from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

# Router-based CRUD endpoints
router.register(r"orgs", views.OrgViewSet)
router.register(r"users", views.UserViewSet)
router.register(r"sops", views.SOPViewSet)
router.register(r"skills", views.SkillViewSet)
router.register(r"roles", views.JobRoleViewSet)
router.register(r"role-skills", views.RoleSkillViewSet)
router.register(r"modules", views.ModuleViewSet)
router.register(r"attempts", views.ModuleAttemptViewSet)
router.register(r"xp", views.XPEventViewSet)
router.register(r"signoffs", views.SupervisorSignoffViewSet)
router.register(r"recerts", views.RecertRequirementViewSet)
router.register(r"levels", views.LevelDefViewSet)
router.register(r"badges", views.BadgeViewSet)
router.register(r"user-badges", views.UserBadgeViewSet)
router.register(r"departments", views.DepartmentViewSet)
router.register(r"teams", views.TeamViewSet)
router.register(r"team-members", views.TeamMemberViewSet)
router.register(r"role-assignments", views.RoleAssignmentViewSet)
router.register(r"training-pathways", views.TrainingPathwayViewSet)

urlpatterns = [
    # All the router-driven viewsets:
    path("", include(router.urls)),

    # -------------------------------------------------------------------------
    # Me / progress / dashboards
    # -------------------------------------------------------------------------
    path("my-progress/", views.my_progress, name="my-progress"),
    path("my_progress/", views.my_progress, name="my-progress-underscore"),

    path("me/whoami/", views.whoami, name="whoami"),
    path("me/sop-views/", views.my_sop_views),

    # Overdue recerts for current user
    path(
        "me/overdue-sops/",
        views.MeOverdueSopsView.as_view(),
        name="me-overdue-sops",
    ),

    # Training pathways for current user
    path(
        "me/training-pathways/",
        views.MyTrainingPathwaysView.as_view(),
        name="my-training-pathways",
    ),

    # Personal dashboard & attempts
    path("me/dashboard/", views.my_dashboard, name="my-dashboard"),
    path(
        "me/module-attempts/",
        views.MyModuleAttemptsView.as_view(),
        name="my-module-attempts",
    ),

    # -------------------------------------------------------------------------
    # SOP media tracking
    # -------------------------------------------------------------------------
    path("sops/<uuid:sop_id>/view/", views.sop_view_heartbeat),

    # -------------------------------------------------------------------------
    # Quiz / module attempt engine (per-question flow)
    # -------------------------------------------------------------------------
    # Start a module attempt → returns attempt_id + served questions
    path(
        "modules/<uuid:module_id>/attempt/start/",
        views.start_module_attempt,
        name="start-module-attempt",
    ),
    # Optional alias kept for backwards compatibility
    path(
        "modules/<uuid:module_id>/start/",
        views.start_module_attempt,
    ),

    # Per-question navigation
    path(
        "attempts/<uuid:attempt_id>/next/",
        views.next_question,
        name="next-question",
    ),
    path(
        "attempts/<uuid:attempt_id>/submit/",
        views.submit_question,
        name="submit-question",
    ),
    path(
        "attempts/<uuid:attempt_id>/finish/",
        views.finish_attempt,
        name="finish-attempt",
    ),

    # Attempt review (used by the frontend review page)
    path(
        "attempts/<uuid:attempt_id>/review/",
        views.attempt_review,
        name="attempt-review",
    ),

    # Optional legacy endpoint: whole-attempt submit in one go
    path(
        "attempts/<uuid:attempt_id>/submit-all/",
        views.submit_started_attempt,
        name="submit-started-attempt",
    ),

    # -------------------------------------------------------------------------
    # Manager dashboards
    # -------------------------------------------------------------------------
    path(
        "manager/dashboard/",
        views.manager_dashboard,
        name="manager-dashboard",
    ),

    # (We’ll wire /manager/badges/ & /me/badges/ once the views are in place)

    # -------------------------------------------------------------------------
    # Leaderboards & CSV exports
    # -------------------------------------------------------------------------
    path("leaderboard/", views.leaderboard),
    path("leaderboard.csv", views.leaderboard_csv),
    path("xp/export.csv", views.xp_events_csv),

    path(
        "leaderboard/skill/<uuid:skill_id>/",
        views.skill_leaderboard,
    ),
    path(
        "leaderboard/role/<uuid:role_id>/",
        views.role_leaderboard,
    ),
    path(
        "leaderboard/group/",
        views.org_leaderboard_by_group,
        name="org-leaderboard-by-group",
    ),
]
