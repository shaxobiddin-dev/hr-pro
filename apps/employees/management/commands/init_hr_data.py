"""
Initialize HR default data - levels, tenure brackets, MHTM.

Usage:
    python manage.py init_hr_data
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.employees.models import Level, TenureBracket, MHTMHistory


class Command(BaseCommand):
    help = "Initialize HR default data (levels, tenure brackets, MHTM)"

    def handle(self, *args, **options):
        self.stdout.write("HR boshlang'ich ma'lumotlarini yaratish...")

        # 1. Darajalar (10-level system)
        self.stdout.write("\n1. Darajalar yaratilmoqda...")
        Level.create_defaults()
        self.stdout.write(self.style.SUCCESS(f"   ✓ {Level.objects.count()} ta daraja"))

        # 2. Staj koeffitsiyentlari
        self.stdout.write("\n2. Staj koeffitsiyentlari yaratilmoqda...")
        TenureBracket.create_defaults()
        self.stdout.write(self.style.SUCCESS(f"   ✓ {TenureBracket.objects.count()} ta staj oralig'i"))

        # 3. MHTM tarixi
        self.stdout.write("\n3. MHTM tarixi yaratilmoqda...")
        mhtm_data = [
            ("2024-01-01", 1050000, "PQ-26 14.12.2023"),
            ("2025-01-01", 1200000, "PQ-... 2024"),
        ]
        for date, amount, decree in mhtm_data:
            obj, created = MHTMHistory.objects.get_or_create(
                effective_date=date,
                defaults={
                    'amount': Decimal(amount),
                    'decree_number': decree,
                }
            )
            if created:
                self.stdout.write(f"   + MHTM {date}: {amount:,} so'm")
            else:
                self.stdout.write(f"   - MHTM {date} mavjud")

        self.stdout.write(self.style.SUCCESS(f"   ✓ {MHTMHistory.objects.count()} ta MHTM yozuvi"))

        self.stdout.write(self.style.SUCCESS("\n✅ Boshlang'ich ma'lumotlar yaratildi!"))
