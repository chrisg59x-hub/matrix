from rest_framework.test import APIClient
from django.urls import reverse
from accounts.models import Org, User
from learning.models import Skill, XPEvent

def _auth_client(role="admin"):
    c = APIClient()
    org, _ = Org.objects.get_or_create(name="Demo Org")
    u, _ = User.objects.get_or_create(username=f"{role}1", defaults={"biz_role": role, "org": org, "email": f"{role}1@x.x"})
    u.set_password("pass1234"); u.save()
    c.force_authenticate(user=u)
    return c, org, u

def test_org_leaderboard_json(db):
    c, org, u = _auth_client()
    skill = Skill.objects.create(org=org, name="Safety")
    XPEvent.objects.create(org=org, user=u, skill=skill, amount=50, source="test")
    resp = c.get("/api/leaderboard/")
    assert resp.status_code == 200
    assert isinstance(resp.data, list)
    assert any(r["username"] == u.username for r in resp.data)

def test_leaderboard_csv(db):
    c, org, u = _auth_client()
    r = c.get("/api/leaderboard.csv")
    assert r.status_code == 200
    assert r["Content-Type"].startswith("text/csv")

def test_xp_export_csv_requires_manager(db):
    # non-manager
    c, _, _ = _auth_client(role="employee")
    r = c.get("/api/xp/export.csv")
    assert r.status_code in (401, 403)

    # manager
    c, org, u = _auth_client(role="manager")
    r = c.get("/api/xp/export.csv")
    assert r.status_code == 200
    assert r["Content-Type"].startswith("text/csv")
