# backend/learning/views.py
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet
from .models import Module
from .serializers import ModuleSerializer

class ModuleViewSet(ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        params = self.request.query_params

        skill = params.get("skill")
        only_overdue = params.get("onlyOverdue")

        if skill:
            # adapt this to however you link modules to skills
            qs = qs.filter(skills__id=skill).distinct()

        if only_overdue == "1":
            # EXAMPLE logic – tweak to your actual schema
            # e.g. modules that have a “next_due_at” for this user in the past
            now = timezone.now()
            qs = qs.filter(
                assignments__user=user,
                assignments__next_due_at__lte=now,
            ).distinct()

        return qs
# Create your views here.
