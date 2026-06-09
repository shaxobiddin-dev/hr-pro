"""
Payroll boshlang'ich ma'lumotlarini yaratish.

Ishlatish:
    python manage.py init_payroll_data
"""

from decimal import Decimal
from datetime import date
from django.core.management.base import BaseCommand

from apps.payroll.models import TaxRate, SalaryComponent


class Command(BaseCommand):
    help = "Payroll uchun boshlang'ich ma'lumotlarni yaratish (soliq stavkalari, komponentlar)"

    def handle(self, *args, **options):
        self.stdout.write("Payroll ma'lumotlari yaratilmoqda...")

        # Soliq stavkalari
        self.create_tax_rates()

        # Ish haqi komponentlari
        self.create_salary_components()

        self.stdout.write(self.style.SUCCESS("Payroll ma'lumotlari muvaffaqiyatli yaratildi!"))

    def create_tax_rates(self):
        """Soliq stavkalarini yaratish."""
        rates = [
            (TaxRate.TaxType.JSHDT, Decimal("12.00"), "Jismoniy shaxslar daromad solig'i - standart stavka"),
            (TaxRate.TaxType.JSHDT_IT, Decimal("7.50"), "JSHDT IT Park rezidentlari uchun"),
            (TaxRate.TaxType.INPS, Decimal("0.10"), "Ijtimoiy nafaqa pensiya sug'urtasi"),
            (TaxRate.TaxType.SOCIAL, Decimal("12.00"), "Ijtimoiy soliq (ish beruvchi to'laydi)"),
        ]

        created_count = 0
        for tax_type, rate, description in rates:
            obj, created = TaxRate.objects.get_or_create(
                tax_type=tax_type,
                effective_date=date(2024, 1, 1),
                defaults={
                    'rate': rate,
                    'description': description,
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"  + {obj}")

        self.stdout.write(f"  Soliq stavkalari: {created_count} ta yaratildi")

    def create_salary_components(self):
        """Ish haqi komponentlarini yaratish."""
        SalaryComponent.create_defaults()
        self.stdout.write(f"  Ish haqi komponentlari yaratildi")
