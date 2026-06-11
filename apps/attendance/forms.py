"""
Attendance forms.
"""

from django import forms
from django.utils import timezone
from .models import Attendance, MonthlyTimesheet
from apps.employees.models import Employee


class AttendanceForm(forms.ModelForm):
    """Davomat formasi."""

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.eligible_for_operations(),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'
        }),
        label="Xodim"
    )

    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'check_in', 'check_out', 'status', 'notes']
        widgets = {
            'date': forms.DateInput(format='%Y-%m-%d', attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'
            }),
            'check_in': forms.TimeInput(format='%H:%M', attrs={
                'type': 'time',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'
            }),
            'check_out': forms.TimeInput(format='%H:%M', attrs={
                'type': 'time',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500',
                'placeholder': 'Izoh...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.is_edit = kwargs.pop('is_edit', False)
        super().__init__(*args, **kwargs)
        # Faqat buyruqi tasdiqlangan xodimlar
        self.fields['employee'].queryset = Employee.objects.eligible_for_operations(
        ).select_related('user').order_by('user__last_name')

        # Tahrirlashda xodim va sana o'zgarmasin
        if self.is_edit:
            self.fields['employee'].disabled = True
            self.fields['date'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        status = cleaned_data.get('status')
        employee = cleaned_data.get('employee')
        date = cleaned_data.get('date')

        # Xodim uchun tasdiqlangan buyruq bormi?
        if employee and not employee.has_approved_hiring_order:
            raise forms.ValidationError(
                f"{employee.full_name} uchun ishga olish buyrug'i tasdiqlanmagan. "
                "Avval buyruqni tasdiqlang."
            )

        # Sana tekshiruvlari
        if employee and date:
            today = timezone.now().date()

            # 1. Kelajak sanasiga davomat kiritish mumkin emas
            if date > today:
                raise forms.ValidationError(
                    f"Kelajak sanasiga ({date.strftime('%d.%m.%Y')}) davomat kiritish mumkin emas."
                )

            # 2. Xodimning ishga kirish sanasidan oldingi davomat mumkin emas
            if employee.hire_date and date < employee.hire_date:
                raise forms.ValidationError(
                    f"Xodim {employee.hire_date.strftime('%d.%m.%Y')} sanasida ishga kirgan. "
                    f"Undan oldingi sanaga ({date.strftime('%d.%m.%Y')}) davomat kiritish mumkin emas."
                )

        # Duplicate tekshiruvi (faqat yangi yozuv uchun)
        if employee and date and not self.instance.pk:
            if Attendance.objects.filter(employee=employee, date=date).exists():
                raise forms.ValidationError(
                    f"Bu xodim uchun {date.strftime('%d.%m.%Y')} sanasida davomat allaqachon kiritilgan."
                )

        # Kasallik, ta'til, kelmadi holatlari uchun vaqt kerak emas
        statuses_no_time = [Attendance.Status.SICK, Attendance.Status.ON_LEAVE, Attendance.Status.ABSENT]

        # Keldi/Kechikdi bo'lsa, check_in bo'lishi kerak
        if status in [Attendance.Status.PRESENT, Attendance.Status.LATE]:
            if not check_in:
                raise forms.ValidationError("Kelish vaqtini kiriting.")

        # Xizmat safari - vaqtlar ixtiyoriy, lekin kiritilsa tekshiriladi
        # Kasallik/ta'til - vaqtlar avtomatik tozalanadi

        # Ketish vaqti kelishdan keyin bo'lishi kerak
        if check_in and check_out and check_out <= check_in:
            raise forms.ValidationError("Ketish vaqti kelishdan keyin bo'lishi kerak.")

        return cleaned_data


class BulkAttendanceForm(forms.Form):
    """Ommaviy davomat kiritish."""

    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'
        }),
        label="Sana"
    )
    department = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'
        }),
        label="Bo'lim"
    )

    def __init__(self, *args, **kwargs):
        from apps.departments.models import Department
        super().__init__(*args, **kwargs)
        departments = Department.objects.filter(is_active=True)
        choices = [('', 'Barcha bo\'limlar')]
        choices.extend([(d.id, d.name) for d in departments])
        self.fields['department'].choices = choices


class CheckInOutForm(forms.Form):
    """Tezkor kelish/ketish."""

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.eligible_for_operations(),
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'
        }),
        label="Xodim"
    )
    action = forms.ChoiceField(
        choices=[('check_in', 'Kelish'), ('check_out', 'Ketish')],
        widget=forms.RadioSelect(attrs={'class': 'mr-2'}),
        label="Amal"
    )
    time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'
        }),
        label="Vaqt (bo'sh qolsa hozirgi vaqt)"
    )

    def clean_employee(self):
        employee = self.cleaned_data.get('employee')
        if employee and not employee.has_approved_hiring_order:
            raise forms.ValidationError(
                f"Ishga olish buyrug'i tasdiqlanmagan."
            )
        return employee
