"""
Core mixins for views.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


class HRProLoginRequiredMixin(LoginRequiredMixin):
    """
    Login required mixin with custom redirect.
    """
    login_url = '/accounts/login/'
    redirect_field_name = 'next'


class SuccessMessageMixin:
    """
    Mixin to add success message after form submission.
    """
    success_message = ""

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            messages.success(self.request, self.success_message)
        return response


class HTMXMixin:
    """
    Mixin for HTMX partial responses.

    Usage:
        class MyView(HTMXMixin, TemplateView):
            template_name = 'full_page.html'
            htmx_template_name = '_partial.html'
    """
    htmx_template_name = None

    def get_template_names(self):
        if self.request.headers.get('HX-Request') and self.htmx_template_name:
            return [self.htmx_template_name]
        return super().get_template_names()


class AuditMixin:
    """
    Mixin to track who created/updated records.

    Requires model to have:
        - created_by (ForeignKey to User)
        - updated_by (ForeignKey to User)
    """

    def form_valid(self, form):
        if not form.instance.pk:
            # Creating new record
            form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ActiveEmployeeRequiredMixin:
    """
    Faqat faol xodimlar uchun operatsiyalarni ruxsat beruvchi mixin.

    Tekshiruvlar:
    1. Foydalanuvchida employee profili bormi?
    2. Employee statusi ACTIVE mi?
    3. Tasdiqlangan ishga olish buyrug'i bormi?

    Agar shartlar bajarilmasa - xato xabari ko'rsatiladi.

    Usage:
        class AttendanceCreateView(ActiveEmployeeRequiredMixin, CreateView):
            ...
    """
    inactive_employee_message = "Sizning profilingiz faol emas. HR bo'limiga murojaat qiling."
    no_hiring_order_message = "Ishga olish buyrug'i tasdiqlanmagan. HR bo'limiga murojaat qiling."
    no_employee_profile_message = "Xodim profili topilmadi."

    def dispatch(self, request, *args, **kwargs):
        # Login tekshiruvi
        if not request.user.is_authenticated:
            return redirect('account_login')

        # Superuser/staff uchun cheklov yo'q
        if request.user.is_superuser or request.user.is_staff:
            return super().dispatch(request, *args, **kwargs)

        # Employee profili bormi?
        if not hasattr(request.user, 'employee'):
            messages.error(request, self.no_employee_profile_message)
            return redirect('dashboard')

        employee = request.user.employee

        # Status ACTIVE mi?
        if employee.status != 'active':
            messages.error(request, self.inactive_employee_message)
            return redirect('dashboard')

        # Tasdiqlangan buyruq bormi?
        if not employee.has_approved_hiring_order:
            messages.error(request, self.no_hiring_order_message)
            return redirect('dashboard')

        return super().dispatch(request, *args, **kwargs)


class EmployeeOperationMixin:
    """
    Xodim ustida operatsiya bajarilganda tekshiruvlar.

    Bu mixin boshqa xodim ustida operatsiya qilganda ishlatiladi.
    Masalan: HR xodim davomatini kiritmoqda.

    Usage:
        class AttendanceCreateView(EmployeeOperationMixin, CreateView):
            def get_target_employee(self):
                return Employee.objects.get(pk=self.kwargs['employee_pk'])
    """
    target_employee_inactive_message = "Bu xodim faol emas."
    target_no_hiring_order_message = "Bu xodim uchun ishga olish buyrug'i tasdiqlanmagan."

    def get_target_employee(self):
        """Override this method to return target employee."""
        raise NotImplementedError("get_target_employee() must be implemented")

    def check_target_employee(self):
        """Target xodimni tekshirish."""
        employee = self.get_target_employee()

        if employee.status != 'active':
            messages.error(self.request, self.target_employee_inactive_message)
            return False

        if not employee.has_approved_hiring_order:
            messages.error(self.request, self.target_no_hiring_order_message)
            return False

        return True

    def dispatch(self, request, *args, **kwargs):
        # Avval parent dispatch
        response = super().dispatch(request, *args, **kwargs)

        # Agar GET so'rovi bo'lsa - tekshiruvni o'tkazish
        if request.method == 'GET':
            if not self.check_target_employee():
                return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

        return response

    def form_valid(self, form):
        """POST so'rovida ham tekshirish."""
        if not self.check_target_employee():
            return redirect(self.request.META.get('HTTP_REFERER', 'dashboard'))
        return super().form_valid(form)
