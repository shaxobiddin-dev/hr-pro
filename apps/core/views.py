"""
Core views.
"""

from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection


class HealthCheckView(View):
    """Health check endpoint for load balancers and monitoring."""

    def get(self, request):
        health_status = {
            'status': 'healthy',
            'database': 'ok',
            'cache': 'ok',
        }

        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['database'] = str(e)

        # Cache check
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') != 'ok':
                raise Exception('Cache read/write failed')
        except Exception as e:
            health_status['cache'] = str(e)
            # Cache failure is not critical
            if health_status['status'] == 'healthy':
                health_status['status'] = 'degraded'

        status_code = 200 if health_status['status'] == 'healthy' else 503
        return JsonResponse(health_status, status=status_code)


class HomeView(TemplateView):
    """Home page view."""
    template_name = 'home.html'

    def dispatch(self, request, *args, **kwargs):
        # Login qilgan foydalanuvchi → Dashboard'ga redirect
        if request.user.is_authenticated:
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard view (requires login)."""
    template_name = 'dashboard.html'
    login_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from apps.employees.models import Employee, Position, Level
        from apps.departments.models import Department

        # Statistika
        context['total_employees'] = Employee.objects.filter(is_active=True).count()
        context['total_departments'] = Department.objects.filter(is_active=True).count()
        context['on_leave_count'] = Employee.objects.filter(
            is_active=True, status=Employee.Status.ON_LEAVE
        ).count()
        context['total_positions'] = Position.objects.filter(is_active=True).count()

        # So'nggi xodimlar
        context['recent_employees'] = Employee.objects.filter(
            is_active=True
        ).select_related('user', 'department', 'position').order_by('-created_at')[:5]

        return context


class AboutView(TemplateView):
    """About page view."""
    template_name = 'about.html'
