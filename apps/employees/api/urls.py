"""
Employee API URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    EmployeeViewSet,
    PositionViewSet,
    LevelViewSet,
    TenureBracketViewSet,
    MHTMHistoryViewSet,
)

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'positions', PositionViewSet, basename='position')
router.register(r'levels', LevelViewSet, basename='level')
router.register(r'tenure-brackets', TenureBracketViewSet, basename='tenure-bracket')
router.register(r'mhtm', MHTMHistoryViewSet, basename='mhtm')

urlpatterns = [
    path('', include(router.urls)),
]
