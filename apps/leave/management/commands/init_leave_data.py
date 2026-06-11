"""
Ta'til default ma'lumotlarini yaratish.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal

from apps.leave.models import LeaveType, LeaveBalance
from apps.employees.models import Employee


class Command(BaseCommand):
    help = "Ta'til turlari va balanslarini yaratish"

    def handle(self, *args, **options):
        self.stdout.write("Ta'til ma'lumotlari yaratilmoqda...")

        # 1. Ta'til turlari
        self.stdout.write("Ta'til turlari...")
        LeaveType.create_defaults()
        self.stdout.write(self.style.SUCCESS(
            f"  ✓ {LeaveType.objects.count()} ta ta'til turi"
        ))

        # 2. Xodimlar uchun yillik ta'til balanslari
        year = timezone.now().year
        annual_leave = LeaveType.objects.filter(code='ANNUAL').first()

        if annual_leave:
            employees = Employee.objects.filter(is_active=True, status='active')
            created = 0

            for emp in employees:
                # Yangi Mehnat Kodeksi: 21 kalendar kun (barcha uchun bir xil)
                # Maxsus toifalar (o'qituvchi, sudya, nogironlar) uchun alohida sozlash kerak
                days = 21

                balance, was_created = LeaveBalance.objects.get_or_create(
                    employee=emp,
                    leave_type=annual_leave,
                    year=year,
                    defaults={'entitled_days': Decimal(str(days))}
                )
                if was_created:
                    created += 1

            self.stdout.write(self.style.SUCCESS(
                f"  ✓ {created} ta xodim uchun {year} yillik balans yaratildi"
            ))

        self.stdout.write(self.style.SUCCESS("\n✓ Ta'til ma'lumotlari muvaffaqiyatli yaratildi!"))
