"""
Employee API serializers.
"""

from rest_framework import serializers
from apps.accounts.models import User
from apps.employees.models import Employee, Position, Level, TenureBracket, MHTMHistory
from apps.departments.models import Department


class UserSerializer(serializers.ModelSerializer):
    """Foydalanuvchi serializeri."""

    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'phone']
        read_only_fields = ['id', 'email']


class LevelSerializer(serializers.ModelSerializer):
    """Daraja serializeri."""

    class Meta:
        model = Level
        fields = ['id', 'name', 'level', 'coefficient', 'description']


class TenureBracketSerializer(serializers.ModelSerializer):
    """Staj oralig'i serializeri."""

    class Meta:
        model = TenureBracket
        fields = ['id', 'name', 'min_months', 'max_months', 'coefficient']


class PositionSerializer(serializers.ModelSerializer):
    """Lavozim serializeri."""

    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Position
        fields = [
            'id', 'name', 'code', 'department', 'department_name',
            'base_coefficient', 'description', 'is_active'
        ]


class PositionListSerializer(serializers.ModelSerializer):
    """Lavozim ro'yxati uchun qisqa serializer."""

    class Meta:
        model = Position
        fields = ['id', 'name', 'code', 'base_coefficient']


class DepartmentMinimalSerializer(serializers.ModelSerializer):
    """Bo'lim minimal serializeri."""

    class Meta:
        model = Department
        fields = ['id', 'name', 'code']


class EmployeeListSerializer(serializers.ModelSerializer):
    """Xodimlar ro'yxati uchun serializer."""

    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    position_name = serializers.CharField(source='position.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    level_name = serializers.CharField(source='level.name', read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_code', 'full_name', 'email',
            'position_name', 'department_name', 'level_name',
            'status', 'hire_date', 'is_active'
        ]


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Xodim tafsiloti uchun serializer."""

    user = UserSerializer(read_only=True)
    position = PositionListSerializer(read_only=True)
    department = DepartmentMinimalSerializer(read_only=True)
    level = LevelSerializer(read_only=True)
    tenure_bracket = TenureBracketSerializer(read_only=True)
    base_salary = serializers.SerializerMethodField()
    tenure_months = serializers.IntegerField(read_only=True)
    tenure_display = serializers.CharField(read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_code', 'user', 'position', 'department',
            'level', 'tenure_bracket', 'hire_date', 'birth_date',
            'gender', 'status', 'contract_type', 'contract_end_date',
            'address', 'emergency_contact', 'notes',
            'base_salary', 'tenure_months', 'tenure_display',
            'is_active', 'created_at', 'updated_at'
        ]

    def get_base_salary(self, obj):
        """Asosiy ish haqini hisoblash."""
        mhtm = MHTMHistory.get_current()
        if mhtm:
            return str(obj.calculate_base_salary(mhtm))
        return "0"


class EmployeeCreateUpdateSerializer(serializers.ModelSerializer):
    """Xodim yaratish/yangilash uchun serializer."""

    email = serializers.EmailField(write_only=True, required=False)
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Employee
        fields = [
            'employee_code', 'email', 'first_name', 'last_name', 'phone',
            'position', 'department', 'level',
            'hire_date', 'birth_date', 'gender',
            'status', 'contract_type', 'contract_end_date',
            'address', 'emergency_contact', 'notes'
        ]

    def create(self, validated_data):
        # User ma'lumotlarini ajratish
        email = validated_data.pop('email', None)
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        phone = validated_data.pop('phone', '')

        if not email:
            raise serializers.ValidationError({'email': 'Email majburiy.'})

        # User yaratish
        user = User.objects.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            password=User.objects.make_random_password()
        )

        # Employee yaratish
        employee = Employee.objects.create(user=user, **validated_data)
        return employee

    def update(self, instance, validated_data):
        # User ma'lumotlarini yangilash
        user = instance.user
        if 'first_name' in validated_data:
            user.first_name = validated_data.pop('first_name')
        if 'last_name' in validated_data:
            user.last_name = validated_data.pop('last_name')
        if 'phone' in validated_data:
            user.phone = validated_data.pop('phone')
        user.save()

        # Email o'zgartirilmaydi
        validated_data.pop('email', None)

        # Employee yangilash
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class MHTMHistorySerializer(serializers.ModelSerializer):
    """MHTM tarixi serializeri."""

    class Meta:
        model = MHTMHistory
        fields = ['id', 'amount', 'effective_date', 'description', 'created_at']
