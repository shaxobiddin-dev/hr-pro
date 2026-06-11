"""
Leave views - Ta'til moduli.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.db import IntegrityError
from django.utils import timezone
from decimal import Decimal

from apps.employees.models import Employee
from .models import LeaveType, LeaveBalance, LeaveRequest
from .forms import LeaveRequestForm, LeaveApprovalForm


@login_required
def leave_dashboard(request):
    """Ta'til dashboard - umumiy ko'rinish."""
    today = timezone.now().date()
    year = today.year

    # Joriy xodimning balanslarini olish
    employee = getattr(request.user, 'employee', None)
    my_balances = []
    my_requests = []
    is_admin = request.user.is_staff

    if employee:
        my_balances = LeaveBalance.objects.filter(
            employee=employee,
            year=year
        ).select_related('leave_type')

        my_requests = LeaveRequest.objects.filter(
            employee=employee
        ).order_by('-created_at')[:5]
    elif is_admin:
        # Admin uchun barcha so'rovlarni ko'rsatish
        my_requests = LeaveRequest.objects.all().order_by('-created_at')[:5]

    # Hozirda ta'tilda bo'lganlar (faqat faol xodimlar)
    on_leave = LeaveRequest.objects.filter(
        status='approved',
        start_date__lte=today,
        end_date__gte=today,
        employee__is_active=True  # O'chirilgan xodimlar ko'rinmaydi
    ).select_related('employee__user', 'leave_type')

    # Kutilayotgan so'rovlar (rahbar yoki admin uchun) - faqat faol xodimlar
    pending_requests = []
    if is_admin:
        # Admin barcha kutilayotgan so'rovlarni ko'radi
        pending_requests = LeaveRequest.objects.filter(
            status='pending',
            employee__is_active=True
        ).select_related('employee__user', 'leave_type')
    elif employee and employee.subordinates.filter(is_active=True).exists():
        subordinate_ids = employee.subordinates.filter(is_active=True).values_list('id', flat=True)
        pending_requests = LeaveRequest.objects.filter(
            employee_id__in=subordinate_ids,
            status='pending',
            employee__is_active=True
        ).select_related('employee__user', 'leave_type')

    # Statistika (faqat faol xodimlar)
    stats = {
        'on_leave_count': on_leave.count(),
        'pending_count': LeaveRequest.objects.filter(
            status='pending',
            employee__is_active=True
        ).count(),
        'approved_this_month': LeaveRequest.objects.filter(
            status='approved',
            start_date__year=today.year,
            start_date__month=today.month,
            employee__is_active=True
        ).count(),
    }

    context = {
        'my_balances': my_balances,
        'my_requests': my_requests,
        'on_leave': on_leave,
        'pending_requests': pending_requests,
        'stats': stats,
        'today': today,
    }
    return render(request, 'leave/dashboard.html', context)


@login_required
def leave_request_list(request):
    """Ta'til so'rovlari ro'yxati."""
    employee = getattr(request.user, 'employee', None)

    # Admin barcha so'rovlarni ko'radi, xodim faqat o'zini
    if request.user.is_staff:
        # Admin: barcha so'rovlar (arxivlangan ham filter orqali)
        requests = LeaveRequest.objects.all()
        # Arxivlangan xodimlarni filtrlash imkoniyati
        show_archived = request.GET.get('show_archived')
        if not show_archived:
            requests = requests.filter(employee__is_active=True)
    elif employee:
        # O'zining va qo'l ostidagilarning so'rovlari (faqat faol xodimlar)
        subordinate_ids = list(employee.subordinates.filter(is_active=True).values_list('id', flat=True))
        subordinate_ids.append(employee.id)
        requests = LeaveRequest.objects.filter(
            employee_id__in=subordinate_ids,
            employee__is_active=True
        )
    else:
        requests = LeaveRequest.objects.none()

    requests = requests.select_related('employee__user', 'leave_type', 'approved_by__user')

    # Filtrlash
    status = request.GET.get('status')
    if status:
        requests = requests.filter(status=status)

    leave_type = request.GET.get('leave_type')
    if leave_type:
        requests = requests.filter(leave_type_id=leave_type)

    # Qidiruv
    search = request.GET.get('search', '')
    if search:
        requests = requests.filter(
            Q(employee__user__first_name__icontains=search) |
            Q(employee__user__last_name__icontains=search) |
            Q(employee__employee_code__icontains=search)
        )

    requests = requests.order_by('-created_at')

    # Pagination
    paginator = Paginator(requests, 20)
    page = request.GET.get('page', 1)
    requests = paginator.get_page(page)

    context = {
        'requests': requests,
        'status_choices': LeaveRequest.Status.choices,
        'leave_types': LeaveType.objects.filter(is_active=True),
        'current_status': status,
        'current_leave_type': leave_type,
        'search': search,
    }
    return render(request, 'leave/request_list.html', context)


@login_required
def leave_request_create(request):
    """Yangi ta'til so'rovi yaratish."""
    employee = getattr(request.user, 'employee', None)
    is_admin = request.user.is_staff

    # Oddiy foydalanuvchi va xodim profili yo'q
    if not employee and not is_admin:
        messages.error(request, "Sizning xodim profilingiz topilmadi.")
        return redirect('leave:dashboard')

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES, employee=employee, is_admin=is_admin)
        if form.is_valid():
            try:
                leave_request = form.save()
                messages.success(request, "Ta'til so'rovi yaratildi.")
                return redirect('leave:request_detail', pk=leave_request.pk)
            except IntegrityError as e:
                messages.error(request, f"Xatolik: {str(e)}")
    else:
        form = LeaveRequestForm(employee=employee, is_admin=is_admin)

    # Balanslarni ko'rsatish
    year = timezone.now().year
    balances = []
    if employee:
        balances = LeaveBalance.objects.filter(
            employee=employee,
            year=year
        ).select_related('leave_type')

    context = {
        'form': form,
        'balances': balances,
        'is_admin': is_admin,
    }
    return render(request, 'leave/request_form.html', context)


@login_required
def leave_request_detail(request, pk):
    """Ta'til so'rovi tafsiloti."""
    leave_request = get_object_or_404(
        LeaveRequest.objects.select_related(
            'employee__user', 'employee__department', 'employee__position',
            'leave_type', 'approved_by__user'
        ),
        pk=pk
    )

    # Faqat o'zi, rahbari yoki admin ko'ra oladi
    employee = getattr(request.user, 'employee', None)
    can_view = (
        request.user.is_staff or
        (employee and leave_request.employee == employee) or
        (employee and leave_request.employee.manager == employee)
    )

    if not can_view:
        messages.error(request, "Bu so'rovni ko'rish huquqingiz yo'q.")
        return redirect('leave:request_list')

    # Tasdiqlash huquqi
    can_approve = (
        request.user.is_staff or
        (employee and leave_request.employee.manager == employee)
    ) and leave_request.status == 'pending'

    context = {
        'leave_request': leave_request,
        'can_approve': can_approve,
    }
    return render(request, 'leave/request_detail.html', context)


@login_required
def leave_request_submit(request, pk):
    """Ta'til so'rovini yuborish."""
    leave_request = get_object_or_404(LeaveRequest, pk=pk)
    employee = getattr(request.user, 'employee', None)

    # O'zi yoki admin yuborishi mumkin
    can_submit = request.user.is_staff or (employee and leave_request.employee == employee)
    if not can_submit:
        messages.error(request, "Bu so'rovni yuborish huquqingiz yo'q.")
        return redirect('leave:request_detail', pk=pk)

    if leave_request.submit():
        messages.success(request, "So'rov yuborildi. Rahbar tasdiqlashini kuting.")
    else:
        messages.error(request, "So'rovni yuborib bo'lmadi.")

    return redirect('leave:request_detail', pk=pk)


@login_required
def leave_request_approve(request, pk):
    """Ta'til so'rovini tasdiqlash."""
    leave_request = get_object_or_404(LeaveRequest, pk=pk)
    employee = getattr(request.user, 'employee', None)

    # Tasdiqlash huquqi
    can_approve = (
        request.user.is_staff or
        (employee and leave_request.employee.manager == employee)
    )

    if not can_approve:
        messages.error(request, "Tasdiqlash huquqingiz yo'q.")
        return redirect('leave:request_detail', pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            approver = employee if employee else None
            if leave_request.approve(approver):
                messages.success(request, "Ta'til so'rovi tasdiqlandi.")
            else:
                messages.error(request, "Tasdiqlash muvaffaqiyatsiz.")

        elif action == 'reject':
            reason = request.POST.get('rejection_reason', '')
            rejector = employee if employee else None
            if leave_request.reject(rejector, reason):
                messages.success(request, "Ta'til so'rovi rad etildi.")
            else:
                messages.error(request, "Rad etish muvaffaqiyatsiz.")

    return redirect('leave:request_detail', pk=pk)


@login_required
def leave_request_cancel(request, pk):
    """Ta'til so'rovini bekor qilish."""
    leave_request = get_object_or_404(LeaveRequest, pk=pk)
    employee = getattr(request.user, 'employee', None)

    # O'zi yoki admin bekor qilishi mumkin
    can_cancel = request.user.is_staff or (employee and leave_request.employee == employee)
    if not can_cancel:
        messages.error(request, "Bu so'rovni bekor qilish huquqingiz yo'q.")
        return redirect('leave:request_detail', pk=pk)

    if request.method == 'POST':
        if leave_request.cancel():
            messages.success(request, "So'rov bekor qilindi.")
        else:
            messages.error(request, "So'rovni bekor qilib bo'lmadi.")

    return redirect('leave:request_list')


@login_required
def leave_balance_list(request):
    """Ta'til balanslari ro'yxati."""
    year = request.GET.get('year', timezone.now().year)

    balances = LeaveBalance.objects.filter(
        year=year,
        employee__is_active=True  # O'chirilgan xodimlar ko'rinmaydi
    ).select_related('employee__user', 'employee__department', 'leave_type')

    # Filtrlash
    department = request.GET.get('department')
    if department:
        balances = balances.filter(employee__department_id=department)

    leave_type = request.GET.get('leave_type')
    if leave_type:
        balances = balances.filter(leave_type_id=leave_type)

    # Qidiruv
    search = request.GET.get('search', '')
    if search:
        balances = balances.filter(
            Q(employee__user__first_name__icontains=search) |
            Q(employee__user__last_name__icontains=search) |
            Q(employee__employee_code__icontains=search)
        )

    balances = balances.order_by('employee__user__last_name', 'leave_type')

    # Pagination
    paginator = Paginator(balances, 30)
    page = request.GET.get('page', 1)
    balances = paginator.get_page(page)

    # Yillar
    years = list(range(timezone.now().year - 2, timezone.now().year + 2))

    context = {
        'balances': balances,
        'years': years,
        'current_year': int(year),
        'leave_types': LeaveType.objects.filter(is_active=True),
        'current_leave_type': leave_type,
        'search': search,
    }
    return render(request, 'leave/balance_list.html', context)


@login_required
def leave_calendar(request):
    """Ta'til kalendari."""
    today = timezone.now().date()

    # Joriy oyning ta'tillari
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    # Tasdiqlangan ta'tillar (faqat faol xodimlar)
    leaves = LeaveRequest.objects.filter(
        status='approved',
        start_date__year=year,
        start_date__month=month,
        employee__is_active=True  # O'chirilgan xodimlar ko'rinmaydi
    ).select_related('employee__user', 'leave_type').order_by('start_date')

    # Oylar va yillar
    months = [
        (1, 'Yanvar'), (2, 'Fevral'), (3, 'Mart'), (4, 'Aprel'),
        (5, 'May'), (6, 'Iyun'), (7, 'Iyul'), (8, 'Avgust'),
        (9, 'Sentabr'), (10, 'Oktabr'), (11, 'Noyabr'), (12, 'Dekabr')
    ]
    years_list = list(range(today.year - 1, today.year + 2))

    context = {
        'leaves': leaves,
        'current_month': month,
        'current_year': year,
        'months': months,
        'years': years_list,
        'today': today,
    }
    return render(request, 'leave/calendar.html', context)


@login_required
def leave_type_list(request):
    """Ta'til turlari ro'yxati."""
    leave_types = LeaveType.objects.filter(is_active=True).order_by('name')

    context = {
        'leave_types': leave_types,
    }
    return render(request, 'leave/type_list.html', context)
