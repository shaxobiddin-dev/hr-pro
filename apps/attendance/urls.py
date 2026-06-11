"""
Attendance URLs.
"""

from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Dashboard
    path('', views.attendance_dashboard, name='dashboard'),

    # Davomatlar
    path('list/', views.attendance_list, name='list'),
    path('create/', views.attendance_create, name='create'),
    path('<int:pk>/update/', views.attendance_update, name='update'),
    path('<int:pk>/delete/', views.attendance_delete, name='delete'),

    # Tezkor kiritish
    path('quick-check/', views.quick_check_in, name='quick_check'),
    path('bulk/', views.bulk_attendance, name='bulk'),
    path('mark-all-present/', views.mark_all_present, name='mark_all_present'),
    path('clear/', views.clear_attendance, name='clear'),

    # Tabellar
    path('timesheets/', views.timesheet_list, name='timesheet_list'),
    path('timesheets/generate/', views.generate_timesheets, name='generate_timesheets'),
    path('timesheets/<int:pk>/', views.timesheet_detail, name='timesheet_detail'),
]
