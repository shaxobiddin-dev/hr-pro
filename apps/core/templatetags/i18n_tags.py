"""
i18n uchun custom template taglar.

Foydalanish:
    {% load i18n_tags %}
    <a href="{% switch_lang 'en' %}">English</a>
"""

from django import template
from django.urls import translate_url

register = template.Library()


@register.simple_tag(takes_context=True)
def switch_lang(context, lang_code):
    """
    Joriy sahifa URL'ini boshqa tilga tarjima qiladi.

    Misol:
        /ru/about/ + 'en' -> /en/about/
        /ru/about/ + 'uz' -> /about/  (default til, prefix yo'q)
        /about/ + 'ru' -> /ru/about/

    Args:
        context: Template context (request kerak)
        lang_code: Yangi til kodi ('uz', 'ru', 'en')

    Returns:
        str: Yangi til uchun URL
    """
    request = context.get('request')
    if not request:
        return '/'

    path = request.path

    # Django'ning translate_url funksiyasi
    # URL'ni boshqa tilga tarjima qiladi
    translated_url = translate_url(path, lang_code)

    return translated_url
