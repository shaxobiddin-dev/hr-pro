"""
Payroll API URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TaxRateViewSet,
    SalaryComponentViewSet,
    PayrollPeriodViewSet,
    PayrollViewSet,
)

router = DefaultRouter()
router.register(r'tax-rates', TaxRateViewSet, basename='tax-rate')
router.register(r'components', SalaryComponentViewSet, basename='component')
router.register(r'periods', PayrollPeriodViewSet, basename='period')
router.register(r'payrolls', PayrollViewSet, basename='payroll')

urlpatterns = [
    path('', include(router.urls)),
]
