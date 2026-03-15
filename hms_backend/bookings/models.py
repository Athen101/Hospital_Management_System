from django.db import models
from django.contrib.auth.models import User
from doctors.models import Doctor, Availability
from patients.models import Patient

class Booking(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='bookings')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='bookings')
    availability = models.OneToOneField(Availability, on_delete=models.CASCADE, related_name='booking')
    booked_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed')
    ], default='confirmed')
    google_event_id = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return f"{self.patient} - {self.doctor} - {self.availability.date}"
