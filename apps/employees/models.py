"""
Employee models - Xodimlar boshqaruvi.

Asosiy ish haqi formulasi:
ISH_HAQI = MHTM × JOB_COEF × LEVEL_COEF × TENURE_COEF
"""

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import SoftDeleteModel


class Level(SoftDeleteModel):
    """
    10-darajali professional daraja tizimi.

    Har bir daraja o'z koeffitsiyentiga ega.
    """

    LEVEL_CHOICES = [
        (1, "Level 1 - Entry-level specialist"),
        (2, "Level 2 - Junior specialist"),
        (3, "Level 3 - Mid-level specialist"),
        (4, "Level 4 - Independent specialist"),
        (5, "Level 5 - Experienced specialist"),
        (6, "Level 6 - Highly qualified specialist"),
        (7, "Level 7 - Senior specialist"),
        (8, "Level 8 - Lead specialist"),
        (9, "Level 9 - Principal lead specialist"),
        (10, "Level 10 - Chief specialist"),
    ]

    # Default koeffitsiyentlar
    DEFAULT_COEFFICIENTS = {
        1: Decimal("1.00"),
        2: Decimal("1.10"),
        3: Decimal("1.20"),
        4: Decimal("1.30"),
        5: Decimal("1.40"),
        6: Decimal("1.55"),
        7: Decimal("1.70"),
        8: Decimal("1.85"),
        9: Decimal("2.00"),
        10: Decimal("2.20"),
    }

    level = models.PositiveSmallIntegerField(
        choices=LEVEL_CHOICES,
        unique=True,
        verbose_name="Daraja"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Daraja nomi"
    )
    coefficient = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Koeffitsiyent"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Tavsif"
    )

    class Meta:
        verbose_name = "Daraja"
        verbose_name_plural = "Darajalar"
        ordering = ['level']

    def __str__(self):
        return f"Level {self.level} - {self.name} (×{self.coefficient})"

    @classmethod
    def create_defaults(cls):
        """Standart 10 darajani yaratish."""
        for level_num, label in cls.LEVEL_CHOICES:
            name = label.split(" - ")[1]
            coef = cls.DEFAULT_COEFFICIENTS[level_num]
            cls.objects.get_or_create(
                level=level_num,
                defaults={
                    'name': name,
                    'coefficient': coef,
                }
            )


class TenureBracket(SoftDeleteModel):
    """
    Ish staji koeffitsiyentlari.

    Staj bo'yicha qo'shimcha koeffitsiyent.
    """

    name = models.CharField(
        max_length=50,
        verbose_name="Nomi"
    )
    min_months = models.PositiveIntegerField(
        verbose_name="Minimum oylar"
    )
    max_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Maksimum oylar",
        help_text="Bo'sh qoldirilsa - cheksiz"
    )
    coefficient = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Koeffitsiyent"
    )

    class Meta:
        verbose_name = "Staj koeffitsiyenti"
        verbose_name_plural = "Staj koeffitsiyentlari"
        ordering = ['min_months']

    def __str__(self):
        if self.max_months:
            return f"{self.name}: {self.min_months}-{self.max_months} oy (×{self.coefficient})"
        return f"{self.name}: {self.min_months}+ oy (×{self.coefficient})"

    @classmethod
    def create_defaults(cls):
        """Standart staj koeffitsiyentlarini yaratish."""
        defaults = [
            ("0-6 oy", 0, 6, Decimal("1.00")),
            ("6 oy - 1 yil", 6, 12, Decimal("1.10")),
            ("1-3 yil", 12, 36, Decimal("1.20")),
            ("3-6 yil", 36, 72, Decimal("1.30")),
            ("6+ yil", 72, None, Decimal("1.40")),
        ]
        for name, min_m, max_m, coef in defaults:
            cls.objects.get_or_create(
                min_months=min_m,
                defaults={
                    'name': name,
                    'max_months': max_m,
                    'coefficient': coef,
                }
            )

    @classmethod
    def get_coefficient(cls, months):
        """Berilgan staj uchun koeffitsiyentni qaytarish."""
        bracket = cls.objects.filter(
            is_active=True,
            min_months__lte=months
        ).filter(
            models.Q(max_months__gt=months) | models.Q(max_months__isnull=True)
        ).first()
        return bracket.coefficient if bracket else Decimal("1.00")


class Position(SoftDeleteModel):
    """
    Lavozim modeli.

    Har bir lavozimning o'z bazaviy koeffitsiyenti bor.
    """

    name = models.CharField(
        max_length=100,
        verbose_name="Lavozim nomi"
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Lavozim kodi"
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='positions',
        verbose_name="Bo'lim"
    )
    base_coefficient = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Bazaviy koeffitsiyent"
    )
    min_level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='min_positions',
        verbose_name="Minimal daraja"
    )
    max_level = models.ForeignKey(
        Level,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='max_positions',
        verbose_name="Maksimal daraja"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Lavozim tavsifi"
    )
    requirements = models.TextField(
        blank=True,
        verbose_name="Talablar"
    )

    class Meta:
        verbose_name = "Lavozim"
        verbose_name_plural = "Lavozimlar"
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class MHTMHistory(models.Model):
    """
    MHTM (Mehnatga Haq To'lashning Minimal Miqdori) tarixi.

    MHTM har yili o'zgaradi, bu model tarixni saqlaydi.
    """

    effective_date = models.DateField(
        unique=True,
        verbose_name="Kuchga kirish sanasi"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="MHTM miqdori (so'm)"
    )
    decree_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Qaror raqami"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Izohlar"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "MHTM tarixi"
        verbose_name_plural = "MHTM tarixi"
        ordering = ['-effective_date']
        get_latest_by = 'effective_date'

    def __str__(self):
        return f"MHTM {self.effective_date}: {self.amount:,.0f} so'm"

    @classmethod
    def get_current(cls):
        """Joriy MHTM qiymatini olish."""
        from django.utils import timezone
        today = timezone.now().date()
        mhtm = cls.objects.filter(effective_date__lte=today).first()
        if mhtm:
            return mhtm.amount
        return Decimal(settings.MHTM_DEFAULT)


class EmployeeQuerySet(models.QuerySet):
    """Employee uchun custom queryset."""

    def active(self):
        """Faqat faol xodimlar."""
        return self.filter(is_active=True, status='active')

    def with_approved_order(self):
        """Faqat tasdiqlangan buyruqli xodimlar."""
        from apps.orders.models import HiringOrderItem, Order
        approved_employee_ids = HiringOrderItem.objects.filter(
            order__status=Order.Status.APPROVED
        ).values_list('employee_id', flat=True)
        return self.filter(id__in=approved_employee_ids)

    def eligible_for_operations(self):
        """Operatsiyalar uchun yaroqli xodimlar (active + buyruqli)."""
        return self.active().with_approved_order()


class EmployeeManager(models.Manager):
    """Employee uchun custom manager."""

    def get_queryset(self):
        return EmployeeQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def with_approved_order(self):
        return self.get_queryset().with_approved_order()

    def eligible_for_operations(self):
        return self.get_queryset().eligible_for_operations()


class Employee(SoftDeleteModel):
    """
    Xodim modeli.

    User bilan bog'langan, ammo alohida model.
    Bir user bir nechta kompaniyalarda ishlashi mumkin (future).
    """

    class Status(models.TextChoices):
        PENDING = 'pending', "Kutilmoqda"  # Buyruq tasdiqlanmagan
        ACTIVE = 'active', "Faol"
        ON_LEAVE = 'on_leave', "Ta'tilda"
        SUSPENDED = 'suspended', "To'xtatilgan"
        TERMINATED = 'terminated', "Ishdan bo'shatilgan"

    class ContractType(models.TextChoices):
        PERMANENT = 'permanent', "Doimiy"
        FIXED_TERM = 'fixed_term', "Muddatli"
        PROBATION = 'probation', "Sinov muddati"
        PART_TIME = 'part_time', "Yarim stavka"

    # Asosiy ma'lumotlar
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee',
        verbose_name="Foydalanuvchi"
    )
    employee_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Xodim kodi"
    )

    # Tashkiliy ma'lumotlar
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name="Bo'lim"
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name="Lavozim"
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name="Daraja"
    )
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        verbose_name="Bevosita rahbar"
    )

    # Mehnat shartnomasi
    contract_type = models.CharField(
        max_length=20,
        choices=ContractType.choices,
        default=ContractType.PERMANENT,
        verbose_name="Shartnoma turi"
    )
    hire_date = models.DateField(
        verbose_name="Ishga kirgan sana"
    )
    contract_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Shartnoma tugash sanasi"
    )
    probation_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Sinov muddati tugashi"
    )

    # Oldingi staj
    prior_experience_months = models.PositiveIntegerField(
        default=0,
        verbose_name="Oldingi ish staji (oylar)"
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,  # Buyruq tasdiqlanmaguncha PENDING
        verbose_name="Holat"
    )
    termination_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Ishdan bo'shatilgan sana"
    )
    termination_reason = models.TextField(
        blank=True,
        verbose_name="Ishdan bo'shatilish sababi"
    )

    # Custom manager
    objects = EmployeeManager()

    class Meta:
        verbose_name = "Xodim"
        verbose_name_plural = "Xodimlar"
        ordering = ['employee_code']

    def __str__(self):
        return f"{self.employee_code} - {self.user.get_full_name()}"

    @property
    def full_name(self):
        """Xodimning to'liq ismi."""
        return self.user.get_full_name()

    @property
    def tenure_months(self):
        """Umumiy ish staji (oylar)."""
        from django.utils import timezone
        if self.termination_date:
            end_date = self.termination_date
        else:
            end_date = timezone.now().date()

        # Yillar va oylarni hisoblash
        months = (end_date.year - self.hire_date.year) * 12
        months += end_date.month - self.hire_date.month

        # Oldingi stajni qo'shish
        return months + self.prior_experience_months

    @property
    def tenure_coefficient(self):
        """Staj bo'yicha koeffitsiyent."""
        return TenureBracket.get_coefficient(self.tenure_months)

    def calculate_base_salary(self, mhtm=None):
        """
        Bazaviy ish haqini hisoblash.

        Formula: MHTM × JOB_COEF × LEVEL_COEF × TENURE_COEF
        """
        if mhtm is None:
            mhtm = MHTMHistory.get_current()

        job_coef = self.position.base_coefficient
        level_coef = self.level.coefficient
        tenure_coef = self.tenure_coefficient

        return mhtm * job_coef * level_coef * tenure_coef

    @classmethod
    def generate_employee_code(cls):
        """Yangi xodim kodi generatsiya qilish."""
        from django.utils import timezone
        year = timezone.now().year
        prefix = f"EMP{year}"

        last = cls.objects.filter(
            employee_code__startswith=prefix
        ).order_by('-employee_code').first()

        if last:
            try:
                num = int(last.employee_code[-4:]) + 1
            except ValueError:
                num = 1
        else:
            num = 1

        return f"{prefix}{num:04d}"

    def soft_delete(self):
        """
        Xodimni arxivlash.

        - is_active = False
        - status = TERMINATED
        - termination_date = bugun
        - Bog'liq buyruqlar: tasdiqlangan -> arxiv, qolganlar -> o'chirish
        """
        from django.utils import timezone

        # Bog'liq buyruqlarni boshqarish
        self._handle_related_orders()

        self.is_active = False
        self.status = self.Status.TERMINATED
        self.termination_date = timezone.now().date()
        self.deleted_at = timezone.now()
        self.save()

    def _handle_related_orders(self):
        """
        Xodimga bog'liq buyruqlarni boshqarish.

        - Tasdiqlangan buyruqlar → arxivlanadi (soft delete)
        - Qolgan buyruqlar → o'chiriladi (hard delete)
        """
        from apps.orders.models import HiringOrderItem, Order

        # Ishga olish buyruqlari
        hiring_items = HiringOrderItem.objects.filter(employee=self).select_related('order')

        for item in hiring_items:
            order = item.order
            if order.status == Order.Status.APPROVED:
                # Tasdiqlangan buyruq - arxivlash
                order.soft_delete()
            else:
                # Qolgan buyruqlar - o'chirish
                order.delete()

    def restore(self):
        """
        Xodimni arxivdan tiklash.

        - is_active = True
        - status = ACTIVE
        - termination_date = None
        """
        self.is_active = True
        self.status = self.Status.ACTIVE
        self.termination_date = None
        self.deleted_at = None
        self.save()

    @property
    def has_approved_hiring_order(self):
        """Tasdiqlangan ishga olish buyrug'i bormi?"""
        from apps.orders.models import HiringOrderItem, Order
        return HiringOrderItem.objects.filter(
            employee=self,
            order__status=Order.Status.APPROVED
        ).exists()

    @property
    def is_eligible_for_operations(self):
        """
        Xodim uchun operatsiyalar (davomat, ta'til, ish haqi)
        bajarish mumkinmi?

        Shartlar:
        1. status = ACTIVE
        2. Tasdiqlangan ishga olish buyrug'i mavjud
        """
        return (
            self.status == self.Status.ACTIVE and
            self.has_approved_hiring_order
        )
