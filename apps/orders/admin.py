"""
Buyruqlar admin.
"""

from django.contrib import admin
from .models import Order, HiringOrderItem


class HiringOrderItemInline(admin.TabularInline):
    model = HiringOrderItem
    extra = 0
    autocomplete_fields = ['employee', 'department', 'position', 'probation_department', 'probation_position']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'order_type', 'order_date', 'status', 'approved_by', 'created_by']
    list_filter = ['order_type', 'status', 'order_date']
    search_fields = ['order_number']
    date_hierarchy = 'order_date'
    ordering = ['-order_date']
    autocomplete_fields = ['approved_by']

    fieldsets = (
        (None, {
            'fields': ('order_number', 'order_type', 'order_date', 'status')
        }),
        ('Tasdiqlash', {
            'fields': ('approved_by', 'approved_at')
        }),
        ('Asos va izohlar', {
            'fields': ('legal_basis', 'notes')
        }),
    )

    readonly_fields = ['approved_at']

    def get_inlines(self, request, obj=None):
        if obj and obj.order_type == Order.OrderType.HIRING:
            return [HiringOrderItemInline]
        return []


@admin.register(HiringOrderItem)
class HiringOrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'employee', 'department', 'position', 'start_date', 'salary', 'has_probation']
    list_filter = ['has_probation', 'work_schedule', 'contract_type']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']
    autocomplete_fields = ['order', 'employee', 'department', 'position']
