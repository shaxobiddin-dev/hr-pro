"""
Department API views.
"""

from django.db import models
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count

from apps.departments.models import Department
from .serializers import (
    DepartmentListSerializer,
    DepartmentDetailSerializer,
    DepartmentCreateUpdateSerializer,
    DepartmentTreeSerializer,
)


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    Bo'limlar API.

    list: Barcha bo'limlar ro'yxati
    retrieve: Bo'lim tafsiloti
    create: Yangi bo'lim yaratish
    update: Bo'lim ma'lumotlarini yangilash
    destroy: Bo'limni o'chirish (soft delete)
    tree: Bo'limlar daraxti
    """

    queryset = Department.objects.filter(is_active=True).annotate(
        employee_count=Count('employees', filter=models.Q(employees__is_active=True))
    ).select_related('parent')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return DepartmentListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DepartmentCreateUpdateSerializer
        elif self.action == 'tree':
            return DepartmentTreeSerializer
        return DepartmentDetailSerializer

    def perform_destroy(self, instance):
        """Soft delete."""
        instance.soft_delete()

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Bo'limlar daraxti (faqat root bo'limlar)."""
        root_departments = Department.objects.filter(
            parent__isnull=True,
            is_active=True
        )
        serializer = DepartmentTreeSerializer(root_departments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Bo'limdagi xodimlar."""
        department = self.get_object()
        employees = department.employees.filter(is_active=True).select_related('user', 'position', 'level')

        from apps.employees.api.serializers import EmployeeListSerializer
        serializer = EmployeeListSerializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Bo'limlar statistikasi."""
        total = Department.objects.filter(is_active=True).count()
        with_employees = Department.objects.filter(
            is_active=True,
            employees__is_active=True
        ).distinct().count()

        return Response({
            'total': total,
            'with_employees': with_employees,
            'empty': total - with_employees,
        })
