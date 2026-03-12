from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'availability', 'status', 'booked_at']
    list_filter = ['status', 'booked_at']