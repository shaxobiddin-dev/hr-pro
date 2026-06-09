"""
API v1 URL patterns.
"""

from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

app_name = 'api'

urlpatterns = [
    # JWT Authentication
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # HR API
    path('hr/', include('apps.employees.api.urls')),

    # Departments API
    path('org/', include('apps.departments.api.urls')),

    # Payroll API
    path('payroll/', include('apps.payroll.api.urls')),
]
