"""
Payroll models - Ish haqi hisoblash tizimi.

O'zbekiston Soliq Kodeksi va Mehnat Kodeksiga mos:
- JSHDT: 12% (IT Park: 7.5%)
- INPS: 0.1%
- Ijtimoiy soliq: 12% (ish beruvchi)
"""

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import BaseModel


class TaxRate(models.Model):
    """
    Soliq stavkalari.

    Soliq qonunchiligidagi o'zgarishlarni kuzatish uchun.
    """

    class TaxType(models.TextChoices):
        JSHDT = 'jshdt', "JSHDT (Daromad solig'i)"
        JSHDT_IT = 'jshdt_it', "JSHDT (IT Park)"
        INPS = 'inps', "INPS (Pensiya fondi)"
        SOCIAL = 'social', "Ijtimoiy soliq"

    tax_type = models.CharField(
        max_length=20,
        choices=TaxType.choices,
        verbose_name="Soliq turi"
    )
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
        verbose_name="Stavka (%)"
    )
    effective_date = models.DateField(
        verbose_name="Kuchga kirish sanasi"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Izoh"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Soliq stavkasi"
        verbose_name_plural = "Soliq stavkalari"
        ordering = ['-effective_date', 'tax_type']
        unique_together = ['tax_type', 'effective_date']

    def __str__(self):
        return f"{self.get_tax_type_display()}: {self.rate}%"

    @classmethod
    def get_rate(cls, tax_type, date=None):
        """Berilgan sana uchun soliq stavkasini olish."""
        from django.utils import timezone
        if date is None:
            date = timezone.now().date()

        rate = cls.objects.filter(
            tax_type=tax_type,
            effective_date__lte=date,
            is_active=True
        ).order_by('-effective_date').first()

        if rate:
            return rate.rate / 100  # Foizdan koeffitsiyentga
        return Decimal("0")


class SalaryComponent(BaseModel):
    """
    Ish haqi tarkibiy qismlari.

    Qo'shimchalar va ushlanmalar.
    """

    class ComponentType(models.TextChoices):
        EARNING = 'earning', "Qo'shimcha (hisoblash)"
        DEDUCTION = 'deduction', "Ushlanma (ayirish)"

    class CalculationType(models.TextChoices):
        FIXED = 'fixed', "Qat'iy summa"
        PERCENTAGE = 'percentage', "Foiz (bazadan)"
        FORMULA = 'formula', "Formula"

    name = models.CharField(
        max_length=100,
        verbose_name="Nomi"
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Kod"
    )
    component_type = models.CharField(
        max_length=20,
        choices=ComponentType.choices,
        verbose_name="Turi"
    )
    calculation_type = models.CharField(
        max_length=20,
        choices=CalculationType.choices,
        default=CalculationType.FIXED,
        verbose_name="Hisoblash usuli"
    )
    default_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Standart qiymat"
    )
    is_taxable = models.BooleanField(
        default=True,
        verbose_name="Soliqqa tortiladimi"
    )
    is_statutory = models.BooleanField(
        default=False,
        verbose_name="Qonuniy (JSHDT, INPS)"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Tavsif"
    )

    class Meta:
        verbose_name = "Ish haqi komponenti"
        verbose_name_plural = "Ish haqi komponentlari"
        ordering = ['component_type', 'name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @classmethod
    def create_defaults(cls):
        """Standart komponentlarni yaratish."""
        defaults = [
            # Qo'shimchalar
            ('BASE', "Asosiy ish haqi", 'earning', 'formula', 0, True, False),
            ('BONUS', "Mukofot", 'earning', 'fixed', 0, True, False),
            ('OVERTIME', "Qo'shimcha ish", 'earning', 'fixed', 0, True, False),
            ('ALLOWANCE', "Nafaqa", 'earning', 'fixed', 0, False, False),

            # Ushlanmalar
            ('JSHDT', "JSHDT (12%)", 'deduction', 'percentage', 12, False, True),
            ('INPS', "INPS (0.1%)", 'deduction', 'percentage', 0.1, False, True),
            ('ADVANCE', "Avans", 'deduction', 'fixed', 0, False, False),
            ('ALIMONY', "Aliment", 'deduction', 'percentage', 0, False, False),
            ('OTHER_DED', "Boshqa ushlanmalar", 'deduction', 'fixed', 0, False, False),
        ]

        for code, name, comp_type, calc_type, value, taxable, statutory in defaults:
            cls.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'component_type': comp_type,
                    'calculation_type': calc_type,
                    'default_value': Decimal(str(value)),
                    'is_taxable': taxable,
                    'is_statutory': statutory,
                }
            )


class PayrollPeriod(BaseModel):
    """
    Ish haqi davri (oy).
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', "Qoralama"
        PROCESSING = 'processing', "Hisoblanmoqda"
        CONFIRMED = 'confirmed', "Tasdiqlangan"
        PAID = 'paid', "To'langan"
        CANCELLED = 'cancelled', "Bekor qilingan"

    name = models.CharField(
        max_length=50,
        verbose_name="Davr nomi"
    )
    start_date = models.DateField(
        verbose_name="Boshlanish sanasi"
    )
    end_date = models.DateField(
        verbose_name="Tugash sanasi"
    )
    payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="To'lov sanasi"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Holat"
    )
    work_days = models.PositiveSmallIntegerField(
        default=22,
        verbose_name="Ish kunlari"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Izohlar"
    )

    class Meta:
        verbose_name = "Ish haqi davri"
        verbose_name_plural = "Ish haqi davrlari"
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    @property
    def total_gross(self):
        """Jami yalpi ish haqi."""
        return sum(p.gross_salary for p in self.payrolls.all())

    @property
    def total_net(self):
        """Jami sof ish haqi."""
        return sum(p.net_salary for p in self.payrolls.all())

    @property
    def total_deductions(self):
        """Jami ushlanmalar."""
        return sum(p.total_deductions for p in self.payrolls.all())


class Payroll(BaseModel):
    """
    Xodim ish haqi hisob-kitobi.
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', "Qoralama"
        CALCULATED = 'calculated', "Hisoblangan"
        CONFIRMED = 'confirmed', "Tasdiqlangan"
        PAID = 'paid', "To'langan"

    period = models.ForeignKey(
        PayrollPeriod,
        on_delete=models.CASCADE,
        related_name='payrolls',
        verbose_name="Davr"
    )
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='payrolls',
        verbose_name="Xodim"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Holat"
    )

    # Ish kunlari
    work_days = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Ishlangan kunlar"
    )
    absent_days = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Kelmaган kunlar"
    )
    leave_days = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Ta'til kunlari"
    )
    sick_days = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Kasallik kunlari"
    )

    # Summalar
    base_salary = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Asosiy ish haqi"
    )
    gross_salary = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Yalpi ish haqi"
    )
    total_earnings = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Jami qo'shimchalar"
    )
    total_deductions = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Jami ushlanmalar"
    )
    net_salary = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Sof ish haqi"
    )

    # Soliqlar (tafsilot uchun)
    jshdt_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="JSHDT"
    )
    inps_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="INPS"
    )

    notes = models.TextField(
        blank=True,
        verbose_name="Izohlar"
    )

    class Meta:
        verbose_name = "Ish haqi"
        verbose_name_plural = "Ish haqlari"
        ordering = ['-period__start_date', 'employee__employee_code']
        unique_together = ['period', 'employee']

    def __str__(self):
        return f"{self.employee.employee_code} - {self.period.name}"

    def get_employee_salary(self):
        """
        Xodimning joriy oylik maoshini olish.

        Avvalo ishga olish buyrug'idan olinadi.
        Agar buyruq topilmasa, formula bilan hisoblanadi.
        """
        from apps.employees.models import MHTMHistory

        # Ishga olish buyrug'ini tekshirish
        hiring_item = self.employee.hiring_order_items.select_related('order').filter(
            order__status='approved'
        ).order_by('-order__order_date').first()

        if hiring_item:
            # Buyruqdagi current_salary (sinov muddatini ham hisobga oladi)
            return hiring_item.current_salary

        # Buyruq topilmasa, formula bilan hisoblash
        mhtm = MHTMHistory.get_current()
        return self.employee.calculate_base_salary(mhtm)

    def load_from_timesheet(self):
        """Tabeldan ma'lumotlarni yuklash."""
        from apps.attendance.models import MonthlyTimesheet

        # Davr oyi va yilini aniqlash
        year = self.period.start_date.year
        month = self.period.start_date.month

        try:
            timesheet = MonthlyTimesheet.objects.get(
                employee=self.employee,
                year=year,
                month=month
            )
            # Tabeldan ma'lumotlarni olish
            self.work_days = timesheet.present_days + timesheet.late_days
            self.absent_days = timesheet.absent_days
            self.leave_days = timesheet.leave_days
            self.sick_days = timesheet.sick_days
            return True
        except MonthlyTimesheet.DoesNotExist:
            # Tabel topilmasa, davomatlardan to'g'ridan-to'g'ri hisoblash
            return self._calculate_from_attendances()

    def _calculate_from_attendances(self):
        """Davomatlardan kunlarni hisoblash (tabel yo'q bo'lsa)."""
        from apps.attendance.models import Attendance

        year = self.period.start_date.year
        month = self.period.start_date.month

        attendances = Attendance.objects.filter(
            employee=self.employee,
            date__year=year,
            date__month=month
        )

        self.work_days = attendances.filter(
            status__in=[Attendance.Status.PRESENT, Attendance.Status.LATE]
        ).count()
        self.absent_days = attendances.filter(status=Attendance.Status.ABSENT).count()
        self.leave_days = attendances.filter(status=Attendance.Status.ON_LEAVE).count()
        self.sick_days = attendances.filter(status=Attendance.Status.SICK).count()

        return self.work_days > 0

    def calculate(self):
        """Ish haqini hisoblash."""
        # 1. Asosiy ish haqi - buyruqdan olish
        self.base_salary = self.get_employee_salary()

        # 2. Tabeldan ishlangan kunlarni yuklash
        self.load_from_timesheet()

        # 3. Ishlangan kunlar bo'yicha hisoblash
        period_days = self.period.work_days

        # Nol bo'lmasligini ta'minlash
        if period_days == 0:
            period_days = 22

        # Ishlangan kunlar - tabeldan olinadi
        actual_days = self.work_days  # 0 bo'lsa 0 qoladi!

        day_rate = self.base_salary / Decimal(period_days)

        # Proporsional hisoblash
        calculated_salary = day_rate * Decimal(actual_days)

        # 3. Qo'shimchalar
        earnings = Decimal("0")
        for item in self.items.filter(component__component_type='earning'):
            if item.component.code != 'BASE':
                earnings += item.amount

        self.total_earnings = earnings
        self.gross_salary = calculated_salary + earnings

        # 4. Soliqlar
        # JSHDT - 12% (yoki IT Park 7.5%) - xodimdan ushlanadi
        jshdt_rate = TaxRate.get_rate(TaxRate.TaxType.JSHDT) or Decimal("0.12")
        total_jshdt = self.gross_salary * jshdt_rate

        # INPS - 0.1% - JSHDT ichidan to'lanadi, alohida ushlanmaydi!
        # INPS jamg'armasiga: JSHDT summasidan 0.1%
        # JSHDT jamg'armasiga: JSHDT - INPS
        inps_rate = TaxRate.get_rate(TaxRate.TaxType.INPS) or Decimal("0.001")
        self.inps_amount = self.gross_salary * inps_rate
        self.jshdt_amount = total_jshdt - self.inps_amount  # JSHDT jamg'armasiga ketadigan qism

        # 5. Boshqa ushlanmalar
        other_deductions = Decimal("0")
        for item in self.items.filter(component__component_type='deduction'):
            if item.component.code not in ['JSHDT', 'INPS']:
                other_deductions += item.amount

        # Xodimdan faqat JSHDT (12%) ushlanadi, INPS alohida ushlanmaydi
        self.total_deductions = total_jshdt + other_deductions

        # 6. Sof ish haqi
        self.net_salary = self.gross_salary - self.total_deductions

        self.status = self.Status.CALCULATED
        self.save()

        return self


class PayrollItem(BaseModel):
    """
    Ish haqi tafsiloti (qo'shimcha/ushlanma).
    """

    payroll = models.ForeignKey(
        Payroll,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Ish haqi"
    )
    component = models.ForeignKey(
        SalaryComponent,
        on_delete=models.PROTECT,
        verbose_name="Komponent"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Summa"
    )
    notes = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Izoh"
    )

    class Meta:
        verbose_name = "Ish haqi elementi"
        verbose_name_plural = "Ish haqi elementlari"
        ordering = ['component__component_type', 'component__name']

    def __str__(self):
        return f"{self.payroll} - {self.component.name}: {self.amount}"
