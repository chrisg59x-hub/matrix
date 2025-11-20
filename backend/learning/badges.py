# learning/badges.py
import logging
from typing import Optional, Dict, Set

from django.db.models import Sum, Count, Q

from .models import (
    Badge,
    UserBadge,
    XPEvent,
    SupervisorSignoff,
    TeamMember,
    Team,
    Department,
)

log = logging.getLogger(__name__)


def auto_award_badges_for_user(user, org=None):
    """
    Evaluate all badge rules for a single user and award any
    badges they qualify for (that they don't already hold).

    Supported rule_types:

      - overall_xp_at_least
      - skill_xp_at_least
      - signoffs_at_least
      - team_total_xp_at_least
      - department_total_xp_at_least

    Unknown rule_types are ignored (logged at debug).
    """
    if org is None:
        org = getattr(user, "org", None)

    # ----------------------------------------------------------------------------
    # 1) Precompute per-user aggregates
    # ----------------------------------------------------------------------------
    xp_qs = XPEvent.objects.filter(user=user)
    if org is not None:
        xp_qs = xp_qs.filter(org=org)

    # Overall XP for this user
    overall_xp = xp_qs.aggregate(total=Sum("amount"))["total"] or 0

    # XP per skill
    skill_rows = (
        xp_qs.values("skill_id")
        .annotate(total=Sum("amount"))
    )
    skill_xp: Dict[Optional[str], int] = {
        row["skill_id"]: row["total"] or 0
        for row in skill_rows
        if row["skill_id"] is not None
    }

    # Count of supervisor signoffs for this user
    signoff_qs = SupervisorSignoff.objects.filter(user=user)
    if org is not None:
        # if skills are per-org, this keeps it scoped
        signoff_qs = signoff_qs.filter(skill__org=org)
    signoff_count = signoff_qs.count()

    # ----------------------------------------------------------------------------
    # 2) Precompute team / department aggregates for this user
    # ----------------------------------------------------------------------------
    # Teams this user belongs to
    memberships = TeamMember.objects.filter(user=user, active=True).select_related(
        "team", "team__department"
    )

    team_ids: Set[str] = set()
    dept_ids: Set[str] = set()

    for tm in memberships:
        if tm.team_id:
            team_ids.add(str(tm.team_id))
        if tm.team and tm.team.department_id:
            dept_ids.add(str(tm.team.department_id))

    team_xp: Dict[str, int] = {}
    dept_xp: Dict[str, int] = {}

    if team_ids:
        # All active members of teams this user is in
        team_member_rows = TeamMember.objects.filter(
            team_id__in=team_ids,
            active=True,
        ).values("team_id", "user_id")

        team_to_users: Dict[str, Set[str]] = {}
        user_ids_for_teams: Set[str] = set()

        for row in team_member_rows:
            tid = str(row["team_id"])
            uid = str(row["user_id"])
            team_to_users.setdefault(tid, set()).add(uid)
            user_ids_for_teams.add(uid)

        # XP for all those users in this org
        team_xp_rows = XPEvent.objects.filter(
            user_id__in=user_ids_for_teams,
        )
        if org is not None:
            team_xp_rows = team_xp_rows.filter(org=org)

        team_xp_rows = (
            team_xp_rows.values("user_id")
            .annotate(total=Sum("amount"))
        )
        xp_by_user: Dict[str, int] = {
            str(r["user_id"]): r["total"] or 0 for r in team_xp_rows
        }

        # Sum per team
        for tid, uids in team_to_users.items():
            team_xp[tid] = sum(xp_by_user.get(uid, 0) for uid in uids)

        # From team_xp, roll up to departments
        # First, get mapping team_id -> department_id
        team_objs = Team.objects.filter(id__in=team_ids).select_related("department")
        team_to_dept: Dict[str, Optional[str]] = {}
        for t in team_objs:
            team_to_dept[str(t.id)] = str(t.department_id) if t.department_id else None

        for tid, total in team_xp.items():
            dept_id = team_to_dept.get(tid)
            if not dept_id:
                continue
            dept_xp.setdefault(dept_id, 0)
            dept_xp[dept_id] += total

    # ----------------------------------------------------------------------------
    # 3) Evaluate badge rules
    # ----------------------------------------------------------------------------
    badge_qs = Badge.objects.all()
    if org is not None:
        badge_qs = badge_qs.filter(org=org)

    # Avoid re-awarding badges
    already = set(
        UserBadge.objects.filter(user=user).values_list("badge_id", flat=True)
    )

    to_award = []

    for badge in badge_qs:
        if badge.id in already:
            continue

        rt = badge.rule_type
        value = badge.value or 0

        if rt == "overall_xp_at_least":
            if overall_xp >= value:
                to_award.append(badge)
                continue

        elif rt == "skill_xp_at_least":
            if not badge.skill_id:
                # Misconfigured – needs a skill
                log.debug("Badge %s has rule_type=skill_xp_at_least but no skill.", badge.id)
                continue
            user_skill_xp = skill_xp.get(str(badge.skill_id), 0)
            if user_skill_xp >= value:
                to_award.append(badge)
                continue

        elif rt == "signoffs_at_least":
            if signoff_count >= value:
                to_award.append(badge)
                continue

        elif rt == "team_total_xp_at_least":
            if not badge.team_id:
                log.debug("Badge %s has rule_type=team_total_xp_at_least but no team.", badge.id)
                continue
            tid = str(badge.team_id)
            # Only if user is actually in this team
            if tid in team_ids and team_xp.get(tid, 0) >= value:
                to_award.append(badge)
                continue

        elif rt == "department_total_xp_at_least":
            if not badge.department_id:
                log.debug("Badge %s has rule_type=department_total_xp_at_least but no department.", badge.id)
                continue
            did = str(badge.department_id)
            # Only if user is in this department (via any team)
            if did in dept_ids and dept_xp.get(did, 0) >= value:
                to_award.append(badge)
                continue

        else:
            # Other rule types (e.g. team_member_count_with_xp_at_least) are not yet implemented
            log.debug("Ignoring unsupported badge rule_type=%s for badge=%s", rt, badge.id)

    # ----------------------------------------------------------------------------
    # 4) Create UserBadge rows
    # ----------------------------------------------------------------------------
    for badge in to_award:
        ub, created = UserBadge.objects.get_or_create(
            user=user,
            badge=badge,
            defaults={"meta": {"auto_awarded": True}},
        )
        if created:
            log.info(
                "Auto-awarded badge %s (%s) to user %s",
                badge.code or badge.id,
                badge.name,
                user,
            )
