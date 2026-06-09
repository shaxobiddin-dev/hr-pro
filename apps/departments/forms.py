"""
Department forms.
"""

from django import forms
from django.contrib.auth import get_user_model

from .models import Department

User = get_user_model()


class DepartmentForm(forms.ModelForm):
    """Bo'lim formasi."""

    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'parent', 'manager']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': "Bo'lim nomi"
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'DEP001'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Tavsif...'
            }),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Parent querysetini filtrlash
        self.fields['parent'].queryset = Department.objects.filter(is_active=True)
        self.fields['parent'].required = False

        # Manager - faqat staff userlar
        self.fields['manager'].queryset = User.objects.filter(is_active=True, is_staff=True)
        self.fields['manager'].required = False

        # O'zini o'ziga parent qilmaslik uchun
        if self.instance.pk:
            self.fields['parent'].queryset = self.fields['parent'].queryset.exclude(
                pk=self.instance.pk
            )
