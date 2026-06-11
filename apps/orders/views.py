"""
Buyruqlar views.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.utils.crypto import get_random_string
from decimal import Decimal

from .models import Order, HiringOrderItem
from .forms import OrderForm, HiringOrderItemFormSet
from apps.employees.models import Employee, Position, MHTMHistory, Level
from apps.departments.models import Department
from apps.accounts.models import User


@login_required
def order_list(request):
    """Buyruqlar ro'yxati."""
    order_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    show_archive = request.GET.get('archive') == '1'

    if show_archive:
        # Arxivdagi buyruqlar (is_active=False)
        orders = Order.objects.filter(is_active=False).select_related('approved_by__user', 'created_by')
    else:
        # Faol buyruqlar (is_active=True)
        orders = Order.objects.filter(is_active=True).select_related('approved_by__user', 'created_by')

    if order_type:
        orders = orders.filter(order_type=order_type)

    if status:
        orders = orders.filter(status=status)

    # Arxivdagi buyruqlar soni
    archive_count = Order.objects.filter(is_active=False).count()

    context = {
        'orders': orders,
        'order_types': Order.OrderType.choices,
        'status_choices': Order.Status.choices,
        'current_type': order_type,
        'current_status': status,
        'show_archive': show_archive,
        'archive_count': archive_count,
    }
    return render(request, 'orders/order_list.html', context)


@login_required
def hiring_order_create(request):
    """Ishga olish buyrug'i yaratish."""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = HiringOrderItemFormSet(request.POST, prefix='items')

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Buyruqni saqlash
                    order = form.save(commit=False)
                    order.order_type = Order.OrderType.HIRING
                    order.created_by = request.user
                    order.save()

                    # Qatorlarni saqlash (bo'sh qatorlarni o'tkazib yuborish)
                    items = formset.save(commit=False)
                    for item in items:
                        # Tegishli formni topish
                        item_form = None
                        for f in formset.forms:
                            if f.instance == item:
                                item_form = f
                                break

                        # Bo'sh qatorni o'tkazib yuborish
                        if item_form and hasattr(item_form, 'is_empty_row') and item_form.is_empty_row():
                            continue

                        if item_form and item_form.cleaned_data.get('is_new_employee'):
                            # Yangi user va employee yaratish
                            new_email = item_form.cleaned_data['new_email']
                            # Username sifatida email'ning @ dan oldingi qismini ishlatamiz
                            base_username = new_email.split('@')[0]
                            username = base_username
                            # Agar username mavjud bo'lsa, raqam qo'shamiz
                            counter = 1
                            while User.objects.filter(username=username).exists():
                                username = f"{base_username}{counter}"
                                counter += 1

                            user = User.objects.create_user(
                                username=username,
                                email=new_email,
                                first_name=item_form.cleaned_data['new_first_name'],
                                last_name=item_form.cleaned_data['new_last_name'],
                                password=get_random_string(12)
                            )

                            # Default level olish
                            default_level = Level.objects.first()

                            employee = Employee.objects.create(
                                user=user,
                                employee_code=Employee.generate_employee_code(),
                                department=item.department,
                                position=item.position,
                                level=default_level,
                                hire_date=item.start_date,
                                status='pending'  # Buyruq tasdiqlanmaguncha kutilmoqda
                            )
                            item.employee = employee

                        item.order = order
                        item.save()

                    # O'chirilganlarni ham saqlash
                    for obj in formset.deleted_objects:
                        obj.delete()

                    messages.success(request, f"Buyruq #{order.order_number} yaratildi.")
                    return redirect('orders:detail', pk=order.pk)
            except IntegrityError as e:
                error_msg = str(e)
                if 'email' in error_msg.lower():
                    messages.error(request, "Bu email allaqachon ro'yxatdan o'tgan.")
                elif 'order_number' in error_msg.lower():
                    messages.error(request, "Bu buyruq raqami allaqachon mavjud.")
                else:
                    messages.error(request, f"Ma'lumotlar bazasi xatosi: {error_msg}")
        else:
            messages.error(request, "Formada xatoliklar bor. Tekshiring.")
    else:
        form = OrderForm()
        formset = HiringOrderItemFormSet(prefix='items')

    context = {
        'form': form,
        'formset': formset,
        'title': "Ishga olish buyrug'i",
    }
    return render(request, 'orders/hiring_order_form.html', context)


@login_required
def hiring_order_update(request, pk):
    """Ishga olish buyrug'ini tahrirlash."""
    order = get_object_or_404(Order, pk=pk, order_type=Order.OrderType.HIRING)

    if order.status == Order.Status.APPROVED:
        messages.error(request, "Tasdiqlangan buyruqni tahrirlash mumkin emas.")
        return redirect('orders:detail', pk=pk)

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        formset = HiringOrderItemFormSet(request.POST, instance=order, prefix='items')

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    order = form.save()
                    formset.save()

                    messages.success(request, f"Buyruq #{order.order_number} yangilandi.")
                    return redirect('orders:detail', pk=order.pk)
            except IntegrityError as e:
                error_msg = str(e)
                if 'order_number' in error_msg.lower():
                    messages.error(request, "Bu buyruq raqami allaqachon mavjud.")
                else:
                    messages.error(request, f"Ma'lumotlar bazasi xatosi: {error_msg}")
        else:
            messages.error(request, "Formada xatoliklar bor. Tekshiring.")
    else:
        form = OrderForm(instance=order)
        formset = HiringOrderItemFormSet(instance=order, prefix='items')

    context = {
        'form': form,
        'formset': formset,
        'order': order,
        'title': f"Buyruqni tahrirlash: {order.order_number}",
    }
    return render(request, 'orders/hiring_order_form.html', context)


@login_required
def order_detail(request, pk):
    """Buyruq tafsiloti."""
    order = get_object_or_404(
        Order.objects.select_related('approved_by__user', 'created_by'),
        pk=pk
    )

    # Buyruq turiga qarab qatorlarni olish
    if order.order_type == Order.OrderType.HIRING:
        items = order.hiring_items.all().select_related(
            'employee__user', 'department', 'position',
            'probation_department', 'probation_position'
        )
    else:
        items = []

    context = {
        'order': order,
        'items': items,
    }
    return render(request, 'orders/order_detail.html', context)


@login_required
def order_approve(request, pk):
    """Buyruqni tasdiqlash."""
    order = get_object_or_404(Order, pk=pk)

    if order.status != Order.Status.DRAFT:
        messages.error(request, "Faqat qoralama buyruqlarni tasdiqlash mumkin.")
        return redirect('orders:detail', pk=pk)

    # Foydalanuvchining xodim profilini olish
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, "Sizning xodim profilingiz topilmadi.")
        return redirect('orders:detail', pk=pk)

    order.approve(employee)
    messages.success(request, f"Buyruq #{order.order_number} tasdiqlandi.")

    return redirect('orders:detail', pk=pk)


@login_required
def order_delete(request, pk):
    """Buyruqni o'chirish yoki arxivlash."""
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        order_number = order.order_number

        if order.can_hard_delete():
            # Tasdiqlangan bo'lmasa - to'liq o'chirish
            order.delete()
            messages.success(request, f"Buyruq #{order_number} o'chirildi.")
        else:
            # Tasdiqlangan bo'lsa - arxivlash
            order.soft_delete()
            messages.success(request, f"Buyruq #{order_number} arxivlandi.")

        return redirect('orders:list')

    return redirect('orders:detail', pk=pk)


@login_required
def order_restore(request, pk):
    """Buyruqni arxivdan tiklash."""
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        order.restore()
        messages.success(request, f"Buyruq #{order.order_number} tiklandi.")

    return redirect('orders:list')


# ===== API Endpoints =====

@login_required
def api_positions(request):
    """Barcha faol lavozimlarni olish."""
    positions = Position.objects.filter(
        is_active=True
    ).values('id', 'name', 'code', 'base_coefficient').order_by('name')

    return JsonResponse(list(positions), safe=False)


@login_required
def api_position_salary(request, position_id):
    """Lavozim bo'yicha oylik hisoblash."""
    position = get_object_or_404(Position, pk=position_id)

    # MHTM × lavozim koeffitsiyenti
    mhtm = MHTMHistory.get_current()
    base_salary = mhtm * position.base_coefficient

    return JsonResponse({
        'salary': float(base_salary),
        'mhtm': float(mhtm),
        'coefficient': float(position.base_coefficient),
    })


@login_required
def api_generate_order_number(request):
    """Yangi buyruq raqami generatsiya."""
    return JsonResponse({
        'order_number': Order.generate_order_number()
    })


# ===== PDF Generation =====

@login_required
def order_print(request, pk):
    """Buyruqni chop etish uchun PDF."""
    order = get_object_or_404(Order, pk=pk)

    # Hozircha oddiy HTML template
    if order.order_type == Order.OrderType.HIRING:
        items = order.hiring_items.all().select_related(
            'employee__user', 'department', 'position'
        )
        template = 'orders/print/hiring_order.html'
    else:
        items = []
        template = 'orders/print/generic_order.html'

    context = {
        'order': order,
        'items': items,
    }
    return render(request, template, context)
