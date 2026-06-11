"""
Attendance modeli - Xodimlar davomati.

Kelish/Ketish vaqti, ish kunlari hisobi.
"""

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

from apps.core.models import BaseModel


class Attendance(BaseModel):
    """
    Kunlik davomat yozuvi.

    Har bir xodim uchun kunlik kelish/ketish.
    """

    class Status(models.TextChoices):
        PRESENT = 'present', "Keldi"
        ABSENT = 'absent', "Kelmadi"
        LATE = 'late', "Kechikdi"
        HALF_DAY = 'half_day', "Yarim kun"
        ON_LEAVE = 'on_leave', "Ta'tilda"
        SICK = 'sick', "Kasallik"
        BUSINESS_TRIP = 'business_trip', "Xizmat safari"

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name="Xodim"
    )
    date = models.DateField(
        verbose_name="Sana"
    )

    # Kelish/Ketish vaqti
    check_in = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Kelish vaqti"
    )
    check_out = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Ketish vaqti"
    )

    # Holat
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PRESENT,
        verbose_name="Holat"
    )

    # Ish soatlari (avtomatik hisoblanadi)
    work_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Ish soatlari"
    )

    # Kechikish (daqiqalarda)
    late_minutes = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Kechikish (daqiqa)"
    )

    # Erta ketish (daqiqalarda)
    early_leave_minutes = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Erta ketish (daqiqa)"
    )

    # Izoh
    notes = models.TextField(
        blank=True,
        verbose_name="Izoh"
    )

    # Kim tomonidan kiritilgan
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_attendances',
        verbose_name="Kiritgan"
    )

    class Meta:
        verbose_name = "Davomat"
        verbose_name_plural = "Davomatlar"
        unique_together = ['employee', 'date']
        ordering = ['-date', 'employee']

    def __str__(self):
        return f"{self.employee} - {self.date} ({self.get_status_display()})"

    # Holatlar - ish soatlari kiritilmaydigan
    STATUSES_NO_TIME = ['sick', 'on_leave', 'absent']
    # Xizmat safari va yarim kun bundan mustasno

    def save(self, *args, **kwargs):
        # Kasallik, ta'til, kelmadi holatlari uchun vaqtlarni tozalash
        # Xizmat safari bundan mustasno - boshqa joyda ishlayotgan bo'ladi
        if self.status in self.STATUSES_NO_TIME:
            self.check_in = None
            self.check_out = None
            self.work_hours = Decimal("0")
            self.late_minutes = 0
            self.early_leave_minutes = 0

        # Kechikdi/keldi bo'lsa va ketish vaqti yo'q - avtomatik 18:00
        if self.status in [self.Status.LATE, self.Status.PRESENT] and self.check_in and not self.check_out:
            self.check_out = datetime.strptime("18:00", "%H:%M").time()

        # Ish soatlarini hisoblash
        if self.check_in and self.check_out:
            check_in_dt = datetime.combine(self.date, self.check_in)
            check_out_dt = datetime.combine(self.date, self.check_out)

            if check_out_dt > check_in_dt:
                diff = check_out_dt - check_in_dt
                hours = diff.total_seconds() / 3600
                # Tushlik uchun 1 soat ayirish (agar 6 soatdan ko'p bo'lsa)
                if hours > 6:
                    hours -= 1
                self.work_hours = Decimal(str(round(hours, 2)))

        # Kechikishni hisoblash (09:00 dan keyin)
        if self.check_in:
            standard_start = datetime.strptime("09:00", "%H:%M").time()
            if self.check_in > standard_start:
                check_in_dt = datetime.combine(self.date, self.check_in)
                standard_dt = datetime.combine(self.date, standard_start)
                diff = check_in_dt - standard_dt
                self.late_minutes = int(diff.total_seconds() / 60)
                if self.late_minutes > 0 and self.status == self.Status.PRESENT:
                    self.status = self.Status.LATE
            else:
                self.late_minutes = 0

        # Erta ketishni hisoblash (18:00 dan oldin)
        if self.check_out:
            standard_end = datetime.strptime("18:00", "%H:%M").time()
            if self.check_out < standard_end:
                check_out_dt = datetime.combine(self.date, self.check_out)
                standard_dt = datetime.combine(self.date, standard_end)
                diff = standard_dt - check_out_dt
                self.early_leave_minutes = int(diff.total_seconds() / 60)
            else:
                self.early_leave_minutes = 0

        super().save(*args, **kwargs)

    @property
    def is_full_day(self):
        """To'liq ish kuni (8 soat)."""
        return self.work_hours >= 8

    @property
    def check_in_display(self):
        """Kelish vaqti formatlangan."""
        return self.check_in.strftime("%H:%M") if self.check_in else "-"

    @property
    def check_out_display(self):
        """Ketish vaqti formatlangan."""
        return self.check_out.strftime("%H:%M") if self.check_out else "-"


class MonthlyTimesheet(BaseModel):
    """
    Oylik tabel.

    Har bir xodim uchun oylik umumlashtirish.
    """

    class Status(models.TextChoices):
        DRAFT = 'draft', "Qoralama"
        CONFIRMED = 'confirmed', "Tasdiqlangan"

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='timesheets',
        verbose_name="Xodim"
    )
    year = models.PositiveSmallIntegerField(
        verbose_name="Yil"
    )
    month = models.PositiveSmallIntegerField(
        verbose_name="Oy"
    )

    # Kunlar
    work_days = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Ish kunlari (rejadagi)"
    )
    present_days = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Kelgan kunlar"
    )
    absent_days = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Kelmagan kunlar"
    )
    late_days = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Kechikkan kunlar"
    )
    leave_days = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Ta'til kunlari"
    )
    sick_days = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Kasallik kunlari"
    )

    # Soatlar
    total_work_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Jami ish soatlari"
    )
    total_late_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name="Jami kechikish (daqiqa)"
    )

    # Holat
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Holat"
    )

    confirmed_by = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_timesheets',
        verbose_name="Tasdiqlagan"
    )
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Tasdiqlangan vaqt"
    )

    class Meta:
        verbose_name = "Oylik tabel"
        verbose_name_plural = "Oylik tabellar"
        unique_together = ['employee', 'year', 'month']
        ordering = ['-year', '-month', 'employee']

    def __str__(self):
        return f"{self.employee} - {self.month}/{self.year}"

    @property
    def month_name(self):
        """Oy nomi."""
        months = [
            '', 'Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun',
            'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr'
        ]
        return months[self.month]

    @property
    def attendance_percentage(self):
        """Davomat foizi."""
        if self.work_days == 0:
            return 0
        return round((self.present_days / self.work_days) * 100, 1)

    def calculate_from_attendances(self):
        """Davomatlardan hisoblash."""
        from django.db.models import Sum, Count

        attendances = Attendance.objects.filter(
            employee=self.employee,
            date__year=self.year,
            date__month=self.month
        )

        self.present_days = attendances.filter(
            status__in=[Attendance.Status.PRESENT, Attendance.Status.LATE]
        ).count()

        self.absent_days = attendances.filter(
            status=Attendance.Status.ABSENT
        ).count()

        self.late_days = attendances.filter(
            status=Attendance.Status.LATE
        ).count()

        self.leave_days = attendances.filter(
            status=Attendance.Status.ON_LEAVE
        ).count()

        self.sick_days = attendances.filter(
            status=Attendance.Status.SICK
        ).count()

        totals = attendances.aggregate(
            total_hours=Sum('work_hours'),
            total_late=Sum('late_minutes')
        )

        self.total_work_hours = totals['total_hours'] or Decimal("0")
        self.total_late_minutes = totals['total_late'] or 0

        self.save()

    def confirm(self, confirmed_by):
        """Tabelni tasdiqlash."""
        self.status = self.Status.CONFIRMED
        self.confirmed_by = confirmed_by
        self.confirmed_at = timezone.now()
        self.save()
