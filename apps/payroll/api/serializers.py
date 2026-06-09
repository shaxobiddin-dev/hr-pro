"""
Payroll API serializers.
"""

from rest_framework import serializers
from apps.payroll.models import (
    TaxRate, SalaryComponent, PayrollPeriod, Payroll, PayrollItem
)


class TaxRateSerializer(serializers.ModelSerializer):
    """Soliq stavkasi serializeri."""

    tax_type_display = serializers.CharField(source='get_tax_type_display', read_only=True)

    class Meta:
        model = TaxRate
        fields = [
            'id', 'tax_type', 'tax_type_display', 'rate',
            'effective_date', 'description', 'is_active'
        ]


class SalaryComponentSerializer(serializers.ModelSerializer):
    """Ish haqi komponenti serializeri."""

    component_type_display = serializers.CharField(source='get_component_type_display', read_only=True)
    calculation_type_display = serializers.CharField(source='get_calculation_type_display', read_only=True)

    class Meta:
        model = SalaryComponent
        fields = [
            'id', 'name', 'code', 'component_type', 'component_type_display',
            'calculation_type', 'calculation_type_display', 'default_value',
            'is_taxable', 'is_statutory', 'description'
        ]


class PayrollItemSerializer(serializers.ModelSerializer):
    """Ish haqi elementi serializeri."""

    component_name = serializers.CharField(source='component.name', read_only=True)
    component_code = serializers.CharField(source='component.code', read_only=True)
    component_type = serializers.CharField(source='component.component_type', read_only=True)

    class Meta:
        model = PayrollItem
        fields = [
            'id', 'component', 'component_name', 'component_code',
            'component_type', 'amount', 'notes'
        ]


class PayrollListSerializer(serializers.ModelSerializer):
    """Ish haqi ro'yxati uchun serializer."""

    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    position_name = serializers.CharField(source='employee.position.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payroll
        fields = [
            'id', 'employee_code', 'employee_name', 'position_name',
            'work_days', 'gross_salary', 'total_deductions', 'net_salary',
            'status', 'status_display'
        ]


class PayrollDetailSerializer(serializers.ModelSerializer):
    """Ish haqi tafsiloti uchun serializer."""

    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    position_name = serializers.CharField(source='employee.position.name', read_only=True)
    department_name = serializers.CharField(source='employee.department.name', read_only=True)
    period_name = serializers.CharField(source='period.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = PayrollItemSerializer(many=True, read_only=True)

    class Meta:
        model = Payroll
        fields = [
            'id', 'period', 'period_name', 'employee', 'employee_code',
            'employee_name', 'position_name', 'department_name',
            'status', 'status_display',
            'work_days', 'absent_days', 'leave_days', 'sick_days',
            'base_salary', 'gross_salary', 'total_earnings', 'total_deductions',
            'jshdt_amount', 'inps_amount', 'net_salary',
            'items', 'notes', 'created_at', 'updated_at'
        ]


class PayrollUpdateSerializer(serializers.ModelSerializer):
    """Ish haqi yangilash uchun serializer."""

    class Meta:
        model = Payroll
        fields = ['work_days', 'absent_days', 'leave_days', 'sick_days', 'notes']


class PayrollPeriodListSerializer(serializers.ModelSerializer):
    """Ish haqi davrlari ro'yxati uchun serializer."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    employee_count = serializers.SerializerMethodField()
    total_gross = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_net = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = PayrollPeriod
        fields = [
            'id', 'name', 'start_date', 'end_date', 'payment_date',
            'work_days', 'status', 'status_display',
            'employee_count', 'total_gross', 'total_net'
        ]

    def get_employee_count(self, obj):
        return obj.payrolls.count()


class PayrollPeriodDetailSerializer(serializers.ModelSerializer):
    """Ish haqi davri tafsiloti uchun serializer."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payrolls = PayrollListSerializer(many=True, read_only=True)
    statistics = serializers.SerializerMethodField()

    class Meta:
        model = PayrollPeriod
        fields = [
            'id', 'name', 'start_date', 'end_date', 'payment_date',
            'work_days', 'status', 'status_display', 'notes',
            'payrolls', 'statistics', 'created_at', 'updated_at'
        ]

    def get_statistics(self, obj):
        payrolls = obj.payrolls.all()
        return {
            'employee_count': payrolls.count(),
            'total_gross': str(obj.total_gross),
            'total_net': str(obj.total_net),
            'total_deductions': str(obj.total_deductions),
        }


class PayrollPeriodCreateUpdateSerializer(serializers.ModelSerializer):
    """Ish haqi davri yaratish/yangilash uchun serializer."""

    class Meta:
        model = PayrollPeriod
        fields = ['name', 'start_date', 'end_date', 'work_days', 'payment_date', 'notes']

    def validate(self, data):
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError({
                    'end_date': "Tugash sanasi boshlanish sanasidan keyin bo'lishi kerak."
                })
        return data
