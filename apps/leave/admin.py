"""
Leave admin configuration.
"""

from django.contrib import admin
from .models import LeaveType, LeaveBalance, LeaveRequest


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'default_days', 'is_paid', 'requires_document', 'is_active']
    list_filter = ['category', 'is_paid', 'requires_document', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'year', 'entitled_days', 'carried_forward', 'used_days', 'remaining_days']
    list_filter = ['year', 'leave_type']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'employee__employee_code']
    ordering = ['-year', 'employee']
    raw_id_fields = ['employee']

    def remaining_days(self, obj):
        return obj.remaining_days
    remaining_days.short_description = "Qolgan kunlar"


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'requested_days', 'status', 'approved_by', 'created_at']
    list_filter = ['status', 'leave_type', 'start_date']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'employee__employee_code']
    ordering = ['-created_at']
    raw_id_fields = ['employee', 'approved_by']
    readonly_fields = ['requested_days', 'approved_at']
    date_hierarchy = 'start_date'

    fieldsets = (
        ("Asosiy ma'lumotlar", {
            'fields': ('employee', 'leave_type', 'start_date', 'end_date', 'requested_days', 'reason')
        }),
        ("Holat", {
            'fields': ('status', 'approved_by', 'approved_at', 'rejection_reason')
        }),
        ("Hujjat", {
            'fields': ('document',),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        count = 0
        for leave_request in queryset.filter(status='pending'):
            leave_request.status = 'approved'
            leave_request.save()
            count += 1
        self.message_user(request, f"{count} ta so'rov tasdiqlandi.")
    approve_requests.short_description = "Tanlangan so'rovlarni tasdiqlash"

    def reject_requests(self, request, queryset):
        count = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f"{count} ta so'rov rad etildi.")
    reject_requests.short_description = "Tanlangan so'rovlarni rad etish"
