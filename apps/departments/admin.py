"""
Department admin configuration.
"""

from django.contrib import admin
from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'manager', 'employee_count', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'code', 'description']
    ordering = ['name']
    raw_id_fields = ['parent', 'manager']

    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'description')
        }),
        ("Ierarxiya", {
            'fields': ('parent', 'manager')
        }),
        ("Holat", {
            'fields': ('is_active',),
            'classes': ('collapse',)
        }),
    )

    def employee_count(self, obj):
        return obj.employee_count
    employee_count.short_description = "Xodimlar"
