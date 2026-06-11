"""
Payroll API views.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.employees.models import Employee
from apps.payroll.models import (
    TaxRate, SalaryComponent, PayrollPeriod, Payroll, PayrollItem
)
from .serializers import (
    TaxRateSerializer,
    SalaryComponentSerializer,
    PayrollPeriodListSerializer,
    PayrollPeriodDetailSerializer,
    PayrollPeriodCreateUpdateSerializer,
    PayrollListSerializer,
    PayrollDetailSerializer,
    PayrollUpdateSerializer,
    PayrollItemSerializer,
)


class TaxRateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Soliq stavkalari API (faqat o'qish).
    """

    queryset = TaxRate.objects.filter(is_active=True).order_by('-effective_date')
    serializer_class = TaxRateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tax_type']

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Joriy soliq stavkalari."""
        from django.utils import timezone
        today = timezone.now().date()

        rates = {}
        for tax_type, _ in TaxRate.TaxType.choices:
            rate = TaxRate.objects.filter(
                tax_type=tax_type,
                effective_date__lte=today,
                is_active=True
            ).order_by('-effective_date').first()
            if rate:
                rates[tax_type] = str(rate.rate)

        return Response(rates)


class SalaryComponentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Ish haqi komponentlari API (faqat o'qish).
    """

    queryset = SalaryComponent.objects.all().order_by('component_type', 'name')
    serializer_class = SalaryComponentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['component_type', 'is_taxable', 'is_statutory']


class PayrollPeriodViewSet(viewsets.ModelViewSet):
    """
    Ish haqi davrlari API.

    list: Barcha davrlar ro'yxati
    retrieve: Davr tafsiloti
    create: Yangi davr yaratish
    generate: Barcha xodimlar uchun ish haqi yaratish
    calculate: Davrdagi barcha ish haqlarni hisoblash
    confirm: Davrni tasdiqlash
    """

    queryset = PayrollPeriod.objects.all().order_by('-start_date')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['start_date', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PayrollPeriodListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PayrollPeriodCreateUpdateSerializer
        return PayrollPeriodDetailSerializer

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Davr uchun barcha xodimlar ish haqini yaratish."""
        period = self.get_object()

        if period.status != 'draft':
            return Response(
                {'error': "Faqat qoralama holatidagi davr uchun ish haqi yaratish mumkin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        employees = Employee.objects.filter(is_active=True, status='active')
        created_count = 0

        for employee in employees:
            payroll, created = Payroll.objects.get_or_create(
                period=period,
                employee=employee,
                defaults={'work_days': period.work_days}
            )
            if created:
                created_count += 1

        period.status = PayrollPeriod.Status.PROCESSING
        period.save()

        return Response({
            'message': f"{created_count} ta xodim uchun ish haqi yaratildi.",
            'created_count': created_count,
            'total_employees': employees.count()
        })

    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        """Davrdagi barcha ish haqlarni hisoblash."""
        period = self.get_object()

        if period.status not in ['draft', 'processing']:
            return Response(
                {'error': "Faqat qoralama yoki hisoblanmoqda holatidagi davr uchun hisoblash mumkin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        payrolls = period.payrolls.all()
        count = 0
        for payroll in payrolls:
            payroll.calculate()
            count += 1

        return Response({
            'message': f"{count} ta ish haqi hisoblandi.",
            'calculated_count': count
        })

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Davrni tasdiqlash."""
        period = self.get_object()

        if period.status != 'processing':
            return Response(
                {'error': "Faqat hisoblanmoqda holatidagi davrni tasdiqlash mumkin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        uncalculated = period.payrolls.filter(status='draft').count()
        if uncalculated > 0:
            return Response(
                {'error': f"{uncalculated} ta ish haqi hali hisoblanmagan."},
                status=status.HTTP_400_BAD_REQUEST
            )

        period.status = PayrollPeriod.Status.CONFIRMED
        period.save()
        period.payrolls.filter(status='calculated').update(status='confirmed')

        return Response({'message': "Davr tasdiqlandi."})

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Davrni to'langan deb belgilash."""
        period = self.get_object()

        if period.status != 'confirmed':
            return Response(
                {'error': "Faqat tasdiqlangan davrni to'langan deb belgilash mumkin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        period.status = PayrollPeriod.Status.PAID
        period.save()
        period.payrolls.filter(status='confirmed').update(status='paid')

        return Response({'message': "Davr to'langan deb belgilandi."})


class PayrollViewSet(viewsets.ModelViewSet):
    """
    Xodim ish haqi API.
    """

    queryset = Payroll.objects.select_related(
        'employee__user', 'employee__position', 'employee__department', 'period'
    ).prefetch_related('items__component')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['period', 'status', 'employee']
    search_fields = ['employee__employee_code', 'employee__user__first_name', 'employee__user__last_name']
    ordering_fields = ['net_salary', 'created_at']
    ordering = ['-period__start_date', 'employee__employee_code']

    def get_serializer_class(self):
        if self.action == 'list':
            return PayrollListSerializer
        elif self.action in ['update', 'partial_update']:
            return PayrollUpdateSerializer
        return PayrollDetailSerializer

    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        """Ish haqini hisoblash."""
        payroll = self.get_object()

        if payroll.status not in ['draft', 'calculated']:
            return Response(
                {'error': "Tasdiqlangan yoki to'langan ish haqini qayta hisoblash mumkin emas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        payroll.calculate()
        serializer = PayrollDetailSerializer(payroll)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Ish haqiga element qo'shish."""
        payroll = self.get_object()

        if payroll.status not in ['draft', 'calculated']:
            return Response(
                {'error': "Tasdiqlangan ish haqiga element qo'shish mumkin emas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PayrollItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(payroll=payroll)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='items/(?P<item_pk>[^/.]+)')
    def delete_item(self, request, pk=None, item_pk=None):
        """Ish haqi elementini o'chirish."""
        payroll = self.get_object()

        if payroll.status not in ['draft', 'calculated']:
            return Response(
                {'error': "Tasdiqlangan ish haqidan element o'chirish mumkin emas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = payroll.items.get(pk=item_pk)
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PayrollItem.DoesNotExist:
            return Response(
                {'error': "Element topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )
