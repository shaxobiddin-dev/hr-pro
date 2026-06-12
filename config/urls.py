"""
HR-Pro URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.contrib.sitemaps.views import sitemap
from django.contrib.sitemaps import Sitemap
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


@require_GET
def robots_txt(request):
    """robots.txt - qidiruv robotlari uchun."""
    lines = [
        "User-Agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /api/",
        "",
        f"Sitemap: https://hrmpro.uz/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


class StaticViewSitemap(Sitemap):
    """Asosiy sahifalar uchun sitemap."""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        # Faqat ommaviy sahifalar (login talab qilmaydigan)
        return ['core:home', 'core:about']

    def location(self, item):
        from django.urls import reverse
        return reverse(item)


sitemaps = {
    'static': StaticViewSitemap,
}

# Tilga bog'liq bo'lmagan URL'lar
urlpatterns = [
    # SEO
    path('robots.txt', robots_txt, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),

    # API - tilga bog'liq emas
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/', include('apps.core.api.urls')),

    # Til almashtirish
    path('i18n/', include('django.conf.urls.i18n')),
]

# Tilga bog'liq URL'lar (i18n_patterns)
urlpatterns += i18n_patterns(
    # Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('accounts/', include('allauth.urls')),

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

    prefix_default_language=False,  # Default til uchun prefix qo'shmaslik (uz/ emas, / bo'ladi)
)

# Debug toolbar (development only)
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
