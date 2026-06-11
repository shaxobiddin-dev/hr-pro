"""
Employee forms - Xodim formatlari.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from .models import Employee, Position, Level
from apps.departments.models import Department

User = get_user_model()


class EmployeeForm(forms.ModelForm):
    """
    Xodim TAHRIRLASH formasi.
    Yangi xodim faqat "Ishga olish buyrug'i" orqali yaratiladi.
    """

    # User fields
    first_name = forms.CharField(
        label="Ism",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ism'
        })
    )
    last_name = forms.CharField(
        label="Familiya",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Familiya'
        })
    )
    phone = forms.CharField(
        label="Telefon",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+998 90 123-45-67'
        })
    )

    class Meta:
        model = Employee
        fields = ['department', 'position', 'level', 'manager', 'prior_experience_months']
        widgets = {
            'department': forms.Select(attrs={
                'class': 'form-select',
                'hx-get': '/employees/api/positions-by-department/',
                'hx-target': '#id_position',
                'hx-trigger': 'change',
                'hx-include': '[name=position]',
            }),
            'position': forms.Select(attrs={'class': 'form-select', 'id': 'id_position'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'prior_experience_months': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # User ma'lumotlarini to'ldirish
        if self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['phone'].initial = self.instance.user.phone

            # Bo'limga tegishli lavozimlarni filtrlash
            if self.instance.department_id:
                self.fields['position'].queryset = Position.objects.filter(
                    is_active=True,
                    department_id=self.instance.department_id
                )

        # Querysetlarni optimallashtirish
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        if not self.instance.pk or not self.instance.department_id:
            self.fields['position'].queryset = Position.objects.filter(is_active=True)
        self.fields['level'].queryset = Level.objects.filter(is_active=True).order_by('level')
        self.fields['manager'].queryset = Employee.objects.filter(
            is_active=True, status=Employee.Status.ACTIVE
        ).select_related('user')
        self.fields['manager'].required = False
        self.fields['prior_experience_months'].required = False

    def save(self, commit=True):
        employee = super().save(commit=False)

        # User ma'lumotlarini yangilash
        user = employee.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone', '')
        user.save()

        if commit:
            employee.save()

        return employee


class PositionForm(forms.ModelForm):
    """Lavozim formasi."""

    class Meta:
        model = Position
        fields = ['name', 'code', 'department', 'base_coefficient', 'min_level', 'max_level', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'code': forms.TextInput(attrs={'class': 'form-input'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'base_coefficient': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0.01'}),
            'min_level': forms.Select(attrs={'class': 'form-select'}),
            'max_level': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['min_level'].queryset = Level.objects.filter(is_active=True).order_by('level')
        self.fields['max_level'].queryset = Level.objects.filter(is_active=True).order_by('level')
        self.fields['min_level'].required = False
        self.fields['max_level'].required = False
