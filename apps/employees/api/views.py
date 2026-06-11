"""
Employee API views.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.employees.models import Employee, Position, Level, TenureBracket, MHTMHistory
from .serializers import (
    EmployeeListSerializer,
    EmployeeDetailSerializer,
    EmployeeCreateUpdateSerializer,
    PositionSerializer,
    LevelSerializer,
    TenureBracketSerializer,
    MHTMHistorySerializer,
)


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    Xodimlar API.

    list: Barcha xodimlar ro'yxati
    retrieve: Xodim tafsiloti
    create: Yangi xodim yaratish
    update: Xodim ma'lumotlarini yangilash
    destroy: Xodimni o'chirish (soft delete)
    """

    queryset = Employee.objects.select_related(
        'user', 'position', 'department', 'level', 'tenure_bracket'
    ).filter(is_active=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'department', 'position', 'level', 'gender', 'contract_type']
    search_fields = ['employee_code', 'user__first_name', 'user__last_name', 'user__email']
    ordering_fields = ['employee_code', 'hire_date', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EmployeeCreateUpdateSerializer
        return EmployeeDetailSerializer

    def perform_destroy(self, instance):
        """Soft delete."""
        instance.soft_delete()

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """O'chirilgan xodimni tiklash."""
        employee = self.get_object()
        employee.restore()
        return Response({'status': 'restored'})

    @action(detail=True, methods=['get'])
    def salary(self, request, pk=None):
        """Xodim ish haqi ma'lumotlari."""
        employee = self.get_object()
        mhtm = MHTMHistory.get_current()

        data = {
            'employee_code': employee.employee_code,
            'full_name': employee.user.get_full_name(),
            'position': employee.position.name if employee.position else None,
            'level': employee.level.name if employee.level else None,
            'level_coefficient': str(employee.level.coefficient) if employee.level else '1.0',
            'position_coefficient': str(employee.position.base_coefficient) if employee.position else '1.0',
            'tenure_months': employee.tenure_months,
            'tenure_coefficient': str(employee.tenure_bracket.coefficient) if employee.tenure_bracket else '1.0',
            'mhtm': str(mhtm.amount) if mhtm else '0',
            'base_salary': str(employee.calculate_base_salary(mhtm)) if mhtm else '0',
        }
        return Response(data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Xodimlar statistikasi."""
        total = Employee.objects.filter(is_active=True).count()
        active = Employee.objects.filter(is_active=True, status='active').count()
        on_leave = Employee.objects.filter(is_active=True, status='on_leave').count()
        suspended = Employee.objects.filter(is_active=True, status='suspended').count()

        return Response({
            'total': total,
            'active': active,
            'on_leave': on_leave,
            'suspended': suspended,
        })


class PositionViewSet(viewsets.ModelViewSet):
    """
    Lavozimlar API.
    """

    queryset = Position.objects.select_related('department').filter(is_active=True)
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['department', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['name']

    def perform_destroy(self, instance):
        instance.soft_delete()


class LevelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Darajalar API (faqat o'qish).
    """

    queryset = Level.objects.filter(is_active=True).order_by('level')
    serializer_class = LevelSerializer
    permission_classes = [IsAuthenticated]


class TenureBracketViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Staj oralig'i API (faqat o'qish).
    """

    queryset = TenureBracket.objects.filter(is_active=True).order_by('min_months')
    serializer_class = TenureBracketSerializer
    permission_classes = [IsAuthenticated]


class MHTMHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    MHTM tarixi API (faqat o'qish).
    """

    queryset = MHTMHistory.objects.all().order_by('-effective_date')
    serializer_class = MHTMHistorySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Joriy MHTM."""
        mhtm = MHTMHistory.get_current()
        if mhtm:
            serializer = self.get_serializer(mhtm)
            return Response(serializer.data)
        return Response({'detail': 'MHTM topilmadi'}, status=status.HTTP_404_NOT_FOUND)
