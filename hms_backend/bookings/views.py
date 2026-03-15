from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from doctors.models import Availability, Doctor
from patients.models import Patient
from .models import Booking
import requests
import json
from django.conf import settings
from hms_backend.email_utils import send_email

# Try to import calendar, but don't fail if it's missing
try:
    from hms_backend.google_calendar import create_calendar_event, delete_calendar_event, is_calendar_connected
    CALENDAR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Google Calendar module not available: {e}")
    print("⚠️ Calendar features will be disabled")
    CALENDAR_AVAILABLE = False
    
    # Create dummy functions
    def create_calendar_event(booking):
        print("📅 Calendar disabled - would create event for booking", booking.id)
        return False
    
    def delete_calendar_event(booking):
        print("📅 Calendar disabled - would delete event for booking", booking.id)
        return False
    
    def is_calendar_connected(user):
        return False

# class emailservice added 
class EmailService:
    """Class to handle all email operations for bookings"""
    
    @staticmethod
    def send_booking_confirmation(booking):
        """Send booking confirmation emails to both patient and doctor"""
        
        # Email to patient
        patient_email_sent = send_email(
            email_type='BOOKING_CONFIRMATION',
            recipient=booking.patient.user.email,
            name=booking.patient.user.first_name,
            details={
                'doctor_name': f"Dr. {booking.doctor.user.get_full_name()}",
                'patient_name': booking.patient.user.get_full_name(),
                'date': str(booking.availability.date),
                'time': f"{booking.availability.start_time} - {booking.availability.end_time}",
                'specialization': booking.doctor.specialization,
                'location': 'Hospital Main Building'
            }
        )
        
        # Email to doctor
        doctor_email_sent = send_email(
            email_type='BOOKING_CONFIRMATION',
            recipient=booking.doctor.user.email,
            name=f"Dr. {booking.doctor.user.first_name}",
            details={
                'doctor_name': f"Dr. {booking.doctor.user.get_full_name()}",
                'patient_name': booking.patient.user.get_full_name(),
                'date': str(booking.availability.date),
                'time': f"{booking.availability.start_time} - {booking.availability.end_time}",
                'specialization': booking.doctor.specialization,
                'patient_phone': booking.patient.phone,
                'location': 'Hospital Main Building'
            }
        )
        
        return {
            'patient': patient_email_sent,
            'doctor': doctor_email_sent,
            'both_sent': patient_email_sent and doctor_email_sent,
            'at_least_one': patient_email_sent or doctor_email_sent
        }
    
    @staticmethod
    def send_cancellation_email(booking, cancelled_by, cancelled_by_name):
        """Send cancellation emails to both patient and doctor"""
        
        cancelled_by_text = 'You' if cancelled_by == 'self' else f'Dr. {cancelled_by_name}'
        
        # Email to patient
        patient_email_sent = send_email(
            email_type='BOOKING_CANCELLED',
            recipient=booking.patient.user.email,
            name=booking.patient.user.first_name,
            details={
                'doctor_name': f"Dr. {booking.doctor.user.get_full_name()}",
                'patient_name': booking.patient.user.get_full_name(),
                'date': str(booking.availability.date),
                'time': f"{booking.availability.start_time} - {booking.availability.end_time}",
                'specialization': booking.doctor.specialization,
                'cancelled_by': cancelled_by_text
            }
        )
        
        # Email to doctor
        doctor_email_sent = send_email(
            email_type='BOOKING_CANCELLED',
            recipient=booking.doctor.user.email,
            name=f"Dr. {booking.doctor.user.first_name}",
            details={
                'doctor_name': f"Dr. {booking.doctor.user.get_full_name()}",
                'patient_name': booking.patient.user.get_full_name(),
                'date': str(booking.availability.date),
                'time': f"{booking.availability.start_time} - {booking.availability.end_time}",
                'specialization': booking.doctor.specialization,
                'cancelled_by': 'Patient' if cancelled_by == 'patient' else 'You'
            }
        )
        
        return {
            'patient': patient_email_sent,
            'doctor': doctor_email_sent,
            'both_sent': patient_email_sent and doctor_email_sent
        }
    
    @staticmethod
    def send_appointment_reminder(booking):
        """Send reminder email 24 hours before appointment"""
        # This could be used for a cron job later
        pass


class CalendarService:
    """Class to handle all Google Calendar operations"""
    
    @staticmethod
    def check_user_calendars(booking):
        """Check which users have calendars connected"""
        doctor_connected = is_calendar_connected(booking.doctor.user)
        patient_connected = is_calendar_connected(booking.patient.user)
        return {
            'doctor': doctor_connected,
            'patient': patient_connected,
            'any': doctor_connected or patient_connected,
            'both': doctor_connected and patient_connected
        }
    
    @staticmethod
    def create_events(booking):
        """Create calendar events for booking"""
        if not CALENDAR_AVAILABLE:
            print("Calendar service not available")
            return False
        
        # Check if any user has calendar connected
        calendar_status = CalendarService.check_user_calendars(booking)
        
        if not calendar_status['any']:
            print("⚠️ No users have Google Calendar connected")
            return False
        
        try:
            success = create_calendar_event(booking)
            if success:
                print(f"✅ Calendar events created for booking {booking.id}")
                
                # Log which calendars were updated
                if calendar_status['doctor']:
                    print(f"   - Doctor calendar updated")
                if calendar_status['patient']:
                    print(f"   - Patient calendar updated")
                    
            return success
        except Exception as e:
            print(f"❌ Calendar creation error: {e}")
            return False
    
    @staticmethod
    def delete_events(booking):
        """Delete calendar events for cancelled booking"""
        if not CALENDAR_AVAILABLE or not booking.google_event_id:
            return False
        
        try:
            success = delete_calendar_event(booking)
            if success:
                print(f"✅ Calendar events deleted for booking {booking.id}")
            return success
        except Exception as e:
            print(f"❌ Calendar deletion error: {e}")
            return False


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
        
        # Send emails using EmailService class
        email_result = EmailService.send_booking_confirmation(booking)
        
        # Create Google Calendar events using CalendarService class
        calendar_success = CalendarService.create_events(booking)
        
        # Check calendar connection status for feedback
        calendar_status = CalendarService.check_user_calendars(booking)
        
        # User feedback messages
        if email_result['both_sent']:
            messages.success(request, '✅ Appointment booked! Confirmation emails sent to both patient and doctor.')
        elif email_result['at_least_one']:
            messages.success(request, '✅ Appointment booked! (Some email notifications failed)')
        else:
            messages.warning(request, '✅ Appointment booked but email service unavailable.')
        
        if calendar_success:
            messages.info(request, '📅 Calendar events created successfully.')
        elif calendar_status['any'] and not calendar_success:
            messages.warning(request, '⚠️ Calendar connection issue. Please reconnect in profile.')
        elif not calendar_status['any']:
            # Only show this message if no calendars are connected
            pass  # Don't show message - users will see connect option in profile
        
        return redirect('my_appointments')
    
    return render(request, 'confirm_booking.html', {'availability': availability})


@login_required
def cancel_booking(request, booking_id):
    """Cancel an appointment - accessible by both patient and doctor"""
    
    # Determine user type and get booking
    try:
        if hasattr(request.user, 'patient'):
            user_type = 'patient'
            user_name = request.user.first_name
            booking = get_object_or_404(Booking, id=booking_id, patient=request.user.patient)
            cancelled_by = 'self'  # cancelling own appointment
        elif hasattr(request.user, 'doctor'):
            user_type = 'doctor'
            user_name = request.user.first_name
            booking = get_object_or_404(Booking, id=booking_id, doctor=request.user.doctor)
            cancelled_by = 'doctor'
        else:
            messages.error(request, 'Access denied.')
            return redirect('home')
    except:
        messages.error(request, 'Booking not found.')
        return redirect('home')
    
    # Check if appointment is in the future
    if booking.availability.date < timezone.now().date():
        messages.error(request, 'Cannot cancel past appointments!')
        return redirect('my_appointments' if user_type == 'patient' else 'doctor_appointments')
    
    # Check if already cancelled
    if booking.status == 'cancelled':
        messages.warning(request, 'This appointment is already cancelled.')
        return redirect('my_appointments' if user_type == 'patient' else 'doctor_appointments')
    
    # Process cancellation
    with transaction.atomic():
        # Free up the availability slot
        availability = booking.availability
        availability.is_booked = False
        availability.save()
        
        # Update booking status
        booking.status = 'cancelled'
        booking.save()
        
        # Delete Google Calendar events using CalendarService
        CalendarService.delete_events(booking)
        
        # Send cancellation emails using EmailService
        email_result = EmailService.send_cancellation_email(booking, user_type, user_name)
    
    # Success message
    if user_type == 'patient':
        messages.success(request, '✅ Your appointment has been cancelled successfully.')
    else:
        messages.success(request, f'✅ Appointment with {booking.patient.user.first_name} cancelled successfully.')
    
    if not email_result['both_sent']:
        messages.warning(request, '⚠️ Cancellation processed but some email notifications failed.')
    
    # Redirect based on user type
    if user_type == 'patient':
        return redirect('my_appointments')
    else:
        return redirect('doctor_appointments')


@login_required
def get_booking_details(request, booking_id):
    """API endpoint to get booking details"""
    try:
        if hasattr(request.user, 'patient'):
            booking = get_object_or_404(Booking, id=booking_id, patient=request.user.patient)
        elif hasattr(request.user, 'doctor'):
            booking = get_object_or_404(Booking, id=booking_id, doctor=request.user.doctor)
        else:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        data = {
            'id': booking.id,
            'doctor': f"Dr. {booking.doctor.user.get_full_name()}",
            'patient': booking.patient.user.get_full_name(),
            'date': str(booking.availability.date),
            'start_time': str(booking.availability.start_time),
            'end_time': str(booking.availability.end_time),
            'status': booking.status,
            'specialization': booking.doctor.specialization,
            'doctor_email': booking.doctor.user.email,
            'patient_email': booking.patient.user.email,
            'doctor_phone': booking.doctor.phone,
            'patient_phone': booking.patient.phone
        }
        return JsonResponse(data)
    except:
        return JsonResponse({'error': 'Booking not found'}, status=404)
