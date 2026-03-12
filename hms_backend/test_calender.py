import os
import sys
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_backend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.contrib.auth.models import User

def test_google_auth():
    """Test Google OAuth flow with correct redirect URI"""
    
    # Create a test user if not exists
    user, created = User.objects.get_or_create(
        username='testdoctor',
        defaults={
            'email': 'your-email@gmail.com',
            'first_name': 'Test',
            'last_name': 'Doctor'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print("✓ Test user created")
    
    # Create tokens directory
    os.makedirs('google_tokens', exist_ok=True)
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        return
    
    # IMPORTANT: Match exactly with Google Console (no trailing slash)
    redirect_uri = 'http://localhost:8000/oauth2callback'  # NO trailing slash!
    
    # Set up OAuth flow
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/calendar'],
        redirect_uri=redirect_uri
    )
    
    # Generate authorization URL
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        state=str(user.id)
    )
    
    print("\n" + "="*50)
    print("STEP 1: Open this URL in your browser:")
    print("="*50)
    print(auth_url)
    print("\n" + "="*50)
    print("STEP 2: After granting permission, you'll be redirected to:")
    print(f"{redirect_uri}?code=...")
    print("="*50)
    print("\nCopy the ENTIRE redirect URL and paste it below:\n")

if __name__ == '__main__':
    test_google_auth()