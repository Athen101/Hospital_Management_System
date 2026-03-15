from django.db import models
from django.contrib.auth.models import User

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Google Calendar fields
    google_calendar_connected = models.BooleanField(default=False)
    google_calendar_email = models.EmailField(blank=True, null=True)
    google_refresh_token = models.TextField(blank=True, null=True)  # Store refresh token securely
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
    def get_calendar_status(self):
        """Return calendar connection status with email if connected"""
        if self.google_calendar_connected and self.google_calendar_email:
            return f"Connected to {self.google_calendar_email}"
        return "Not connected"
    
    class Meta:
        ordering = ['user__first_name', 'user__last_name']  # Optional: add default ordering
