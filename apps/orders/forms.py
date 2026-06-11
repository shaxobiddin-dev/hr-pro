"""
Buyruqlar formasi.
"""

from django import forms
from django.forms import inlineformset_factory
from decimal import Decimal

from .models import Order, HiringOrderItem
from apps.employees.models import Employee, Position, MHTMHistory
from apps.departments.models import Department
from apps.accounts.models import User


class OrderForm(forms.ModelForm):
    """Buyruq asosiy formasi."""

    class Meta:
        model = Order
        fields = ['order_number', 'order_date', 'approved_by', 'legal_basis', 'notes']
        widgets = {
            'order_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
                'placeholder': 'Avtomatik generatsiya qilinadi'
            }),
            'order_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'
            }),
            'approved_by': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'
            }),
            'legal_basis': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
                'placeholder': "O'zbekiston Respublikasi Mehnat kodeksining 127-moddasi..."
            }),
            'notes': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
                'placeholder': 'Qo\'shimcha izohlar...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Tasdiqlovchilar - faqat managerlar (keyinroq filter qo'shiladi)
        self.fields['approved_by'].queryset = Employee.objects.filter(
            is_active=True,
            status='active'
        ).select_related('user', 'position').order_by('user__last_name')

        self.fields['approved_by'].label_from_instance = lambda obj: f"{obj.full_name} - {obj.position.name if obj.position else 'Lavozim belgilanmagan'}"

        # Buyruq raqami - avtomatik generatsiya bo'lsa
        if not self.instance.pk:
            self.fields['order_number'].initial = Order.generate_order_number()

    def clean_order_number(self):
        """Order number uniqueness check."""
        order_number = self.cleaned_data.get('order_number')
        if order_number:
            # Yangi buyruq uchun
            if not self.instance.pk:
                if Order.objects.filter(order_number=order_number).exists():
                    raise forms.ValidationError(f"Bu buyruq raqami ({order_number}) allaqachon mavjud.")
            else:
                # Tahrirlashda - o'z raqamidan tashqari tekshirish
                if Order.objects.filter(order_number=order_number).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError(f"Bu buyruq raqami ({order_number}) allaqachon mavjud.")
        return order_number


class HiringOrderItemForm(forms.ModelForm):
    """Ishga olish qatori formasi."""

    # Yangi xodim yaratish uchun
    is_new_employee = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-indigo-600 focus:ring-indigo-500',
            'x-model': 'isNewEmployee'
        })
    )

    # Yangi xodim ma'lumotlari
    new_first_name = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Ism',
            'x-show': 'isNewEmployee'
        })
    )
    new_last_name = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Familiya',
            'x-show': 'isNewEmployee'
        })
    )
    new_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Email',
            'x-show': 'isNewEmployee'
        })
    )

    class Meta:
        model = HiringOrderItem
        fields = [
            'employee', 'department', 'position', 'start_date', 'end_date',
            'salary', 'work_schedule',
            'has_probation', 'probation_end_date', 'probation_salary',
            'probation_department', 'probation_position',
            'contract_number', 'contract_date'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 employee-select',
                'x-show': '!isNewEmployee'
            }),
            'department': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 department-select',
                'x-on:change': 'loadPositions($event.target.value)',
                ':disabled': '!isNewEmployee'
            }),
            'position': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 position-select',
                'x-on:change': 'loadSalary($event.target.value)',
                ':disabled': '!isNewEmployee'
            }),
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'
            }),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
                'placeholder': 'Nomuayyan muddat uchun bo\'sh qoldiring'
            }),
            'salary': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 salary-input',
                'step': '0.01',
                'min': '0'
            }),
            'rate': forms.NumberInput(attrs={
                'class': 'w-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
                'step': '0.25',
                'min': '0.25',
                'max': '2.0'
            }),
            'work_schedule': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'
            }),
            'has_probation': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-indigo-600 focus:ring-indigo-500',
                'x-model': 'hasProbation'
            }),
            'probation_end_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
                'x-show': 'hasProbation'
            }),
            'probation_salary': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Bo\'sh qolsa asosiy oylik',
                'x-show': 'hasProbation'
            }),
            'probation_department': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
                'x-show': 'hasProbation'
            }),
            'probation_position': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
                'x-show': 'hasProbation'
            }),
            'contract_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
                'placeholder': 'Shartnoma raqami'
            }),
            'contract_date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Xodimlar - ishga olish buyrug'i yo'qlar
        self.fields['employee'].queryset = Employee.objects.filter(
            is_active=True
        ).exclude(
            hiring_order_items__order__status='approved'
        ).select_related('user').order_by('user__last_name')

        self.fields['employee'].label_from_instance = lambda obj: f"{obj.employee_code} - {obj.full_name}"
        self.fields['employee'].required = False

        # Bo'limlar
        departments = Department.objects.filter(is_active=True)
        self.fields['department'].queryset = departments
        self.fields['probation_department'].queryset = departments
        self.fields['probation_department'].required = False

        # Lavozimlar
        positions = Position.objects.filter(is_active=True)
        self.fields['position'].queryset = positions
        self.fields['probation_position'].queryset = positions
        self.fields['probation_position'].required = False

    def is_empty_row(self):
        """Qator bo'shmi tekshirish."""
        data = self.data
        prefix = self.prefix

        # Xodim tanlanmaganmi?
        employee = data.get(f'{prefix}-employee', '')
        is_new = data.get(f'{prefix}-is_new_employee', '')

        # Agar yangi xodim emas va xodim tanlanmagan - bo'sh qator
        if not is_new and not employee:
            return True
        return False

    def clean(self):
        cleaned_data = super().clean()

        # Agar bo'sh qator bo'lsa - validatsiya qilmaslik
        if self.is_empty_row() and not self.instance.pk:
            # Barcha xatolarni tozalash
            self._errors = {}
            return cleaned_data

        is_new = cleaned_data.get('is_new_employee')
        employee = cleaned_data.get('employee')

        if is_new:
            # Yangi xodim uchun validatsiya
            if not cleaned_data.get('new_first_name'):
                self.add_error('new_first_name', 'Ism kiritilishi shart')
            if not cleaned_data.get('new_last_name'):
                self.add_error('new_last_name', 'Familiya kiritilishi shart')
            if not cleaned_data.get('new_email'):
                self.add_error('new_email', 'Email kiritilishi shart')
            else:
                # Email mavjudligini tekshirish
                new_email = cleaned_data.get('new_email')
                if User.objects.filter(email=new_email).exists():
                    self.add_error('new_email', f'Bu email ({new_email}) allaqachon ro\'yxatdan o\'tgan')

        # Sinov muddati validatsiya
        has_probation = cleaned_data.get('has_probation')
        if has_probation:
            probation_end = cleaned_data.get('probation_end_date')
            start_date = cleaned_data.get('start_date')

            if not probation_end:
                self.add_error('probation_end_date', 'Sinov muddati tugash sanasini kiriting')
            elif start_date and probation_end <= start_date:
                self.add_error('probation_end_date', 'Sinov muddati ish boshlash sanasidan keyin bo\'lishi kerak')

        # Muayyan muddat validatsiya
        end_date = cleaned_data.get('end_date')
        start_date = cleaned_data.get('start_date')
        if end_date and start_date and end_date <= start_date:
            self.add_error('end_date', 'Tugash sanasi boshlash sanasidan keyin bo\'lishi kerak')

        return cleaned_data


# Inline formset
HiringOrderItemFormSet = inlineformset_factory(
    Order,
    HiringOrderItem,
    form=HiringOrderItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)
