"""
Core models - Base classes for all models.
"""

from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model for all HR-Pro models.

    Provides:
        - created_at: Record creation timestamp
        - updated_at: Record update timestamp
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Yangilangan vaqt"
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteModel(BaseModel):
    """
    Abstract model with soft delete capability.

    Provides:
        - is_active: Soft delete flag
        - deleted_at: Deletion timestamp
    """

    is_active = models.BooleanField(
        default=True,
        verbose_name="Faol"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="O'chirilgan vaqt"
    )

    class Meta:
        abstract = True

    def soft_delete(self):
        """Mark record as deleted."""
        from django.utils import timezone
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at', 'updated_at'])

    def restore(self):
        """Restore soft-deleted record."""
        self.is_active = True
        self.deleted_at = None
        self.save(update_fields=['is_active', 'deleted_at', 'updated_at'])
