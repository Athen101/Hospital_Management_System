from django.db import models
from django.contrib.auth.models import User

class Doctor(models.Model):
    # Specialization choices
    SPECIALIZATIONS = [
        ('CARDIOLOGY', 'Cardiology'),
        ('DERMATOLOGY', 'Dermatology'),
        ('NEUROLOGY', 'Neurology'),
        ('PEDIATRICS', 'Pediatrics'),
        ('ORTHOPEDICS', 'Orthopedics'),
        ('GYNECOLOGY', 'Gynecology'),
        ('OPHTHALMOLOGY', 'Ophthalmology'),
        ('ENT', 'ENT Specialist'),
        ('PSYCHIATRY', 'Psychiatry'),
        ('RADIOLOGY', 'Radiology'),
        ('ANESTHESIOLOGY', 'Anesthesiology'),
        ('EMERGENCY', 'Emergency Medicine'),
        ('FAMILY', 'Family Medicine'),
        ('INTERNAL', 'Internal Medicine'),
        ('ONCOLOGY', 'Oncology'),
        ('UROLOGY', 'Urology'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=50, choices=SPECIALIZATIONS, default='FAMILY')
    license_number = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Google Calendar fields
    google_calendar_connected = models.BooleanField(default=False)
    google_calendar_email = models.EmailField(blank=True, null=True)
    google_refresh_token = models.TextField(blank=True, null=True)  # Store refresh token securely
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.get_specialization_display()}"
    
    def get_calendar_status(self):
        """Return calendar connection status with email if connected"""
        if self.google_calendar_connected and self.google_calendar_email:
            return f"Connected to {self.google_calendar_email}"
        return "Not connected"

class Availability(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.doctor} - {self.date} {self.start_time}-{self.end_time}"
    
    class Meta:
        verbose_name_plural = "Availabilities"
        ordering = ['date', 'start_time']  # Add default ordering
