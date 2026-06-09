"""
Department URL patterns.
"""

from django.urls import path
from . import views

app_name = 'departments'

urlpatterns = [
    path('', views.DepartmentListView.as_view(), name='department_list'),
    path('create/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('<int:pk>/', views.DepartmentDetailView.as_view(), name='department_detail'),
    path('<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_update'),
    path('<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department_delete'),
]
