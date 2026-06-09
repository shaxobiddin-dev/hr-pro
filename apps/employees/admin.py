"""
Employee admin configuration.
"""

from django.contrib import admin
from .models import Level, TenureBracket, Position, MHTMHistory, Employee


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ['level', 'name', 'coefficient', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['level']


@admin.register(TenureBracket)
class TenureBracketAdmin(admin.ModelAdmin):
    list_display = ['name', 'min_months', 'max_months', 'coefficient', 'is_active']
    list_filter = ['is_active']
    ordering = ['min_months']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'base_coefficient', 'is_active']
    list_filter = ['is_active', 'department']
    search_fields = ['name', 'code']
    autocomplete_fields = ['department', 'min_level', 'max_level']

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        return queryset, use_distinct


@admin.register(MHTMHistory)
class MHTMHistoryAdmin(admin.ModelAdmin):
    list_display = ['effective_date', 'amount', 'decree_number']
    ordering = ['-effective_date']
    date_hierarchy = 'effective_date'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'employee_code', 'full_name', 'department', 'position',
        'level', 'status', 'hire_date'
    ]
    list_filter = ['status', 'contract_type', 'department', 'level', 'is_active']
    search_fields = [
        'employee_code', 'user__first_name', 'user__last_name', 'user__email'
    ]
    raw_id_fields = ['user', 'manager']
    autocomplete_fields = ['department', 'position', 'level']
    date_hierarchy = 'hire_date'
    ordering = ['employee_code']

    fieldsets = (
        ("Asosiy ma'lumotlar", {
            'fields': ('user', 'employee_code')
        }),
        ("Tashkiliy ma'lumotlar", {
            'fields': ('department', 'position', 'level', 'manager')
        }),
        ("Mehnat shartnomasi", {
            'fields': (
                'contract_type', 'hire_date', 'contract_end_date',
                'probation_end_date', 'prior_experience_months'
            )
        }),
        ("Holat", {
            'fields': ('status', 'termination_date', 'termination_reason', 'is_active'),
            'classes': ('collapse',)
        }),
    )

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = "Ism"
