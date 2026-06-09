"""
Department API serializers.
"""

from rest_framework import serializers
from apps.departments.models import Department


class DepartmentListSerializer(serializers.ModelSerializer):
    """Bo'limlar ro'yxati uchun serializer."""

    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    employee_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'parent', 'parent_name',
            'employee_count', 'is_active'
        ]


class DepartmentDetailSerializer(serializers.ModelSerializer):
    """Bo'lim tafsiloti uchun serializer."""

    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    children = serializers.SerializerMethodField()
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'parent', 'parent_name',
            'description', 'children', 'employee_count',
            'is_active', 'created_at', 'updated_at'
        ]

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return DepartmentListSerializer(children, many=True).data

    def get_employee_count(self, obj):
        return obj.employees.filter(is_active=True).count()


class DepartmentCreateUpdateSerializer(serializers.ModelSerializer):
    """Bo'lim yaratish/yangilash uchun serializer."""

    class Meta:
        model = Department
        fields = ['name', 'code', 'parent', 'description']

    def validate_parent(self, value):
        """O'zini o'ziga parent qilib belgilashni oldini olish."""
        if self.instance and value and self.instance.pk == value.pk:
            raise serializers.ValidationError("Bo'lim o'zini o'ziga parent qilib belgilay olmaydi.")
        return value


class DepartmentTreeSerializer(serializers.ModelSerializer):
    """Bo'limlar daraxti uchun rekursiv serializer."""

    children = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'children']

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return DepartmentTreeSerializer(children, many=True).data
