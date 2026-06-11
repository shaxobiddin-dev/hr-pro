"""
Leave URLs.
"""

from django.urls import path
from . import views

app_name = 'leave'

urlpatterns = [
    # Dashboard
    path('', views.leave_dashboard, name='dashboard'),

    # So'rovlar
    path('requests/', views.leave_request_list, name='request_list'),
    path('requests/create/', views.leave_request_create, name='request_create'),
    path('requests/<int:pk>/', views.leave_request_detail, name='request_detail'),
    path('requests/<int:pk>/submit/', views.leave_request_submit, name='request_submit'),
    path('requests/<int:pk>/approve/', views.leave_request_approve, name='request_approve'),
    path('requests/<int:pk>/cancel/', views.leave_request_cancel, name='request_cancel'),

    # Balanslar
    path('balances/', views.leave_balance_list, name='balance_list'),

    # Kalendar
    path('calendar/', views.leave_calendar, name='calendar'),

    # Turlar
    path('types/', views.leave_type_list, name='type_list'),
]
