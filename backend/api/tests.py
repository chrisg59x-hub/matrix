# backend/api/tests.py
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Org, User
from learning.models import Skill, RecertRequirement


class SmokeTests(TestCase):
    """Existing minimal sanity tests – keep these if you already had them."""

    def test_true_is_true(self):
        self.assertTrue(True)


class OverdueSopsAPITests(TestCase):
    """
    Tests for /api/me/overdue-sops/ endpoint.

    It should:
      - require authentication
      - return only overdue, unresolved requirements for the logged-in user
      - ignore requirements for other users
      - ignore requirements that are resolved
    """

    def setUp(self):
        self.client = APIClient()

        # Org & user
        self.org = Org.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            username="alice",
            password="password123",
            org=self.org,
        )

        # Skill
        self.skill = Skill.objects.create(
            org=self.org,
            name="Test Skill",
        )

    def _url(self):
        return reverse("api:me-overdue-sops")  # make sure your urlpattern has this name

    def test_requires_auth(self):
        """Unauthenticated requests should be rejected."""
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 401)

    def test_returns_only_overdue_for_current_user(self):
        """
        Only past-due, unresolved requirements for the logged-in user are returned.
        """
        now = timezone.now()

        # Overdue requirement for our user (due_at < now)
        overdue = RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_at=now - timedelta(days=2),
            reason="Past due",
            resolved=False,
        )

        # Future requirement (not overdue)
        RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_at=now + timedelta(days=2),
            reason="In future",
            resolved=False,
        )

        # Overdue but for another user -> must be ignored
        other_user = User.objects.create_user(
            username="bob",
            password="password123",
            org=self.org,
        )
        RecertRequirement.objects.create(
            org=self.org,
            user=other_user,
            skill=self.skill,
            due_at=now - timedelta(days=3),
            reason="Other user overdue",
            resolved=False,
        )

        self.client.force_authenticate(self.user)
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200)

        items = list(resp.data if isinstance(resp.data, list) else resp.data.get("results", []))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], overdue.id)

    def test_ignores_resolved_requirements(self):
        """
        Overdue requirements that are already resolved must not be included.
        """
        now = timezone.now()

        # Overdue & unresolved -> should be returned
        overdue_unresolved = RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_at=now - timedelta(days=5),
            reason="Overdue unresolved",
            resolved=False,
        )

        # Overdue but resolved -> must be ignored
        RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_at=now - timedelta(days=10),
            reason="Overdue but resolved",
            resolved=True,
        )

        self.client.force_authenticate(self.user)
        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200)

        items = list(resp.data if isinstance(resp.data, list) else resp.data.get("results", []))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], overdue_unresolved.id)
