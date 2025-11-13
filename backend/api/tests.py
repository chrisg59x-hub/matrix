from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import Org, User
from learning.models import Skill, RecertRequirement

User = get_user_model()


class OverdueSopsAPITests(TestCase):
    """
    Tests for /api/me/overdue-sops/ endpoint.
    """

    def setUp(self):
        self.client = APIClient()

        # Org + users
        self.org = Org.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password123",
            org=self.org,
        )
        self.other_user = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="password123",
            org=self.org,
        )

        # Simple skill
        self.skill = Skill.objects.create(org=self.org, name="Test Skill")

    def test_requires_auth(self):
        """Endpoint requires authentication."""
        resp = self.client.get("/api/me/overdue-sops/")
        self.assertEqual(resp.status_code, 401)

    def test_returns_only_overdue_for_current_user(self):
        """
        Only past-due, unresolved requirements for the logged-in user are returned.
        """
        today = timezone.now().date()
        past_date = today - timezone.timedelta(days=7)
        future_date = today + timezone.timedelta(days=7)

        # 1) overdue for current user -> SHOULD appear
        RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_date=past_date,
            reason="Past due",
        )

        # 2) future due for current user -> should NOT appear
        RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_date=future_date,
            reason="Not yet due",
        )

        # 3) overdue for different user -> should NOT appear
        RecertRequirement.objects.create(
            org=self.org,
            user=self.other_user,
            skill=self.skill,
            due_date=past_date,
            reason="Other user",
        )

        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/me/overdue-sops/")
        self.assertEqual(resp.status_code, 200)

        items = list(resp.data)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["reason"], "Past due")

    def test_ignores_resolved_requirements(self):
        """
        Overdue requirements that are already resolved must not be included.
        """
        today = timezone.now().date()
        past_date = today - timezone.timedelta(days=3)

        # 1) overdue but resolved -> SHOULD be ignored
        RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_date=past_date,
            reason="Already resolved",
            resolved_at=timezone.now(),
        )

        # 2) overdue and unresolved -> SHOULD be returned
        RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_date=past_date,
            reason="Still overdue",
        )

        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/me/overdue-sops/")
        self.assertEqual(resp.status_code, 200)

        items = list(resp.data)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["reason"], "Still overdue")