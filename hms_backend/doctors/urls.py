from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('add-availability/', views.add_availability, name='add_availability'),
    path('delete-availability/<int:availability_id>/', views.delete_availability, name='delete_availability'),
    path('appointments/', views.doctor_appointments, name='doctor_appointments'),
]