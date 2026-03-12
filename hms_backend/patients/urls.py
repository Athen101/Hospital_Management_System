from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('doctors/', views.list_doctors, name='list_doctors'),
    path('doctor/<int:doctor_id>/availability/', views.view_doctor_availability, name='view_doctor_availability'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
]