"""
Attendance admin.
"""

from django.contrib import admin
from .models import Attendance, MonthlyTimesheet


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'check_in', 'check_out', 'status', 'work_hours', 'late_minutes']
    list_filter = ['status', 'date', 'employee__department']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'employee__employee_code']
    date_hierarchy = 'date'
    ordering = ['-date', 'employee']

    fieldsets = (
        (None, {
            'fields': ('employee', 'date', 'status')
        }),
        ('Vaqtlar', {
            'fields': ('check_in', 'check_out', 'work_hours')
        }),
        ("Qo'shimcha", {
            'fields': ('late_minutes', 'early_leave_minutes', 'notes', 'recorded_by')
        }),
    )

    readonly_fields = ['work_hours', 'late_minutes', 'early_leave_minutes']


@admin.register(MonthlyTimesheet)
class MonthlyTimesheetAdmin(admin.ModelAdmin):
    list_display = ['employee', 'year', 'month', 'work_days', 'present_days', 'absent_days', 'status']
    list_filter = ['status', 'year', 'month', 'employee__department']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']
    ordering = ['-year', '-month', 'employee']

    fieldsets = (
        (None, {
            'fields': ('employee', 'year', 'month', 'status')
        }),
        ('Kunlar', {
            'fields': ('work_days', 'present_days', 'absent_days', 'late_days', 'leave_days', 'sick_days')
        }),
        ('Soatlar', {
            'fields': ('total_work_hours', 'total_late_minutes')
        }),
        ('Tasdiqlash', {
            'fields': ('confirmed_by', 'confirmed_at')
        }),
    )
