"""
Employee views - Xodimlar boshqaruvi.

HTMX bilan ishlaydi.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.db.models import Q
from django.contrib import messages

from .models import Employee, Position, Level, TenureBracket, MHTMHistory
from .forms import EmployeeForm, PositionForm


class EmployeeListView(LoginRequiredMixin, ListView):
    """Xodimlar ro'yxati."""
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 20

    def get_queryset(self):
        queryset = Employee.objects.filter(is_active=True).select_related(
            'user', 'department', 'position', 'level'
        )

        # Qidiruv
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(employee_code__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search)
            )

        # Bo'lim filtri
        department = self.request.GET.get('department', '')
        if department:
            queryset = queryset.filter(department_id=department)

        # Status filtri
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        # Daraja filtri
        level = self.request.GET.get('level', '')
        if level:
            queryset = queryset.filter(level_id=level)

        return queryset.order_by('employee_code')

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['employees/partials/employee_table.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = self.request.user.employee.department.get_descendants(include_self=True) if hasattr(self.request.user, 'employee') else []
        context['levels'] = Level.objects.filter(is_active=True)
        context['statuses'] = Employee.Status.choices
        context['total_count'] = Employee.objects.filter(is_active=True).count()
        return context


class EmployeeDetailView(LoginRequiredMixin, DetailView):
    """Xodim tafsilotlari."""
    model = Employee
    template_name = 'employees/employee_detail.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.object
        context['base_salary'] = employee.calculate_base_salary()
        context['mhtm'] = MHTMHistory.get_current()
        return context


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    """Yangi xodim yaratish."""
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employees:employee_list')

    def form_valid(self, form):
        messages.success(self.request, "Xodim muvaffaqiyatli yaratildi!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Yangi Xodim"
        context['button_text'] = "Yaratish"
        return context


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    """Xodim ma'lumotlarini tahrirlash."""
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'

    def get_success_url(self):
        return reverse_lazy('employees:employee_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Xodim ma'lumotlari yangilandi!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Tahrirlash: {self.object.full_name}"
        context['button_text'] = "Saqlash"
        return context


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    """Xodimni o'chirish (soft delete)."""
    model = Employee
    success_url = reverse_lazy('employees:employee_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(request, "Xodim o'chirildi!")

        if request.headers.get('HX-Request'):
            return HttpResponse(status=200, headers={'HX-Trigger': 'employeeDeleted'})
        return super().delete(request, *args, **kwargs)


# Position views
class PositionListView(LoginRequiredMixin, ListView):
    """Lavozimlar ro'yxati."""
    model = Position
    template_name = 'employees/position_list.html'
    context_object_name = 'positions'
    paginate_by = 20

    def get_queryset(self):
        return Position.objects.filter(is_active=True).select_related('department')

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['employees/partials/position_table.html']
        return [self.template_name]


class PositionCreateView(LoginRequiredMixin, CreateView):
    """Yangi lavozim yaratish."""
    model = Position
    form_class = PositionForm
    template_name = 'employees/position_form.html'
    success_url = reverse_lazy('employees:position_list')

    def form_valid(self, form):
        messages.success(self.request, "Lavozim yaratildi!")
        return super().form_valid(form)


class PositionUpdateView(LoginRequiredMixin, UpdateView):
    """Lavozimni tahrirlash."""
    model = Position
    form_class = PositionForm
    template_name = 'employees/position_form.html'
    success_url = reverse_lazy('employees:position_list')

    def form_valid(self, form):
        messages.success(self.request, "Lavozim yangilandi!")
        return super().form_valid(form)


class PositionDeleteView(LoginRequiredMixin, DeleteView):
    """Lavozimni o'chirish."""
    model = Position
    success_url = reverse_lazy('employees:position_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete()
        messages.success(request, "Lavozim o'chirildi!")

        if request.headers.get('HX-Request'):
            return HttpResponse(status=200, headers={'HX-Trigger': 'positionDeleted'})
        return super().delete(request, *args, **kwargs)


# Level views
class LevelListView(LoginRequiredMixin, ListView):
    """Darajalar ro'yxati."""
    model = Level
    template_name = 'employees/level_list.html'
    context_object_name = 'levels'

    def get_queryset(self):
        return Level.objects.filter(is_active=True).order_by('level')


# HTMX partials
def employee_salary_calculator(request, pk):
    """HTMX: Xodim ish haqini hisoblash."""
    employee = Employee.objects.get(pk=pk)
    mhtm = MHTMHistory.get_current()
    salary = employee.calculate_base_salary(mhtm)

    html = f'''
    <div class="bg-green-50 border border-green-200 rounded-lg p-4">
        <div class="text-sm text-green-600 mb-1">Bazaviy ish haqi</div>
        <div class="text-2xl font-bold text-green-700">{salary:,.0f} so'm</div>
        <div class="text-xs text-green-500 mt-2">
            {mhtm:,.0f} × {employee.position.base_coefficient} × {employee.level.coefficient} × {employee.tenure_coefficient}
        </div>
    </div>
    '''
    return HttpResponse(html)
