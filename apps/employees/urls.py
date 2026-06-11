"""
Employee URL patterns.
"""

from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    # Employee URLs
    path('', views.EmployeeListView.as_view(), name='employee_list'),
    # Yangi xodim faqat buyruq orqali yaratiladi -> orders:hiring_create
    path('<int:pk>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
    path('<int:pk>/edit/', views.EmployeeUpdateView.as_view(), name='employee_update'),
    path('<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee_delete'),
    path('<int:pk>/restore/', views.employee_restore, name='employee_restore'),

    # HTMX partials
    path('<int:pk>/salary/', views.employee_salary_calculator, name='employee_salary'),
    path('api/positions-by-department/', views.positions_by_department, name='positions_by_department'),

    # Position URLs
    path('positions/', views.PositionListView.as_view(), name='position_list'),
    path('positions/create/', views.PositionCreateView.as_view(), name='position_create'),
    path('positions/<int:pk>/edit/', views.PositionUpdateView.as_view(), name='position_update'),
    path('positions/<int:pk>/delete/', views.PositionDeleteView.as_view(), name='position_delete'),

    # Level URLs
    path('levels/', views.LevelListView.as_view(), name='level_list'),
]
