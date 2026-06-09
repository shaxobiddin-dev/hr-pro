"""
Payroll URLs.
"""

from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    # PayrollPeriod (davrlar)
    path('', views.period_list, name='period_list'),
    path('periods/create/', views.period_create, name='period_create'),
    path('periods/<int:pk>/', views.period_detail, name='period_detail'),
    path('periods/<int:pk>/update/', views.period_update, name='period_update'),
    path('periods/<int:pk>/delete/', views.period_delete, name='period_delete'),
    path('periods/<int:pk>/generate/', views.generate_payrolls, name='generate_payrolls'),
    path('periods/<int:pk>/calculate/', views.calculate_all, name='calculate_all'),
    path('periods/<int:pk>/confirm/', views.confirm_period, name='confirm_period'),

    # Payroll (individual)
    path('payroll/<int:pk>/', views.payroll_detail, name='payroll_detail'),
    path('payroll/<int:pk>/update/', views.payroll_update, name='payroll_update'),
    path('payroll/<int:pk>/calculate/', views.payroll_calculate, name='payroll_calculate'),
    path('payroll/<int:pk>/add-item/', views.payroll_add_item, name='payroll_add_item'),
    path('payroll/<int:pk>/delete-item/<int:item_pk>/', views.payroll_delete_item, name='payroll_delete_item'),

    # Payslip
    path('payroll/<int:pk>/payslip/', views.payslip, name='payslip'),

    # Components
    path('components/', views.component_list, name='component_list'),
]
