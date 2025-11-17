from rest_framework.routers import DefaultRouter
from .views import XPEventViewSet
router=DefaultRouter()
router.register('xp-events', XPEventViewSet)
urlpatterns=router.urls
