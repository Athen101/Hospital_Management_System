from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from doctors.models import Availability, Doctor
from patients.models import Patient
from .models import Booking
import requests
import json
from django.conf import settings

@login_required
@transaction.atomic
def book_appointment(request, availability_id):
    try:
        patient = request.user.patient
    except:
        messages.error(request, 'Please login as patient to book appointments')
        return redirect('login')
    
    # Get the availability slot and lock it for update to prevent race conditions
    availability = get_object_or_404(
        Availability.objects.select_for_update(),
        id=availability_id,
        is_booked=False,
        date__gte=timezone.now().date()
    )
    
    if request.method == 'POST':
        # Double-check if still available (important for race conditions)
        if availability.is_booked:
            messages.error(request, 'Sorry, this slot was just booked by someone else!')
            return redirect('view_doctor_availability', doctor_id=availability.doctor.id)
        
        # Create booking
        booking = Booking.objects.create(
            patient=patient,
            doctor=availability.doctor,
            availability=availability
        )
        
        # Mark slot as booked
        availability.is_booked = True
        availability.save()
        
        # TODO: Add Google Calendar integration here
        # TODO: Call email service here
        
        messages.success(request, 'Appointment booked successfully!')
        return redirect('my_appointments')
    
    return render(request, 'confirm_booking.html', {'availability': availability})

@login_required
def cancel_booking(request, booking_id):
    try:
        patient = request.user.patient
    except:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    booking = get_object_or_404(Booking, id=booking_id, patient=patient)
    
    # Only allow cancellation of future appointments
    if booking.availability.date >= timezone.now().date():
        with transaction.atomic():
            # Free up the availability slot
            availability = booking.availability
            availability.is_booked = False
            availability.save()
            
            # Update booking status
            booking.status = 'cancelled'
            booking.save()
            
            # TODO: Send cancellation email
            
        messages.success(request, 'Appointment cancelled successfully!')
    else:
        messages.error(request, 'Cannot cancel past appointments!')
    
    return redirect('my_appointments')