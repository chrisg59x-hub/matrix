# backend/api/tests.py

from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Org, User
from learning.models import Skill, RecertRequirement


class OverdueSopsAPITests(APITestCase):
    def setUp(self):
        # minimal Org – only has "name" in your current model
        self.org = Org.objects.create(name="Test Org")

        # user attached to org
        self.user = User.objects.create_user(
            username="alice",
            password="password123",
            org=self.org,
        )

        # minimal Skill – your Skill model is (org, name, risk_level, valid_for_days)
        self.skill = Skill.objects.create(
            org=self.org,
            name="Test Skill",
        )

        self.url = "/api/me/overdue-sops/"

    def test_requires_auth(self):
        # Unauthenticated client should get 401
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_only_overdue_for_current_user(self):
        self.client.force_authenticate(self.user)

        today = date.today()

        # Overdue requirement for this user (yesterday)
        overdue = RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_date=today - timedelta(days=1),
            # due_at is optional; keep it simple
            reason="expiry",
        )

        # Future requirement for this user (should NOT be returned)
        RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_date=today + timedelta(days=5),
            reason="expiry",
        )

        # Overdue for a different user (should NOT be returned)
        other_user = User.objects.create_user(
            username="bob",
            password="password123",
            org=self.org,
        )
        RecertRequirement.objects.create(
            org=self.org,
            user=other_user,
            skill=self.skill,
            due_date=today - timedelta(days=3),
            reason="expiry",
        )

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        # accept either plain list or paginated {results: [...]}
        items = data if isinstance(data, list) else data.get("results", [])

        self.assertEqual(len(items), 1)
        self.assertEqual(str(items[0]["id"]), str(overdue.id))

    def test_ignores_resolved_requirements(self):
        self.client.force_authenticate(self.user)

        today = date.today()

        # Overdue but resolved -> should NOT appear
        RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_date=today - timedelta(days=2),
            reason="expiry",
            resolved=True,
        )

        # Overdue and unresolved -> should appear
        overdue2 = RecertRequirement.objects.create(
            org=self.org,
            user=self.user,
            skill=self.skill,
            due_date=today - timedelta(days=5),
            reason="expiry",
            resolved=False,
        )

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        items = data if isinstance(data, list) else data.get("results", [])

        self.assertEqual(len(items), 1)
        self.assertEqual(str(items[0]["id"]), str(overdue2.id))
