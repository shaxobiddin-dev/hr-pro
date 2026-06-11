"""
Ta'til modeli - O'zbekiston Mehnat Kodeksiga mos.

Mehnat Kodeksi 134-modda:
- Asosiy yillik ta'til: kamida 15 ish kuni
- Qo'shimcha ta'til: 3-15 kun (ish sharoitiga qarab)
- Kasallik varaqasi: 100% (5 yildan ortiq staj)
"""

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone

from apps.core.models import BaseModel


class LeaveType(BaseModel):
    """
    Ta'til turi.

    Masalan: Yillik ta'til, Kasallik, To'lanmaydigan ta'til
    """

    class Category(models.TextChoices):
        ANNUAL = 'annual', "Yillik ta'til"
        SICK = 'sick', "Kasallik varaqasi"
        UNPAID = 'unpaid', "To'lanmaydigan ta'til"
        MATERNITY = 'maternity', "Ona ta'tili"
        PATERNITY = 'paternity', "Ota ta'tili"
        STUDY = 'study', "O'quv ta'tili"
        OTHER = 'other', "Boshqa"

    name = models.CharField(
        max_length=100,
        verbose_name="Nomi"
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Kod"
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.ANNUAL,
        verbose_name="Kategoriya"
    )

    # Kunlar (Yangi MK: 21 kalendar kun minimal)
    default_days = models.PositiveSmallIntegerField(
        default=21,
        verbose_name="Standart kunlar (yillik)"
    )
    max_days = models.PositiveSmallIntegerField(
        default=30,
        verbose_name="Maksimal kunlar"
    )
    min_days = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Minimal kunlar"
    )

    # Qoidalar
    is_paid = models.BooleanField(
        default=True,
        verbose_name="To'lanadimi"
    )
    requires_document = models.BooleanField(
        default=False,
        verbose_name="Hujjat talab qilinadimi"
    )
    can_be_carried_forward = models.BooleanField(
        default=True,
        verbose_name="Keyingi yilga o'tkazilishi mumkinmi"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Tavsif"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Faol"
    )

    class Meta:
        verbose_name = "Ta'til turi"
        verbose_name_plural = "Ta'til turlari"
        ordering = ['name']

    def __str__(self):
        return self.name

    @classmethod
    def create_defaults(cls):
        """Standart ta'til turlarini yaratish (Yangi MK 2023)."""
        defaults = [
            # Yangi MK: 21 kalendar kun minimal
            ('ANNUAL', "Yillik mehnat ta'tili", 'annual', 21, 24, 15, True, False, True),
            ('SICK', "Kasallik varaqasi", 'sick', 0, 120, 1, True, True, False),
            ('UNPAID', "To'lanmaydigan ta'til", 'unpaid', 0, 30, 1, False, False, False),
            ('MATERNITY', "Homiladorlik va tug'ruq ta'tili", 'maternity', 126, 140, 70, True, True, False),
            ('PATERNITY', "Ota ta'tili (bola tug'ilganda)", 'paternity', 3, 14, 1, True, True, False),
            ('STUDY', "O'quv ta'tili", 'study', 0, 60, 1, True, True, False),
        ]

        for code, name, category, default_days, max_days, min_days, paid, doc, carry in defaults:
            cls.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'category': category,
                    'default_days': default_days,
                    'max_days': max_days,
                    'min_days': min_days,
                    'is_paid': paid,
                    'requires_document': doc,
                    'can_be_carried_forward': carry,
                }
            )


class LeaveBalance(BaseModel):
    """
    Xodim ta'til balansi (yillik).

    Har yili yangi balans yaratiladi.
    """

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='leave_balances',
        verbose_name="Xodim"
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name='balances',
        verbose_name="Ta'til turi"
    )
    year = models.PositiveSmallIntegerField(
        verbose_name="Yil"
    )

    # Kunlar
    entitled_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal("15"),
        verbose_name="Berilgan kunlar"
    )
    carried_forward = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal("0"),
        verbose_name="O'tkazilgan kunlar"
    )
    used_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal("0"),
        verbose_name="Ishlatilgan kunlar"
    )

    class Meta:
        verbose_name = "Ta'til balansi"
        verbose_name_plural = "Ta'til balanslari"
        unique_together = ['employee', 'leave_type', 'year']
        ordering = ['-year', 'employee']

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.year})"

    @property
    def total_days(self):
        """Jami mavjud kunlar."""
        return self.entitled_days + self.carried_forward

    @property
    def remaining_days(self):
        """Qolgan kunlar."""
        return self.total_days - self.used_days

    @property
    def usage_percentage(self):
        """Ishlatilgan foiz."""
        if self.total_days == 0:
            return 0
        return round((self.used_days / self.total_days) * 100, 1)


class LeaveRequest(BaseModel):
    """
    Ta'til so'rovi.

    Xodim yuboradi, rahbar tasdiqlaydi.
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', "Qoralama"
        PENDING = 'pending', "Ko'rib chiqilmoqda"
        APPROVED = 'approved', "Tasdiqlangan"
        REJECTED = 'rejected', "Rad etilgan"
        CANCELLED = 'cancelled', "Bekor qilingan"

    # Asosiy ma'lumotlar
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='leave_requests',
        verbose_name="Xodim"
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name='requests',
        verbose_name="Ta'til turi"
    )

    # Sanalar
    start_date = models.DateField(
        verbose_name="Boshlanish sanasi"
    )
    end_date = models.DateField(
        verbose_name="Tugash sanasi"
    )

    # Kunlar (avtomatik hisoblanadi)
    requested_days = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal("0"),
        verbose_name="So'ralgan kunlar"
    )

    # Holat
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Holat"
    )

    # Izohlar
    reason = models.TextField(
        blank=True,
        verbose_name="Sabab"
    )

    # Tasdiqlash
    approved_by = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves',
        verbose_name="Tasdiqlagan"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Tasdiqlangan vaqt"
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Rad etish sababi"
    )

    # Hujjat
    document = models.FileField(
        upload_to='leave_documents/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="Hujjat"
    )

    class Meta:
        verbose_name = "Ta'til so'rovi"
        verbose_name_plural = "Ta'til so'rovlari"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.start_date} - {self.end_date})"

    def save(self, *args, **kwargs):
        # Kunlarni hisoblash
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            self.requested_days = Decimal(str(delta.days + 1))
        super().save(*args, **kwargs)

    def submit(self):
        """So'rovni yuborish."""
        if self.status == self.Status.DRAFT:
            self.status = self.Status.PENDING
            self.save()
            return True
        return False

    def approve(self, approved_by):
        """So'rovni tasdiqlash."""
        if self.status != self.Status.PENDING:
            return False

        self.status = self.Status.APPROVED
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save()

        # Xodim holatini yangilash
        self._update_employee_status()

        # Balansdan ayirish
        self._deduct_from_balance()

        return True

    def reject(self, rejected_by, reason=""):
        """So'rovni rad etish."""
        if self.status != self.Status.PENDING:
            return False

        self.status = self.Status.REJECTED
        self.approved_by = rejected_by
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.save()
        return True

    def cancel(self):
        """So'rovni bekor qilish."""
        if self.status in [self.Status.DRAFT, self.Status.PENDING]:
            self.status = self.Status.CANCELLED
            self.save()
            return True
        return False

    def _update_employee_status(self):
        """Xodim holatini yangilash (ta'tilda)."""
        today = timezone.now().date()
        if self.start_date <= today <= self.end_date:
            self.employee.status = 'on_leave'
            self.employee.save()

    def _deduct_from_balance(self):
        """Balansdan kunlarni ayirish."""
        if self.leave_type.category == LeaveType.Category.ANNUAL:
            year = self.start_date.year
            balance, created = LeaveBalance.objects.get_or_create(
                employee=self.employee,
                leave_type=self.leave_type,
                year=year,
                defaults={'entitled_days': self.leave_type.default_days}
            )
            balance.used_days += self.requested_days
            balance.save()

    @property
    def is_active(self):
        """Hozirda faolmi."""
        today = timezone.now().date()
        return (
            self.status == self.Status.APPROVED and
            self.start_date <= today <= self.end_date
        )

    @property
    def days_until_start(self):
        """Ta'tilgacha qolgan kunlar."""
        today = timezone.now().date()
        if self.start_date > today:
            return (self.start_date - today).days
        return 0
