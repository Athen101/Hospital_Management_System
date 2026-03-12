from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from doctors.models import Doctor, Availability
from bookings.models import Booking
from patients.models import Patient

@login_required
def patient_dashboard(request):
    try:
        patient = request.user.patient
    except:
        messages.error(request, 'Access denied. Patients only.')
        return redirect('home')
    
    # Get upcoming appointments
    upcoming = Booking.objects.filter(
        patient=patient,
        availability__date__gte=timezone.now().date(),
        status='confirmed'
    ).select_related('doctor', 'availability').order_by('availability__date', 'availability__start_time')[:5]
    
    # Get past appointments
    past = Booking.objects.filter(
        patient=patient,
        availability__date__lt=timezone.now().date()
    ).select_related('doctor', 'availability').order_by('-availability__date')[:5]
    
    context = {
        'patient': patient,
        'upcoming_appointments': upcoming,
        'past_appointments': past
    }
    return render(request, 'patient_dashboard.html', context)

@login_required
def list_doctors(request):
    try:
        patient = request.user.patient
    except:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    doctors = Doctor.objects.all().select_related('user')
    return render(request, 'list_doctors.html', {'doctors': doctors})

@login_required
def view_doctor_availability(request, doctor_id):
    try:
        patient = request.user.patient
    except:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    # Get future available slots
    today = timezone.now().date()
    available_slots = Availability.objects.filter(
        doctor=doctor,
        date__gte=today,
        is_booked=False
    ).order_by('date', 'start_time')
    
    context = {
        'doctor': doctor,
        'available_slots': available_slots
    }
    return render(request, 'view_doctor_availability.html', context)

@login_required
def my_appointments(request):
    try:
        patient = request.user.patient
    except:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    appointments = Booking.objects.filter(
        patient=patient
    ).select_related('doctor', 'availability').order_by('-availability__date', '-availability__start_time')
    
    return render(request, 'my_appointments.html', {'appointments': appointments})