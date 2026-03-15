from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Doctor, Availability
from bookings.models import Booking

@login_required
def doctor_dashboard(request):
    try:
        doctor = request.user.doctor
    except:
        messages.error(request, 'Access denied. Doctors only.')
        return redirect('home')
    
    # Get today's date
    today = timezone.now().date()
    
    # Get upcoming availability
    upcoming_availability = Availability.objects.filter(
        doctor=doctor,
        date__gte=today,
        is_booked=False
    ).order_by('date', 'start_time')
    
    # Get today's appointments
    today_appointments = Booking.objects.filter(
        doctor=doctor,
        availability__date=today
    ).select_related('patient', 'availability')
    
    context = {
        'doctor': doctor,
        'upcoming_availability': upcoming_availability,
        'today_appointments': today_appointments
    }
    return render(request, 'doctor_dashboard.html', context)

@login_required
def add_availability(request):
    try:
        doctor = request.user.doctor
    except:
        messages.error(request, 'Access denied. Doctors only.')
        return redirect('home')
    
    if request.method == 'POST':
        date = request.POST['date']
        start_time = request.POST['start_time']
        end_time = request.POST['end_time']
        
        # Check if slot already exists
        existing = Availability.objects.filter(
            doctor=doctor,
            date=date,
            start_time=start_time,
            end_time=end_time
        ).exists()
        
        if existing:
            messages.error(request, 'This time slot already exists!')
        else:
            Availability.objects.create(
                doctor=doctor,
                date=date,
                start_time=start_time,
                end_time=end_time
            )
            messages.success(request, 'Availability added successfully!')
            return redirect('doctor_dashboard')
    
    return render(request, 'add_availability.html')

@login_required
def delete_availability(request, availability_id):
    try:
        doctor = request.user.doctor
    except:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    availability = get_object_or_404(Availability, id=availability_id, doctor=doctor)
    
    if not availability.is_booked:
        availability.delete()
        messages.success(request, 'Availability deleted successfully!')
    else:
        messages.error(request, 'Cannot delete booked slot!')
    
    return redirect('doctor_dashboard')


@login_required
def doctor_appointments(request):
    try:
        doctor = request.user.doctor
    except:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    appointments = Booking.objects.filter(
        doctor=doctor
    ).select_related('patient', 'availability').order_by('-availability__date', '-availability__start_time')
    
    return render(request, 'doctor_appointments.html', {
        'appointments': appointments,
        'now': timezone.now().date()  # Add this
    })
