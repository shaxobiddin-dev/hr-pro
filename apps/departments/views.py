"""
Department views - Bo'limlar boshqaruvi.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.contrib import messages

from .models import Department
from .forms import DepartmentForm


class DepartmentListView(LoginRequiredMixin, ListView):
    """Bo'limlar ro'yxati."""
    model = Department
    template_name = 'departments/department_list.html'
    context_object_name = 'departments'

    def get_queryset(self):
        return Department.objects.filter(
            is_active=True,
            parent__isnull=True  # Faqat yuqori darajadagi bo'limlar
        ).prefetch_related('children')

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['departments/partials/department_tree.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = Department.objects.filter(is_active=True).count()
        return context


class DepartmentDetailView(LoginRequiredMixin, DetailView):
    """Bo'lim tafsilotlari."""
    model = Department
    template_name = 'departments/department_detail.html'
    context_object_name = 'department'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employees'] = self.object.employees.filter(is_active=True).select_related('user', 'position', 'level')[:10]
        context['positions'] = self.object.positions.filter(is_active=True)
        context['children'] = self.object.children.filter(is_active=True)
        return context


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    """Yangi bo'lim yaratish."""
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'
    success_url = reverse_lazy('departments:department_list')

    def form_valid(self, form):
        messages.success(self.request, "Bo'lim yaratildi!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Yangi Bo'lim"
        context['button_text'] = "Yaratish"
        return context


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    """Bo'limni tahrirlash."""
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'

    def get_success_url(self):
        return reverse_lazy('departments:department_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Bo'lim yangilandi!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Tahrirlash: {self.object.name}"
        context['button_text'] = "Saqlash"
        return context


class DepartmentDeleteView(LoginRequiredMixin, DeleteView):
    """Bo'limni o'chirish."""
    model = Department
    success_url = reverse_lazy('departments:department_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Xodimlar bor-yo'qligini tekshirish
        if self.object.employees.filter(is_active=True).exists():
            messages.error(request, "Bu bo'limda xodimlar bor. Avval xodimlarni boshqa bo'limga o'tkazing.")
            return HttpResponse(status=400)

        self.object.soft_delete()
        messages.success(request, "Bo'lim o'chirildi!")

        if request.headers.get('HX-Request'):
            return HttpResponse(status=200, headers={'HX-Trigger': 'departmentDeleted'})
        return super().delete(request, *args, **kwargs)
