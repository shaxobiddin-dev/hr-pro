"""
Payroll admin konfiguratsiyasi.
"""

from decimal import Decimal
from django.contrib import admin
from django.utils.html import format_html

from .models import TaxRate, SalaryComponent, PayrollPeriod, Payroll, PayrollItem


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    """Soliq stavkalari admin."""

    list_display = ['tax_type', 'rate_display', 'effective_date', 'is_active']
    list_filter = ['tax_type', 'is_active', 'effective_date']
    search_fields = ['description']
    ordering = ['-effective_date', 'tax_type']
    date_hierarchy = 'effective_date'

    @admin.display(description="Stavka")
    def rate_display(self, obj):
        return f"{obj.rate}%"


@admin.register(SalaryComponent)
class SalaryComponentAdmin(admin.ModelAdmin):
    """Ish haqi komponentlari admin."""

    list_display = [
        'code', 'name', 'component_type', 'calculation_type',
        'default_value', 'is_taxable', 'is_statutory'
    ]
    list_filter = ['component_type', 'calculation_type', 'is_taxable', 'is_statutory']
    search_fields = ['name', 'code', 'description']
    ordering = ['component_type', 'name']

    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'description')
        }),
        ("Hisoblash", {
            'fields': ('component_type', 'calculation_type', 'default_value')
        }),
        ("Xususiyatlar", {
            'fields': ('is_taxable', 'is_statutory', 'is_active')
        }),
    )


class PayrollInline(admin.TabularInline):
    """Payroll inline for PayrollPeriod."""

    model = Payroll
    extra = 0
    readonly_fields = ['employee', 'gross_salary', 'total_deductions', 'net_salary', 'status']
    fields = ['employee', 'work_days', 'gross_salary', 'total_deductions', 'net_salary', 'status']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    """Ish haqi davri admin."""

    list_display = [
        'name', 'start_date', 'end_date', 'work_days',
        'status', 'employee_count', 'total_gross_display', 'total_net_display'
    ]
    list_filter = ['status', 'start_date']
    search_fields = ['name', 'notes']
    ordering = ['-start_date']
    date_hierarchy = 'start_date'
    inlines = [PayrollInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'status')
        }),
        ("Sanalar", {
            'fields': ('start_date', 'end_date', 'payment_date')
        }),
        ("Parametrlar", {
            'fields': ('work_days', 'notes')
        }),
    )

    @admin.display(description="Xodimlar")
    def employee_count(self, obj):
        return obj.payrolls.count()

    @admin.display(description="Jami yalpi")
    def total_gross_display(self, obj):
        total = obj.total_gross
        return f"{total:,.0f} so'm" if total else "-"

    @admin.display(description="Jami sof")
    def total_net_display(self, obj):
        total = obj.total_net
        return f"{total:,.0f} so'm" if total else "-"


class PayrollItemInline(admin.TabularInline):
    """PayrollItem inline."""

    model = PayrollItem
    extra = 1
    fields = ['component', 'amount', 'notes']
    raw_id_fields = ['component']


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    """Xodim ish haqi admin."""

    list_display = [
        'employee', 'period', 'work_days_display', 'gross_display',
        'deductions_display', 'net_display', 'status'
    ]
    list_filter = ['status', 'period', 'period__start_date']
    search_fields = ['employee__employee_code', 'employee__user__first_name', 'employee__user__last_name']
    ordering = ['-period__start_date', 'employee__employee_code']
    raw_id_fields = ['employee', 'period']
    inlines = [PayrollItemInline]

    fieldsets = (
        (None, {
            'fields': ('period', 'employee', 'status')
        }),
        ("Ish kunlari", {
            'fields': (('work_days', 'absent_days'), ('leave_days', 'sick_days'))
        }),
        ("Hisoblash", {
            'fields': ('base_salary', 'total_earnings', 'gross_salary'),
            'classes': ('collapse',)
        }),
        ("Soliqlar va ushlanmalar", {
            'fields': ('jshdt_amount', 'inps_amount', 'total_deductions'),
            'classes': ('collapse',)
        }),
        ("Natija", {
            'fields': ('net_salary', 'notes')
        }),
    )

    readonly_fields = [
        'base_salary', 'gross_salary', 'total_earnings',
        'total_deductions', 'net_salary', 'jshdt_amount', 'inps_amount'
    ]

    actions = ['calculate_payroll', 'confirm_payroll', 'mark_as_paid']

    @admin.display(description="Ish kunlari")
    def work_days_display(self, obj):
        return f"{obj.work_days}/{obj.period.work_days}"

    @admin.display(description="Yalpi")
    def gross_display(self, obj):
        return f"{obj.gross_salary:,.0f}"

    @admin.display(description="Ushlanmalar")
    def deductions_display(self, obj):
        return f"{obj.total_deductions:,.0f}"

    @admin.display(description="Sof")
    def net_display(self, obj):
        color = 'green' if obj.net_salary > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:,.0f}</span>',
            color, obj.net_salary
        )

    @admin.action(description="Tanlangan ish haqlarini hisoblash")
    def calculate_payroll(self, request, queryset):
        count = 0
        for payroll in queryset:
            payroll.calculate()
            count += 1
        self.message_user(request, f"{count} ta ish haqi hisoblandi.")

    @admin.action(description="Tanlangan ish haqlarini tasdiqlash")
    def confirm_payroll(self, request, queryset):
        count = queryset.filter(status='calculated').update(status='confirmed')
        self.message_user(request, f"{count} ta ish haqi tasdiqlandi.")

    @admin.action(description="To'langan deb belgilash")
    def mark_as_paid(self, request, queryset):
        count = queryset.filter(status='confirmed').update(status='paid')
        self.message_user(request, f"{count} ta ish haqi to'landi deb belgilandi.")


@admin.register(PayrollItem)
class PayrollItemAdmin(admin.ModelAdmin):
    """Ish haqi elementi admin."""

    list_display = ['payroll', 'component', 'amount', 'notes']
    list_filter = ['component__component_type', 'component']
    search_fields = ['payroll__employee__employee_code', 'component__name', 'notes']
    raw_id_fields = ['payroll', 'component']
    ordering = ['payroll', 'component__component_type', 'component__name']
