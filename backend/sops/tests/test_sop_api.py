#import io
from django.urls import reverse
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from accounts.models import Org
#from sops.models import SOP

User = get_user_model()

def auth_client(username="admin", role="admin"):
    c = APIClient()
    org, _ = Org.objects.get_or_create(name="Test Org")
    u, _ = User.objects.get_or_create(username=username, defaults={"biz_role": role, "org": org, "email": f"{username}@x.x"})
    u.set_password("pass1234")
    u.save()
    # If you’re using JWT, you can call token endpoint; else force_authenticate in DRF:
    c.force_authenticate(user=u)
    return c, org, u

def test_create_and_list_sop(db, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    client, org, _ = auth_client()

    # create upload
    content = b"%PDF-1.4 fake pdf"
    fileobj = SimpleUploadedFile("demo.pdf", content, content_type="application/pdf")

    url = reverse("sop-list")  # Depends on your router basename; adjust if needed
    resp = client.post(url, {
        "org": str(org.id),
        "title": "Safety Induction",
        "type": "pdf",              # adjust to your enum/choice
        "active": True,
        "media_file": fileobj,      # must match your model field name
    }, format="multipart")
    assert resp.status_code in (200, 201), resp.data

    # list
    resp = client.get(url)
    assert resp.status_code == 200
    assert any(x["title"] == "Safety Induction" for x in resp.data.get("results", resp.data))
