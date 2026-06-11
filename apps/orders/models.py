"""
Buyruqlar modeli - Orders module.

Ishga olish, o'tkazish, bo'shatish va boshqa buyruqlar.
"""

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date

from apps.core.models import BaseModel, SoftDeleteModel


class Order(SoftDeleteModel):
    """
    Buyruq - asosiy model.

    Har xil turdagi buyruqlar uchun umumiy model.
    """

    class OrderType(models.TextChoices):
        HIRING = 'hiring', "Ishga qabul qilish"
        TRANSFER = 'transfer', "Boshqa lavozimga o'tkazish"
        TERMINATION = 'termination', "Mehnat shartnomasini bekor qilish"
        PROMOTION = 'promotion', "Rag'batlantirish"
        DISCIPLINARY = 'disciplinary', "Intizomiy jazo"
        LEAVE = 'leave', "Ta'til"
        TEMPORARY_DUTY = 'temporary_duty', "Vaqtincha vazifa yuklash"
        SALARY_CHANGE = 'salary_change', "Oylik o'zgartirish"

    class Status(models.TextChoices):
        DRAFT = 'draft', "Qoralama"
        PENDING = 'pending', "Tasdiqlanmoqda"
        APPROVED = 'approved', "Tasdiqlangan"
        REJECTED = 'rejected', "Rad etilgan"
        CANCELLED = 'cancelled', "Bekor qilingan"

    # Buyruq raqami
    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Buyruq raqami"
    )

    # Buyruq turi
    order_type = models.CharField(
        max_length=20,
        choices=OrderType.choices,
        verbose_name="Buyruq turi"
    )

    # Buyruq sanasi
    order_date = models.DateField(
        default=date.today,
        verbose_name="Buyruq sanasi"
    )

    # Holat
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Holat"
    )

    # Asos (umumiy)
    legal_basis = models.TextField(
        blank=True,
        verbose_name="Asos",
        help_text="Mehnat kodeksi moddalari, arizalar va boshqa asoslar"
    )

    # Kim tasdiqlaydi
    approved_by = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_orders',
        verbose_name="Tasdiqlovchi"
    )

    # Tasdiqlangan sana
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Tasdiqlangan vaqt"
    )

    # Izohlar
    notes = models.TextField(
        blank=True,
        verbose_name="Izohlar"
    )

    # Kim yaratdi
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_orders',
        verbose_name="Yaratuvchi"
    )

    class Meta:
        verbose_name = "Buyruq"
        verbose_name_plural = "Buyruqlar"
        ordering = ['-order_date', '-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.get_order_type_display()}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    @classmethod
    def generate_order_number(cls):
        """Avtomatik buyruq raqami generatsiya."""
        year = timezone.now().year

        # Faqat YYYY-NNN formatdagi buyruqlarni olish (YYYY-001, YYYY-002, ...)
        # YYYY-TEST-001 kabi formatlarni HISOBGA OLMAYMIZ
        numeric_orders = cls.objects.filter(
            order_number__regex=rf'^{year}-\d{{3}}$'
        )

        if numeric_orders.exists():
            # Eng katta raqamni topish
            max_num = 0
            for order in numeric_orders:
                try:
                    num = int(order.order_number.split('-')[1])
                    if num > max_num:
                        max_num = num
                except (ValueError, IndexError):
                    continue
            next_num = max_num + 1
        else:
            next_num = 1

        return f"{year}-{next_num:03d}"

    def approve(self, approved_by):
        """Buyruqni tasdiqlash."""
        self.status = self.Status.APPROVED
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save()

        # Ishga olish buyrug'i bo'lsa, xodimlarni aktivlashtirish
        if self.order_type == self.OrderType.HIRING:
            for item in self.hiring_items.all():
                item.activate_employee()

    def can_hard_delete(self):
        """Buyruqni to'liq o'chirish mumkinmi?"""
        # Faqat tasdiqlangan buyruqlar arxivlanadi, qolganlari o'chirilishi mumkin
        return self.status != self.Status.APPROVED


class HiringOrderItem(BaseModel):
    """
    Ishga olish buyrug'i qatori.

    Har bir xodim uchun alohida ma'lumotlar.
    """

    class ContractType(models.TextChoices):
        INDEFINITE = 'indefinite', "Nomuayyan muddatga"
        FIXED_TERM = 'fixed_term', "Muayyan muddatga"

    class WorkSchedule(models.TextChoices):
        FULL_TIME = 'full_time', "To'liq ish kuni"
        PART_TIME = 'part_time', "To'liqsiz ish kuni"
        PART_WEEK = 'part_week', "To'liqsiz ish haftasi"

    # Buyruq
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='hiring_items',
        verbose_name="Buyruq"
    )

    # Xodim (mavjud yoki yangi)
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='hiring_order_items',
        verbose_name="Xodim"
    )

    # Asosiy ma'lumotlar
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        verbose_name="Bo'lim"
    )

    position = models.ForeignKey(
        'employees.Position',
        on_delete=models.PROTECT,
        verbose_name="Lavozim"
    )

    # Shartnoma turi (nomuayyan/muayyan - sanalar asosida avtomatik)
    contract_type = models.CharField(
        max_length=20,
        choices=ContractType.choices,
        default=ContractType.INDEFINITE,
        verbose_name="Shartnoma turi"
    )

    # Ish boshlash sanasi
    start_date = models.DateField(
        verbose_name="Ish boshlash sanasi"
    )

    # Tugash sanasi (faqat muayyan muddat uchun)
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Tugash sanasi",
        help_text="Faqat muayyan muddatli shartnoma uchun"
    )

    # Oylik maosh
    salary = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Oylik maosh"
    )

    # Stavka
    rate = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("1.00"),
        verbose_name="Stavka",
        help_text="Masalan: 0.5, 1.0, 1.5"
    )

    # Ish tartibi
    work_schedule = models.CharField(
        max_length=20,
        choices=WorkSchedule.choices,
        default=WorkSchedule.FULL_TIME,
        verbose_name="Ish tartibi"
    )

    # ===== SINOV MUDDATI =====
    has_probation = models.BooleanField(
        default=False,
        verbose_name="Sinov muddati bor"
    )

    probation_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Sinov muddati tugash sanasi"
    )

    probation_salary = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Sinov muddati oyligi",
        help_text="Bo'sh qolsa asosiy oylik olinadi"
    )

    # Sinov muddatida boshqa bo'lim/lavozim (ixtiyoriy)
    probation_department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='probation_hiring_items',
        verbose_name="Sinov muddati bo'limi"
    )

    probation_position = models.ForeignKey(
        'employees.Position',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='probation_hiring_items',
        verbose_name="Sinov muddati lavozimi"
    )

    # Shartnoma raqami (agar bor bo'lsa)
    contract_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Mehnat shartnomasi raqami"
    )

    contract_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Mehnat shartnomasi sanasi"
    )

    class Meta:
        verbose_name = "Ishga olish qatori"
        verbose_name_plural = "Ishga olish qatorlari"
        ordering = ['id']

    def __str__(self):
        return f"{self.employee} - {self.position}"

    def save(self, *args, **kwargs):
        # Shartnoma turini avtomatik belgilash
        if self.end_date:
            self.contract_type = self.ContractType.FIXED_TERM
        else:
            self.contract_type = self.ContractType.INDEFINITE

        super().save(*args, **kwargs)

    @property
    def current_salary(self):
        """Hozirgi oylik (sinov muddatida bo'lsa sinov oyligi)."""
        if self.has_probation and self.probation_end_date:
            if date.today() <= self.probation_end_date:
                return self.probation_salary or self.salary
        return self.salary

    @property
    def current_department(self):
        """Hozirgi bo'lim."""
        if self.has_probation and self.probation_end_date:
            if date.today() <= self.probation_end_date:
                return self.probation_department or self.department
        return self.department

    @property
    def current_position(self):
        """Hozirgi lavozim."""
        if self.has_probation and self.probation_end_date:
            if date.today() <= self.probation_end_date:
                return self.probation_position or self.position
        return self.position

    @property
    def is_in_probation(self):
        """Sinov muddatida yoki yo'q."""
        if not self.has_probation or not self.probation_end_date:
            return False
        return date.today() <= self.probation_end_date

    def activate_employee(self):
        """Xodimni faollashtirish (buyruq tasdiqlanganda)."""
        employee = self.employee
        employee.department = self.current_department
        employee.position = self.current_position
        employee.hire_date = self.start_date
        employee.status = 'active'
        employee.save()
