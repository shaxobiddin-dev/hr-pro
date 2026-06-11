"""
Leave forms.
"""

from decimal import Decimal
from django import forms
from django.utils import timezone
from .models import LeaveRequest, LeaveType, LeaveBalance
from apps.employees.models import Employee


class LeaveRequestForm(forms.ModelForm):
    """Ta'til so'rovi formasi."""

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.eligible_for_operations(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
        }),
        label="Xodim"
    )

    class Meta:
        model = LeaveRequest
        fields = ['employee', 'leave_type', 'start_date', 'end_date', 'reason', 'document']
        widgets = {
            'leave_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'reason': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': "Ta'til sababi..."
            }),
            'document': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee', None)
        self.is_admin = kwargs.pop('is_admin', False)
        super().__init__(*args, **kwargs)
        self.fields['leave_type'].queryset = LeaveType.objects.filter(is_active=True)

        # Admin bo'lmasa xodim tanlash kerak emas
        if not self.is_admin:
            del self.fields['employee']
        else:
            # Admin uchun xodim tanlash majburiy - faqat buyruqi tasdiqlangan
            self.fields['employee'].required = True
            self.fields['employee'].queryset = Employee.objects.eligible_for_operations(
            ).select_related('user').order_by('user__last_name', 'user__first_name')

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        leave_type = cleaned_data.get('leave_type')

        # Xodimni aniqlash
        if self.is_admin:
            emp = cleaned_data.get('employee')
        else:
            emp = self.employee

        # Buyruq tekshiruvi
        if emp and not emp.has_approved_hiring_order:
            raise forms.ValidationError(
                f"{emp.full_name} uchun ishga olish buyrug'i tasdiqlanmagan."
            )

        if start_date and end_date:
            # Sanalar tekshiruvi
            if start_date > end_date:
                raise forms.ValidationError("Boshlanish sanasi tugash sanasidan oldin bo'lishi kerak.")

            # O'tmishdagi sana
            today = timezone.now().date()
            if start_date < today:
                raise forms.ValidationError("O'tmishdagi sanaga ta'til so'rovi yuborib bo'lmaydi.")

            # Kunlar soni
            days = (end_date - start_date).days + 1

            if leave_type:
                if days < leave_type.min_days:
                    raise forms.ValidationError(
                        f"Minimal {leave_type.min_days} kun bo'lishi kerak."
                    )
                if days > leave_type.max_days:
                    raise forms.ValidationError(
                        f"Maksimal {leave_type.max_days} kun bo'lishi mumkin."
                    )

                # Balans tekshiruvi (faqat yillik ta'til uchun)
                if emp and leave_type.category == 'annual':
                    year = start_date.year

                    # Xodim qancha vaqt ishlagan
                    hire_date = emp.hire_date
                    months_worked = (today.year - hire_date.year) * 12 + (today.month - hire_date.month)

                    # 6 oy ishlash sharti (MK 219-modda)
                    if months_worked < 6:
                        raise forms.ValidationError(
                            f"Yillik ta'til olish uchun kamida 6 oy ishlash kerak. "
                            f"Siz {months_worked} oy ishladingiz."
                        )

                    # 6 oy ishlagan bo'lsa - to'liq 21-24 kun olishi mumkin
                    balance = LeaveBalance.objects.filter(
                        employee=emp,
                        leave_type=leave_type,
                        year=year
                    ).first()

                    if balance:
                        if Decimal(str(days)) > balance.remaining_days:
                            raise forms.ValidationError(
                                f"Yetarli balans yo'q. Qolgan: {balance.remaining_days:.0f} kun, so'ralgan: {days} kun."
                            )
                    else:
                        raise forms.ValidationError(
                            f"{year} yil uchun ta'til balansi topilmadi."
                        )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Admin xodim tanladi, oddiy foydalanuvchi o'zi
        if self.is_admin:
            instance.employee = self.cleaned_data.get('employee')
        elif self.employee:
            instance.employee = self.employee
        if commit:
            instance.save()
        return instance


class LeaveApprovalForm(forms.Form):
    """Ta'tilni tasdiqlash/rad etish formasi."""

    action = forms.ChoiceField(
        choices=[('approve', 'Tasdiqlash'), ('reject', 'Rad etish')],
        widget=forms.RadioSelect(attrs={'class': 'mr-2'})
    )
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg',
            'placeholder': "Rad etish sababi (ixtiyoriy)"
        })
    )
