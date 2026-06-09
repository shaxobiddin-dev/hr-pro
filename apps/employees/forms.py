"""
Employee forms - Xodim formatlari.
"""

from django import forms
from django.contrib.auth import get_user_model

from .models import Employee, Position, Level
from apps.departments.models import Department

User = get_user_model()


class EmployeeForm(forms.ModelForm):
    """Xodim yaratish/tahrirlash formasi."""

    # User fields
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'email@example.com'
        })
    )
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
        fields = [
            'department', 'position', 'level', 'manager',
            'contract_type', 'hire_date', 'contract_end_date',
            'probation_end_date', 'prior_experience_months', 'status'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'probation_end_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'prior_experience_months': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Agar tahrirlash bo'lsa, user ma'lumotlarini to'ldirish
        if self.instance.pk:
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['phone'].initial = self.instance.user.phone
            self.fields['email'].widget.attrs['readonly'] = True

        # Querysetlarni optimallashtirish
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['position'].queryset = Position.objects.filter(is_active=True)
        self.fields['level'].queryset = Level.objects.filter(is_active=True).order_by('level')
        self.fields['manager'].queryset = Employee.objects.filter(
            is_active=True, status=Employee.Status.ACTIVE
        ).select_related('user')
        self.fields['manager'].required = False

    def save(self, commit=True):
        employee = super().save(commit=False)

        # Yangi xodim uchun user yaratish
        if not employee.pk:
            user = User.objects.create_user(
                email=self.cleaned_data['email'],
                password=User.objects.make_random_password(),
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                phone=self.cleaned_data.get('phone', ''),
            )
            employee.user = user
            employee.employee_code = Employee.generate_employee_code()
        else:
            # Mavjud user ma'lumotlarini yangilash
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
