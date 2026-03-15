import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Allow HTTP for local development

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import os
import pickle

from doctors.models import Doctor
from patients.models import Patient
from .email_utils import send_email
from .google_calendar import get_auth_url, is_calendar_connected

# Google OAuth callback
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

def home(request):
    return render(request, 'home.html')

def signup_choice(request):
    return render(request, 'signup_choice.html')

def signup_doctor(request):
    if request.method == 'POST':
        # Get form data
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        specialization = request.POST['specialization']
        license_number = request.POST['license_number']
        phone = request.POST['phone']
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create doctor profile
        Doctor.objects.create(
            user=user,
            specialization=specialization,
            license_number=license_number,
            phone=phone
        )
        
        # Send welcome email
        send_email(
            email_type='SIGNUP_WELCOME',
            recipient=user.email,
            name=user.first_name or user.username,
            details={'user_type': 'doctor', 'specialization': specialization}
        )
        
        # Log the user in
        login(request, user)
        messages.success(request, 'Doctor account created successfully!')
        return redirect('doctor_dashboard')
    
    return render(request, 'signup_doctor.html')

def signup_patient(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        phone = request.POST['phone']
        date_of_birth = request.POST['date_of_birth']
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create patient profile
        Patient.objects.create(
            user=user,
            phone=phone,
            date_of_birth=date_of_birth
        )
        
        # Send welcome email
        send_email(
            email_type='SIGNUP_WELCOME',
            recipient=user.email,
            name=user.first_name or user.username,
            details={'user_type': 'patient'}
        )
        
        # Log the user in
        login(request, user)
        messages.success(request, 'Patient account created successfully!')
        return redirect('patient_dashboard')
    
    return render(request, 'signup_patient.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Redirect based on role
            if hasattr(user, 'doctor'):
                return redirect('doctor_dashboard')
            elif hasattr(user, 'patient'):
                return redirect('patient_dashboard')
            else:
                return redirect('admin:index')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('home')

@login_required
def profile(request):
    """User profile view for editing personal information"""
    # Check calendar connection status
    calendar_connected = is_calendar_connected(request.user)
    
    if request.method == 'POST':
        # Get the current user
        user = request.user
        
        # Update basic user info
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        # Update doctor-specific fields
        if hasattr(user, 'doctor'):
            doctor = user.doctor
            doctor.specialization = request.POST.get('specialization', doctor.specialization)
            doctor.license_number = request.POST.get('license_number', doctor.license_number)
            doctor.phone = request.POST.get('phone', doctor.phone)
            doctor.save()
            messages.success(request, 'Doctor profile updated successfully!')
        
        # Update patient-specific fields
        elif hasattr(user, 'patient'):
            patient = user.patient
            patient.phone = request.POST.get('phone', patient.phone)
            patient.date_of_birth = request.POST.get('date_of_birth', patient.date_of_birth)
            patient.address = request.POST.get('address', patient.address)
            patient.save()
            messages.success(request, 'Patient profile updated successfully!')
        
        # Handle password change
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if current_password and new_password and confirm_password:
            if new_password == confirm_password:
                if user.check_password(current_password):
                    user.set_password(new_password)
                    user.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, 'Password changed successfully!')
                else:
                    messages.error(request, 'Current password is incorrect!')
            else:
                messages.error(request, 'New passwords do not match!')
        
        return redirect('profile')
    
    return render(request, 'profile.html', {
        'calendar_connected': calendar_connected
    })

@login_required
def test_email(request):
    """Test endpoint for email service"""
    result = send_email(
        email_type='SIGNUP_WELCOME',
        recipient=request.user.email,
        name=request.user.first_name or request.user.username,
        details={'test': True, 'message': 'This is a test email from your profile page'}
    )
    
    if result:
        messages.success(request, '✅ Test email sent! Check your inbox.')
    else:
        messages.error(request, '❌ Email failed. Make sure email service is running on port 3000.')
    
    return redirect('profile')

@login_required
def connect_google_calendar(request):
    """Initiate Google Calendar OAuth flow"""
    auth_url = get_auth_url(request.user)
    if auth_url:
        return redirect(auth_url)
    else:
        messages.error(request, 'Failed to initialize Google Calendar connection. Check credentials.json file.')
        return redirect('profile')

def oauth2callback(request):
    """Handle OAuth2 callback from Google"""
    try:
        print("\n" + "="*50)
        print("🔍 OAUTH CALLBACK RECEIVED")
        print("="*50)
        
        # Get the state (user ID) from request
        user_id = request.GET.get('state')
        code = request.GET.get('code')
        
        print(f"📌 State (user_id): {user_id}")
        print(f"📌 Code received: {'Yes' if code else 'No'}")
        
        if not user_id:
            print("❌ No user ID in state")
            messages.error(request, 'Invalid OAuth callback: No user ID')
            return redirect('profile')
        
        if not code:
            print("❌ No authorization code received")
            messages.error(request, 'No authorization code from Google')
            return redirect('profile')
        
        print(f"🔄 Creating Flow with redirect_uri: http://localhost:8000/oauth2callback")
        
        # Create flow instance with EXACT same redirect URI
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri='http://localhost:8000/oauth2callback'
        )
        
        # Exchange authorization code for credentials
        print("🔄 Exchanging code for tokens...")
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials
        print("✅ Token exchange successful!")
        
        # Save credentials
        import os
        import pickle
        os.makedirs('google_tokens', exist_ok=True)
        token_path = f'google_tokens/{user_id}_token.pickle'
        
        with open(token_path, 'wb') as token:
            pickle.dump(credentials, token)
        print(f"✅ Token saved to: {token_path}")
        
        # Update user's calendar connection status
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
            if hasattr(user, 'doctor'):
                user.doctor.google_calendar_connected = True
                user.doctor.save()
                print(f"✅ Doctor calendar status updated")
            elif hasattr(user, 'patient'):
                user.patient.google_calendar_connected = True
                user.patient.save()
                print(f"✅ Patient calendar status updated")
        except Exception as e:
            print(f"⚠️ Could not update user status: {e}")
        
        print("="*50)
        print("✅ SUCCESS! Google Calendar connected!")
        print("="*50)
        
        messages.success(request, '✅ Google Calendar connected successfully!')
        return redirect('profile')
        
    except Exception as e:
        print("\n❌ ERROR IN CALLBACK:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*50)
        
        messages.error(request, f'Failed to connect Google Calendar: {str(e)}')
        return redirect('profile')

@login_required
def calendar_status(request):
    """AJAX endpoint to check calendar connection status"""
    connected = is_calendar_connected(request.user)
    return JsonResponse({'connected': connected})
