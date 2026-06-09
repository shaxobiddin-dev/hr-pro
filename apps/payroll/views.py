"""
Payroll views.
"""

from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Sum, Count
from django.core.paginator import Paginator

from apps.employees.models import Employee, MHTMHistory
from .models import PayrollPeriod, Payroll, PayrollItem, SalaryComponent
from .forms import PayrollPeriodForm, PayrollForm, PayrollItemForm


@login_required
def period_list(request):
    """Ish haqi davrlari ro'yxati."""
    periods = PayrollPeriod.objects.annotate(
        employee_count=Count('payrolls'),
        total_gross=Sum('payrolls__gross_salary'),
        total_net=Sum('payrolls__net_salary')
    ).order_by('-start_date')

    # Filtrlash
    status = request.GET.get('status')
    if status:
        periods = periods.filter(status=status)

    # Pagination
    paginator = Paginator(periods, 12)
    page = request.GET.get('page', 1)
    periods = paginator.get_page(page)

    context = {
        'periods': periods,
        'status_choices': PayrollPeriod.Status.choices,
        'current_status': status,
    }
    return render(request, 'payroll/period_list.html', context)


@login_required
def period_detail(request, pk):
    """Ish haqi davri tafsiloti."""
    period = get_object_or_404(PayrollPeriod, pk=pk)
    payrolls = period.payrolls.select_related('employee__user', 'employee__position').order_by(
        'employee__user__last_name', 'employee__user__first_name'
    )

    # Statistika
    stats = payrolls.aggregate(
        total_gross=Sum('gross_salary'),
        total_net=Sum('net_salary'),
        total_deductions=Sum('total_deductions'),
        total_jshdt=Sum('jshdt_amount'),
        total_inps=Sum('inps_amount')
    )

    context = {
        'period': period,
        'payrolls': payrolls,
        'stats': stats,
    }
    return render(request, 'payroll/period_detail.html', context)


@login_required
def period_create(request):
    """Yangi ish haqi davri yaratish."""
    if request.method == 'POST':
        form = PayrollPeriodForm(request.POST)
        if form.is_valid():
            period = form.save()
            messages.success(request, f"'{period.name}' davri yaratildi.")
            return redirect('payroll:period_detail', pk=period.pk)
    else:
        form = PayrollPeriodForm()

    context = {'form': form}
    return render(request, 'payroll/period_form.html', context)


@login_required
def period_update(request, pk):
    """Ish haqi davrini tahrirlash."""
    period = get_object_or_404(PayrollPeriod, pk=pk)

    if period.status not in ['draft', 'processing']:
        messages.error(request, "Tasdiqlangan yoki to'langan davrni o'zgartirish mumkin emas.")
        return redirect('payroll:period_detail', pk=pk)

    if request.method == 'POST':
        form = PayrollPeriodForm(request.POST, instance=period)
        if form.is_valid():
            form.save()
            messages.success(request, "Davr yangilandi.")
            return redirect('payroll:period_detail', pk=pk)
    else:
        form = PayrollPeriodForm(instance=period)

    context = {'form': form, 'period': period}
    return render(request, 'payroll/period_form.html', context)


@login_required
def period_delete(request, pk):
    """Ish haqi davrini o'chirish."""
    period = get_object_or_404(PayrollPeriod, pk=pk)

    if period.status != 'draft':
        messages.error(request, "Faqat qoralama holatidagi davrni o'chirish mumkin.")
        return redirect('payroll:period_detail', pk=pk)

    if request.method == 'POST':
        period.delete()
        messages.success(request, f"'{period.name}' davri o'chirildi.")
        return redirect('payroll:period_list')

    context = {'period': period}
    return render(request, 'payroll/period_confirm_delete.html', context)


@login_required
def generate_payrolls(request, pk):
    """Davr uchun barcha xodimlar ish haqini yaratish."""
    period = get_object_or_404(PayrollPeriod, pk=pk)

    if period.status != 'draft':
        messages.error(request, "Faqat qoralama holatidagi davr uchun ish haqi yaratish mumkin.")
        return redirect('payroll:period_detail', pk=pk)

    if request.method == 'POST':
        # Faol xodimlar
        employees = Employee.objects.filter(is_active=True, status='working')

        created_count = 0
        for employee in employees:
            payroll, created = Payroll.objects.get_or_create(
                period=period,
                employee=employee,
                defaults={'work_days': period.work_days}
            )
            if created:
                created_count += 1

        period.status = PayrollPeriod.Status.PROCESSING
        period.save()

        messages.success(request, f"{created_count} ta xodim uchun ish haqi yaratildi.")
        return redirect('payroll:period_detail', pk=pk)

    # Mavjud ish haqlari va xodimlar soni
    existing_count = period.payrolls.count()
    employee_count = Employee.objects.filter(is_active=True, status='working').count()

    context = {
        'period': period,
        'existing_count': existing_count,
        'employee_count': employee_count,
        'new_count': employee_count - existing_count
    }
    return render(request, 'payroll/generate_confirm.html', context)


@login_required
def calculate_all(request, pk):
    """Davrdagi barcha ish haqlarni hisoblash."""
    period = get_object_or_404(PayrollPeriod, pk=pk)

    if period.status not in ['draft', 'processing']:
        messages.error(request, "Faqat qoralama yoki hisoblanmoqda holatidagi davr uchun hisoblash mumkin.")
        return redirect('payroll:period_detail', pk=pk)

    if request.method == 'POST':
        payrolls = period.payrolls.all()
        count = 0
        for payroll in payrolls:
            payroll.calculate()
            count += 1

        messages.success(request, f"{count} ta ish haqi hisoblandi.")
        return redirect('payroll:period_detail', pk=pk)

    context = {'period': period, 'payroll_count': period.payrolls.count()}
    return render(request, 'payroll/calculate_confirm.html', context)


@login_required
def confirm_period(request, pk):
    """Davrni tasdiqlash."""
    period = get_object_or_404(PayrollPeriod, pk=pk)

    if period.status != 'processing':
        messages.error(request, "Faqat hisoblanmoqda holatidagi davrni tasdiqlash mumkin.")
        return redirect('payroll:period_detail', pk=pk)

    # Barcha ish haqlar hisoblangan bo'lishi kerak
    uncalculated = period.payrolls.filter(status='draft').count()
    if uncalculated > 0:
        messages.error(request, f"{uncalculated} ta ish haqi hali hisoblanmagan.")
        return redirect('payroll:period_detail', pk=pk)

    if request.method == 'POST':
        period.status = PayrollPeriod.Status.CONFIRMED
        period.save()

        # Barcha ish haqlarni ham tasdiqlash
        period.payrolls.filter(status='calculated').update(status='confirmed')

        messages.success(request, "Davr tasdiqlandi.")
        return redirect('payroll:period_detail', pk=pk)

    context = {'period': period}
    return render(request, 'payroll/confirm_period.html', context)


# Payroll (individual) views

@login_required
def payroll_detail(request, pk):
    """Xodim ish haqi tafsiloti."""
    payroll = get_object_or_404(
        Payroll.objects.select_related('employee__user', 'employee__position', 'period'),
        pk=pk
    )
    items = payroll.items.select_related('component').order_by('component__component_type', 'component__name')

    # Qo'shimchalar va ushlanmalar
    earnings = items.filter(component__component_type='earning')
    deductions = items.filter(component__component_type='deduction')

    context = {
        'payroll': payroll,
        'items': items,
        'earnings': earnings,
        'deductions': deductions,
    }
    return render(request, 'payroll/payroll_detail.html', context)


@login_required
def payroll_update(request, pk):
    """Xodim ish haqi tahrirlash."""
    payroll = get_object_or_404(Payroll, pk=pk)

    if payroll.status not in ['draft', 'calculated']:
        messages.error(request, "Tasdiqlangan yoki to'langan ish haqini o'zgartirish mumkin emas.")
        return redirect('payroll:payroll_detail', pk=pk)

    if request.method == 'POST':
        form = PayrollForm(request.POST, instance=payroll)
        if form.is_valid():
            form.save()
            messages.success(request, "Ish haqi ma'lumotlari yangilandi.")
            return redirect('payroll:payroll_detail', pk=pk)
    else:
        form = PayrollForm(instance=payroll)

    context = {'form': form, 'payroll': payroll}
    return render(request, 'payroll/payroll_form.html', context)


@login_required
def payroll_calculate(request, pk):
    """Bitta ish haqini hisoblash."""
    payroll = get_object_or_404(Payroll, pk=pk)

    if payroll.status not in ['draft', 'calculated']:
        messages.error(request, "Tasdiqlangan yoki to'langan ish haqini qayta hisoblash mumkin emas.")
        return redirect('payroll:payroll_detail', pk=pk)

    payroll.calculate()
    messages.success(request, "Ish haqi hisoblandi.")
    return redirect('payroll:payroll_detail', pk=pk)


@login_required
def payroll_add_item(request, pk):
    """Ish haqiga element qo'shish."""
    payroll = get_object_or_404(Payroll, pk=pk)

    if payroll.status not in ['draft', 'calculated']:
        messages.error(request, "Tasdiqlangan ish haqiga element qo'shish mumkin emas.")
        return redirect('payroll:payroll_detail', pk=pk)

    if request.method == 'POST':
        form = PayrollItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.payroll = payroll
            item.save()
            messages.success(request, "Element qo'shildi.")
            return redirect('payroll:payroll_detail', pk=pk)
    else:
        form = PayrollItemForm()

    context = {'form': form, 'payroll': payroll}
    return render(request, 'payroll/item_form.html', context)


@login_required
def payroll_delete_item(request, pk, item_pk):
    """Ish haqi elementini o'chirish."""
    payroll = get_object_or_404(Payroll, pk=pk)
    item = get_object_or_404(PayrollItem, pk=item_pk, payroll=payroll)

    if payroll.status not in ['draft', 'calculated']:
        messages.error(request, "Tasdiqlangan ish haqidan element o'chirish mumkin emas.")
        return redirect('payroll:payroll_detail', pk=pk)

    if request.method == 'POST':
        item.delete()
        messages.success(request, "Element o'chirildi.")
        return redirect('payroll:payroll_detail', pk=pk)

    context = {'payroll': payroll, 'item': item}
    return render(request, 'payroll/item_confirm_delete.html', context)


# Payslip views

@login_required
def payslip(request, pk):
    """Ish haqi varaqasi (payslip)."""
    payroll = get_object_or_404(
        Payroll.objects.select_related(
            'employee__user', 'employee__position', 'employee__department',
            'employee__level', 'period'
        ),
        pk=pk
    )
    items = payroll.items.select_related('component').order_by('component__component_type', 'component__name')

    earnings = items.filter(component__component_type='earning')
    deductions = items.filter(component__component_type='deduction')

    # MHTM
    mhtm = MHTMHistory.get_current()

    context = {
        'payroll': payroll,
        'earnings': earnings,
        'deductions': deductions,
        'mhtm': mhtm,
    }
    return render(request, 'payroll/payslip.html', context)


# Component views

@login_required
def component_list(request):
    """Ish haqi komponentlari ro'yxati."""
    components = SalaryComponent.objects.all().order_by('component_type', 'name')

    context = {'components': components}
    return render(request, 'payroll/component_list.html', context)
