from rest_framework.viewsets import ModelViewSet
from .models import XPEvent
from .serializers import XPEventSerializer
class XPEventViewSet(ModelViewSet): queryset=XPEvent.objects.all(); serializer_class=XPEventSerializer
