"""
Attendance views - Davomat moduli.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.db import IntegrityError
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
import calendar

from apps.employees.models import Employee
from apps.departments.models import Department
from .models import Attendance, MonthlyTimesheet
from .forms import AttendanceForm, BulkAttendanceForm, CheckInOutForm


@login_required
def attendance_dashboard(request):
    """Davomat dashboard."""
    today = timezone.now().date()

    # Bugungi statistika - FAQAT faol xodimlar
    today_stats = {
        'total_employees': Employee.objects.eligible_for_operations().count(),
        'present': Attendance.objects.filter(date=today, status__in=['present', 'late'], employee__is_active=True).count(),
        'absent': Attendance.objects.filter(date=today, status='absent', employee__is_active=True).count(),
        'late': Attendance.objects.filter(date=today, status='late', employee__is_active=True).count(),
        'on_leave': Attendance.objects.filter(date=today, status='on_leave', employee__is_active=True).count(),
    }
    today_stats['not_recorded'] = today_stats['total_employees'] - Attendance.objects.filter(date=today, employee__is_active=True).count()

    # Bugungi davomatlar - FAQAT faol xodimlar
    today_attendances = Attendance.objects.filter(
        date=today,
        employee__is_active=True
    ).select_related('employee__user', 'employee__department').order_by('-check_in')[:10]

    # Kechikkanlar - FAQAT faol xodimlar
    late_today = Attendance.objects.filter(
        date=today,
        status='late',
        employee__is_active=True
    ).select_related('employee__user')

    # Shu oylik statistika - FAQAT faol xodimlar
    month_start = today.replace(day=1)
    month_attendances = Attendance.objects.filter(
        date__gte=month_start,
        date__lte=today,
        employee__is_active=True
    )
    month_stats = {
        'work_days': (today - month_start).days + 1,
        'total_present': month_attendances.filter(status__in=['present', 'late']).count(),
        'total_late': month_attendances.filter(status='late').count(),
    }

    context = {
        'today': today,
        'today_stats': today_stats,
        'today_attendances': today_attendances,
        'late_today': late_today,
        'month_stats': month_stats,
    }
    return render(request, 'attendance/dashboard.html', context)


@login_required
def attendance_list(request):
    """Davomatlar ro'yxati."""
    # Filtrlar
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    department_id = request.GET.get('department')
    status = request.GET.get('status')
    search = request.GET.get('search', '')

    # Faqat faol xodimlarning davomatlari
    attendances = Attendance.objects.filter(
        date=selected_date,
        employee__is_active=True  # O'chirilgan xodimlarni ko'rsatmaslik
    ).select_related('employee__user', 'employee__department')

    if department_id:
        attendances = attendances.filter(employee__department_id=department_id)

    if status:
        attendances = attendances.filter(status=status)

    if search:
        attendances = attendances.filter(
            Q(employee__user__first_name__icontains=search) |
            Q(employee__user__last_name__icontains=search) |
            Q(employee__employee_code__icontains=search)
        )

    attendances = attendances.order_by('employee__user__last_name')

    # Davomati yo'q xodimlar
    recorded_ids = attendances.values_list('employee_id', flat=True)
    not_recorded = Employee.objects.filter(
        is_active=True, status='active'
    ).exclude(id__in=recorded_ids).select_related('user', 'department')

    if department_id:
        not_recorded = not_recorded.filter(department_id=department_id)

    context = {
        'attendances': attendances,
        'not_recorded': not_recorded,
        'selected_date': selected_date,
        'departments': Department.objects.filter(is_active=True),
        'status_choices': Attendance.Status.choices,
        'current_department': department_id,
        'current_status': status,
        'search': search,
    }
    return render(request, 'attendance/attendance_list.html', context)


@login_required
def attendance_create(request):
    """Yangi davomat kiritish."""
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            try:
                attendance = form.save(commit=False)
                attendance.recorded_by = request.user
                attendance.save()
                messages.success(request, "Davomat kiritildi.")
                # To'g'ri sanaga qaytarish
                return redirect(f"{reverse('attendance:list')}?date={attendance.date.strftime('%Y-%m-%d')}")
            except IntegrityError:
                messages.error(request, "Bu xodim uchun shu sanada davomat allaqachon mavjud.")
    else:
        # URL'dan xodim va sana olish
        initial = {'date': request.GET.get('date', timezone.now().date())}
        employee_id = request.GET.get('employee')
        if employee_id:
            initial['employee'] = employee_id
        form = AttendanceForm(initial=initial)

    context = {
        'form': form,
        'title': "Yangi davomat",
    }
    return render(request, 'attendance/attendance_form.html', context)


@login_required
def attendance_update(request, pk):
    """Davomatni tahrirlash."""
    attendance = get_object_or_404(Attendance, pk=pk)
    original_date = attendance.date  # Asl sanani saqlash

    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=attendance, is_edit=True)
        if form.is_valid():
            # disabled fieldlarni saqlash
            att = form.save(commit=False)
            att.employee = attendance.employee
            att.date = original_date  # Asl sanani saqlash
            att.save()
            messages.success(request, "Davomat yangilandi.")
            # To'g'ri sanaga qaytarish
            return redirect(f"{reverse('attendance:list')}?date={original_date.strftime('%Y-%m-%d')}")
    else:
        form = AttendanceForm(instance=attendance, is_edit=True)

    context = {
        'form': form,
        'attendance': attendance,
        'title': "Davomatni tahrirlash",
    }
    return render(request, 'attendance/attendance_form.html', context)


@login_required
def attendance_delete(request, pk):
    """Davomatni o'chirish."""
    attendance = get_object_or_404(Attendance, pk=pk)

    if request.method == 'POST':
        attendance.delete()
        messages.success(request, "Davomat o'chirildi.")
        return redirect('attendance:list')

    return redirect('attendance:list')


@login_required
def quick_check_in(request):
    """Tezkor kelish/ketish."""
    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        action = request.POST.get('action')
        time_str = request.POST.get('time')

        employee = get_object_or_404(Employee, pk=employee_id)
        today = timezone.now().date()

        # Vaqtni aniqlash
        if time_str:
            current_time = datetime.strptime(time_str, '%H:%M').time()
        else:
            current_time = timezone.now().time()

        # Bugungi davomat
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'recorded_by': request.user}
        )

        if action == 'check_in':
            attendance.check_in = current_time
            attendance.status = Attendance.Status.PRESENT
            messages.success(request, f"{employee.full_name} keldi: {current_time.strftime('%H:%M')}")
        elif action == 'check_out':
            attendance.check_out = current_time
            messages.success(request, f"{employee.full_name} ketdi: {current_time.strftime('%H:%M')}")

        attendance.recorded_by = request.user
        attendance.save()

        return redirect('attendance:dashboard')

    form = CheckInOutForm()
    context = {
        'form': form,
    }
    return render(request, 'attendance/quick_check.html', context)


@login_required
def bulk_attendance(request):
    """Ommaviy davomat kiritish."""
    if request.method == 'POST':
        date_str = request.POST.get('date')
        department_id = request.POST.get('department')

        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "Noto'g'ri sana.")
            return redirect('attendance:bulk')

        # Xodimlarni olish
        employees = Employee.objects.eligible_for_operations()
        if department_id:
            employees = employees.filter(department_id=department_id)

        created_count = 0
        for emp in employees:
            emp_status = request.POST.get(f'status_{emp.id}')
            emp_check_in = request.POST.get(f'check_in_{emp.id}')
            emp_check_out = request.POST.get(f'check_out_{emp.id}')

            if emp_status:
                # String ni time ga aylantirish
                check_in_time = None
                check_out_time = None
                if emp_check_in:
                    try:
                        check_in_time = datetime.strptime(emp_check_in, '%H:%M').time()
                    except ValueError:
                        pass
                if emp_check_out:
                    try:
                        check_out_time = datetime.strptime(emp_check_out, '%H:%M').time()
                    except ValueError:
                        pass

                attendance, created = Attendance.objects.update_or_create(
                    employee=emp,
                    date=selected_date,
                    defaults={
                        'status': emp_status,
                        'check_in': check_in_time,
                        'check_out': check_out_time,
                        'recorded_by': request.user,
                    }
                )
                if created:
                    created_count += 1

        messages.success(request, f"{created_count} ta davomat kiritildi.")
        return redirect('attendance:list', date=date_str)

    # GET - forma
    form = BulkAttendanceForm(initial={'date': timezone.now().date()})
    date_str = request.GET.get('date')
    department_id = request.GET.get('department')

    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    employees = Employee.objects.filter(
        is_active=True, status='active'
    ).select_related('user', 'department')

    if department_id:
        employees = employees.filter(department_id=department_id)

    # Mavjud davomatlar
    existing = {
        a.employee_id: a for a in Attendance.objects.filter(
            employee__in=employees,
            date=selected_date
        )
    }

    employee_data = []
    for emp in employees:
        att = existing.get(emp.id)
        employee_data.append({
            'employee': emp,
            'attendance': att,
        })

    context = {
        'form': form,
        'employees': employee_data,
        'selected_date': selected_date,
        'status_choices': Attendance.Status.choices,
    }
    return render(request, 'attendance/bulk_attendance.html', context)


@login_required
def timesheet_list(request):
    """Oylik tabellar."""
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))

    timesheets = MonthlyTimesheet.objects.filter(
        year=year,
        month=month,
        employee__is_active=True  # Faqat faol xodimlar
    ).select_related('employee__user', 'employee__department')

    # Yillar va oylar
    years = list(range(timezone.now().year - 2, timezone.now().year + 1))
    months = [
        (1, 'Yanvar'), (2, 'Fevral'), (3, 'Mart'), (4, 'Aprel'),
        (5, 'May'), (6, 'Iyun'), (7, 'Iyul'), (8, 'Avgust'),
        (9, 'Sentabr'), (10, 'Oktabr'), (11, 'Noyabr'), (12, 'Dekabr')
    ]

    context = {
        'timesheets': timesheets,
        'current_year': year,
        'current_month': month,
        'years': years,
        'months': months,
    }
    return render(request, 'attendance/timesheet_list.html', context)


@login_required
def generate_timesheets(request):
    """Oylik tabellarni yaratish."""
    if request.method == 'POST':
        year = int(request.POST.get('year', timezone.now().year))
        month = int(request.POST.get('month', timezone.now().month))

        # Oydagi ish kunlarini hisoblash
        _, days_in_month = calendar.monthrange(year, month)
        work_days = 0
        for day in range(1, days_in_month + 1):
            date = datetime(year, month, day).date()
            # Yakshanba emas
            if date.weekday() != 6:
                work_days += 1

        # Har bir xodim uchun tabel (faqat faol xodimlar)
        employees = Employee.objects.eligible_for_operations()
        created_count = 0

        for emp in employees:
            timesheet, created = MonthlyTimesheet.objects.get_or_create(
                employee=emp,
                year=year,
                month=month,
                defaults={'work_days': work_days}
            )
            timesheet.work_days = work_days
            timesheet.calculate_from_attendances()
            if created:
                created_count += 1

        messages.success(request, f"{created_count} ta tabel yaratildi, {employees.count() - created_count} ta yangilandi.")
        return redirect('attendance:timesheet_list')

    years = list(range(timezone.now().year - 2, timezone.now().year + 1))
    context = {
        'year': timezone.now().year,
        'month': timezone.now().month,
        'years': years,
    }
    return render(request, 'attendance/generate_timesheets.html', context)


@login_required
def timesheet_detail(request, pk):
    """Tabel tafsiloti."""
    timesheet = get_object_or_404(
        MonthlyTimesheet.objects.select_related('employee__user', 'employee__department'),
        pk=pk
    )

    # Oylik davomatlar
    attendances = Attendance.objects.filter(
        employee=timesheet.employee,
        date__year=timesheet.year,
        date__month=timesheet.month
    ).order_by('date')

    context = {
        'timesheet': timesheet,
        'attendances': attendances,
    }
    return render(request, 'attendance/timesheet_detail.html', context)


@login_required
def clear_attendance(request):
    """Davomatlarni tozalash (o'chirish)."""
    if request.method == 'POST':
        date_str = request.POST.get('date')
        department_id = request.POST.get('department')
        employee_ids = request.POST.getlist('employees')  # Tanlangan xodimlar

        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "Noto'g'ri sana.")
            return redirect('attendance:list')

        # O'chiriladigan davomatlar
        attendances = Attendance.objects.filter(
            date=selected_date,
            employee__is_active=True
        )

        # Bo'lim bo'yicha filter
        if department_id:
            attendances = attendances.filter(employee__department_id=department_id)

        # Tanlangan xodimlar bo'yicha filter
        if employee_ids:
            attendances = attendances.filter(employee_id__in=employee_ids)

        count = attendances.count()
        attendances.delete()

        messages.success(request, f"{count} ta davomat o'chirildi.")
        return redirect(f"{reverse('attendance:list')}?date={date_str}")

    return redirect('attendance:list')


@login_required
def mark_all_present(request):
    """Barcha xodimlarni keldi deb belgilash."""
    if request.method == 'POST':
        date_str = request.POST.get('date')
        department_id = request.POST.get('department')
        check_in = request.POST.get('check_in', '09:00')
        check_out = request.POST.get('check_out', '18:00')

        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            check_in_time = datetime.strptime(check_in, '%H:%M').time()
            check_out_time = datetime.strptime(check_out, '%H:%M').time()
        except (ValueError, TypeError):
            messages.error(request, "Noto'g'ri ma'lumot.")
            return redirect('attendance:list')

        # Kelajak sanasiga davomat kiritish mumkin emas
        today = timezone.now().date()
        if selected_date > today:
            messages.error(request, "Kelajak sanasiga davomat kiritish mumkin emas.")
            return redirect('attendance:list')

        employees = Employee.objects.eligible_for_operations()
        if department_id:
            employees = employees.filter(department_id=department_id)

        # Faqat ishga kirgan xodimlar (hire_date <= selected_date)
        employees = employees.filter(hire_date__lte=selected_date)

        # Mavjud davomati yo'qlar
        existing_ids = Attendance.objects.filter(
            date=selected_date,
            employee__in=employees
        ).values_list('employee_id', flat=True)

        to_create = employees.exclude(id__in=existing_ids)
        created_count = 0
        skipped_count = 0

        for emp in to_create:
            # Xodimning ishga kirish sanasini tekshirish
            if emp.hire_date and selected_date < emp.hire_date:
                skipped_count += 1
                continue

            try:
                Attendance.objects.create(
                    employee=emp,
                    date=selected_date,
                    check_in=check_in_time,
                    check_out=check_out_time,
                    status=Attendance.Status.PRESENT,
                    recorded_by=request.user
                )
                created_count += 1
            except IntegrityError:
                # Skip if already exists
                pass

        msg = f"{created_count} ta xodim keldi deb belgilandi."
        if skipped_count:
            msg += f" {skipped_count} ta xodim o'tkazib yuborildi (ishga kirish sanasi)."
        messages.success(request, msg)
        # To'g'ri sanaga qaytarish
        return redirect(f"{reverse('attendance:list')}?date={date_str}")

    return redirect('attendance:list')
