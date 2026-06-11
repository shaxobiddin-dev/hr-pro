"""
Buyruqlar URL patterns.
"""

from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Buyruqlar ro'yxati
    path('', views.order_list, name='list'),

    # Ishga olish buyrug'i
    path('hiring/create/', views.hiring_order_create, name='hiring_create'),
    path('hiring/<int:pk>/edit/', views.hiring_order_update, name='hiring_update'),

    # Umumiy
    path('<int:pk>/', views.order_detail, name='detail'),
    path('<int:pk>/approve/', views.order_approve, name='approve'),
    path('<int:pk>/delete/', views.order_delete, name='delete'),
    path('<int:pk>/restore/', views.order_restore, name='restore'),
    path('<int:pk>/print/', views.order_print, name='print'),

    # API
    path('api/positions/', views.api_positions, name='api_positions'),
    path('api/salary/<int:position_id>/', views.api_position_salary, name='api_salary'),
    path('api/generate-number/', views.api_generate_order_number, name='api_generate_number'),
]
