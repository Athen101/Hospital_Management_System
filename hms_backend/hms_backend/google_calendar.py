import os
import pickle
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.conf import settings
from django.urls import reverse
import json
import pytz
from datetime import datetime as dt

# Scopes required for Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_google_calendar_service(user):
    """Get or create Google Calendar service for a user"""
    creds = None
    token_path = f'google_tokens/{user.id}_token.pickle'
    
    # Create token directory if it doesn't exist
    os.makedirs('google_tokens', exist_ok=True)
    
    # Load existing token if available
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # If credentials don't exist or are invalid, let user login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            return None
        
        # Save credentials for next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building service: {e}")
        return None

def format_datetime_for_google(date_obj, time_obj):
    """Format datetime for Google Calendar API in RFC3339 format"""
    # Combine date and time
    dt_naive = dt.combine(date_obj, time_obj)
    # Make timezone aware (IST)
    ist = pytz.timezone('Asia/Kolkata')
    dt_aware = ist.localize(dt_naive)
    # Format in RFC3339
    return dt_aware.isoformat()

def create_calendar_event(booking):
    """Create calendar events for both doctor and patient"""
    try:
        print(f"\n📅 Creating calendar events for booking #{booking.id}")
        print(f"   Doctor: {booking.doctor.user.email}")
        print(f"   Patient: {booking.patient.user.email}")
        print(f"   Date: {booking.availability.date}")
        print(f"   Time: {booking.availability.start_time} - {booking.availability.end_time}")
        
        # Get services for both users
        doctor_service = get_google_calendar_service(booking.doctor.user)
        patient_service = get_google_calendar_service(booking.patient.user)
        
        # Format datetime strings properly using RFC3339 format
        start_datetime = format_datetime_for_google(
            booking.availability.date, 
            booking.availability.start_time
        )
        end_datetime = format_datetime_for_google(
            booking.availability.date, 
            booking.availability.end_time
        )
        
        print(f"   Formatted start: {start_datetime}")
        print(f"   Formatted end: {end_datetime}")
        
        # Event for doctor's calendar (with patient name)
        doctor_event_details = {
            'summary': f'Appointment with {booking.patient.user.get_full_name()}',
            'description': (
                f'Medical appointment with {booking.patient.user.get_full_name()}\n'
                f'Specialization: {booking.doctor.specialization}\n'
                f'Patient Phone: {booking.patient.phone}\n'
                f'Booking ID: #{booking.id}'
            ),
            'start': {
                'dateTime': start_datetime,
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': 'Asia/Kolkata',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
            'colorId': '1',  # Blue color for doctor
        }
        
        # Event for patient's calendar (with doctor name)
        patient_event_details = {
            'summary': f'Appointment with Dr. {booking.doctor.user.get_full_name()}',
            'description': (
                f'Medical appointment with Dr. {booking.doctor.user.get_full_name()}\n'
                f'Specialization: {booking.doctor.specialization}\n'
                f'Doctor Phone: {booking.doctor.phone}\n'
                f'Booking ID: #{booking.id}'
            ),
            'start': {
                'dateTime': start_datetime,
                'timeZone': 'Asia/Kolkata',
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': 'Asia/Kolkata',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
            'colorId': '2',  # Green color for patient
        }
        
        # Create event in doctor's calendar
        doctor_event_id = None
        if doctor_service:
            try:
                print(f"   Creating doctor calendar event...")
                doctor_event = doctor_service.events().insert(
                    calendarId='primary', 
                    body=doctor_event_details
                ).execute()
                doctor_event_id = doctor_event.get('id')
                print(f"   ✅ Doctor calendar event created: {doctor_event.get('htmlLink')}")
            except Exception as e:
                print(f"   ❌ Error creating doctor calendar event: {str(e)}")
                print(f"   Event details sent: {json.dumps(doctor_event_details, indent=2)}")
        
        # Create event in patient's calendar
        patient_event_id = None
        if patient_service:
            try:
                print(f"   Creating patient calendar event...")
                patient_event = patient_service.events().insert(
                    calendarId='primary', 
                    body=patient_event_details
                ).execute()
                patient_event_id = patient_event.get('id')
                print(f"   ✅ Patient calendar event created: {patient_event.get('htmlLink')}")
            except Exception as e:
                print(f"   ❌ Error creating patient calendar event: {str(e)}")
                print(f"   Event details sent: {json.dumps(patient_event_details, indent=2)}")
        
        # Store the event ID in the booking (doctor's event ID)
        if doctor_event_id:
            booking.google_event_id = doctor_event_id
            booking.save(update_fields=['google_event_id'])
            print(f"   ✅ Saved event ID to booking: {doctor_event_id}")
        
        success = doctor_event_id is not None or patient_event_id is not None
        if success:
            print(f"   ✅ Calendar events created successfully")
        else:
            print(f"   ❌ Failed to create any calendar events")
        
        return success
        
    except Exception as e:
        print(f"❌ Error creating calendar event: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def delete_calendar_event(booking):
    """Delete calendar events for a cancelled booking"""
    try:
        # Get services for both users
        doctor_service = get_google_calendar_service(booking.doctor.user)
        patient_service = get_google_calendar_service(booking.patient.user)
        
        deleted = False
        
        # Delete from doctor's calendar
        if doctor_service and booking.google_event_id:
            try:
                doctor_service.events().delete(
                    calendarId='primary', 
                    eventId=booking.google_event_id
                ).execute()
                print(f"✅ Calendar event deleted for doctor")
                deleted = True
            except Exception as e:
                print(f"❌ Error deleting doctor calendar event: {e}")
        
        # Note: We don't store patient's event ID separately
        return deleted
    except Exception as e:
        print(f"❌ Error deleting calendar event: {e}")
        return False

def get_auth_url(user):
    """Get Google OAuth URL for a user"""
    try:
        # Use redirect URI from settings or default
        redirect_uri = getattr(settings, 'GOOGLE_CALENDAR', {}).get('REDIRECT_URI', 'http://localhost:8000/oauth2callback')
        
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        # Store user ID in session for callback
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=str(user.id),
            prompt='consent'  # Force to get refresh token
        )
        
        return auth_url
    except Exception as e:
        print(f"Error generating auth URL: {e}")
        return None

def is_calendar_connected(user):
    """Check if user has connected their Google Calendar"""
    if not user or not user.id:
        return False
    token_path = f'google_tokens/{user.id}_token.pickle'
    exists = os.path.exists(token_path)
    print(f"🔍 Calendar check for user {user.id}: {'✅ Found' if exists else '❌ Not found'}")
    return exists