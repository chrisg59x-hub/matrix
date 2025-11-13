from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import Org
from learning.models import Skill, RecertRequirement

User = get_user_model()


class OverdueSopsAPITests(TestCase):
    def setUp(self):
        self.org = Org.objects.create(name="Test Org")

        self.user = User.objects.create_user(
            username="alice",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            username="bob",
            password="password123",
        )

        # minimal skill with required org
        self.skill = Skill.objects.create(
            org=self.org,
            name="Test Skill",
        )

        self.client = APIClient()
        self.url = "/api/me/overdue-sops/"

    def test_requires_auth(self):
        resp = self.client.get(self.url)
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def _auth(self, user=None):
        if user is None:
            user = self.user
        self.client.force_authenticate(user=user)

    def test_returns_only_overdue_for_current_user(self):
        """Only past-due, unresolved requirements for the logged-in user are returned."""

        self._auth(self.user)
        today = timezone.now().date()

        # overdue requirement for current user
        overdue = RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_date=today - timedelta(days=2),
            reason="Past due",
        )

        # future requirement for current user (should NOT be returned)
        RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_date=today + timedelta(days=2),
            reason="Future requirement",
        )

        # overdue requirement for another user (should NOT be returned)
        RecertRequirement.objects.create(
            org=self.org,
            user=self.other_user,
            skill=self.skill,
            due_date=today - timedelta(days=5),
            reason="Other user's overdue",
        )

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        items = list(resp.data)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], str(overdue.id))

    def test_ignores_resolved_requirements(self):
        """Overdue requirements that are already resolved must not be included."""

        self._auth(self.user)
        today = timezone.now().date()

        # unresolved overdue requirement (should be returned)
        active = RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_date=today - timedelta(days=3),
            reason="Still overdue",
        )

        # same user, overdue but resolved (should NOT be returned)
        RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_date=today - timedelta(days=7),
            reason="Already resolved",
            resolved_at=timezone.now(),
        )

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        items = list(resp.data)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], str(active.id))
