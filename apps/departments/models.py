"""
Department models - Bo'limlar boshqaruvi.
"""

from django.db import models
from django.conf import settings

from apps.core.models import SoftDeleteModel


class Department(SoftDeleteModel):
    """
    Bo'lim modeli.

    Ierarxik tuzilma - har bir bo'lim boshqa bo'limga bo'ysunishi mumkin.
    """

    name = models.CharField(
        max_length=100,
        verbose_name="Bo'lim nomi"
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Bo'lim kodi"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Tavsif"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Yuqori bo'lim"
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name="Bo'lim boshlig'i"
    )

    class Meta:
        verbose_name = "Bo'lim"
        verbose_name_plural = "Bo'limlar"
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def full_path(self):
        """Bo'limning to'liq yo'li (ierarxiya)."""
        if self.parent:
            return f"{self.parent.full_path} / {self.name}"
        return self.name

    @property
    def employee_count(self):
        """Bo'limdagi xodimlar soni."""
        return self.employees.filter(is_active=True).count()
