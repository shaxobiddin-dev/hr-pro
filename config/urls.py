"""
HR-Pro URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('accounts/', include('allauth.urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # API v1
    path('api/v1/', include('apps.core.api.urls')),

    # Web UI
    path('', include('apps.core.urls')),

    # HR Module
    path('employees/', include('apps.employees.urls')),
    path('departments/', include('apps.departments.urls')),

    # Payroll Module
    path('payroll/', include('apps.payroll.urls')),

    # Leave Module
    path('leave/', include('apps.leave.urls')),

    # Attendance Module
    path('attendance/', include('apps.attendance.urls')),

    # Orders Module
    path('orders/', include('apps.orders.urls')),
]

# Debug toolbar (development only)
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
