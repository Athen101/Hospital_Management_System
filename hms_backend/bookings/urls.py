from django.urls import path
from . import views

urlpatterns = [
    path('book/<int:availability_id>/', views.book_appointment, name='book_appointment'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
]