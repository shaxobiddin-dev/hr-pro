"""
Custom allauth adapters.

Ro'yxatdan o'tish yopiq - faqat admin panel orqali foydalanuvchi yaratiladi.
"""

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


class NoSignupAccountAdapter(DefaultAccountAdapter):
    """
    Ro'yxatdan o'tishni to'xtatuvchi adapter.

    Mijozlar uchun login/parol admin panel orqali beriladi.
    """

    def is_open_for_signup(self, request):
        """Ro'yxatdan o'tish yopiq."""
        return False
