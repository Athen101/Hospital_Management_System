import os
import pickle
import re
import urllib.parse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

def handle_callback():
    """Manually handle OAuth callback with better error handling"""
    
    print("\n" + "="*60)
    print("Google OAuth Callback Handler")
    print("="*60)
    
    # Ask for the redirect URL
    print("\n1. Open the authorization URL in your browser")
    print("2. Grant permissions")
    print("3. Copy the ENTIRE redirect URL from your browser's address bar")
    print("\nPaste the redirect URL here:")
    redirect_url = input().strip()
    
    # Parse the URL to extract parameters
    parsed = urllib.parse.urlparse(redirect_url)
    params = urllib.parse.parse_qs(parsed.query)
    
    code = params.get('code', [None])[0]
    state = params.get('state', [None])[0]
    
    if not code:
        print("\n❌ ERROR: No authorization code found in the URL!")
        print("The URL should contain 'code=...' parameter")
        return
    
    print(f"\n✓ Authorization code extracted successfully")
    print(f"✓ State parameter: {state}")
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("\n❌ ERROR: credentials.json not found!")
        return
    
    # Set up OAuth flow
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/calendar'],
        redirect_uri='http://localhost:8000/oauth2callback/'
    )
    
    try:
        # Exchange code for credentials
        print("\n⏳ Exchanging code for tokens...")
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Save credentials
        os.makedirs('google_tokens', exist_ok=True)
        token_path = f'google_tokens/{state}_token.pickle'
        
        with open(token_path, 'wb') as token:
            pickle.dump(credentials, token)
        
        print(f"✅ Google Calendar connected successfully!")
        print(f"✓ Token saved to: {token_path}")
        
        # Test the connection
        from googleapiclient.discovery import build
        service = build('calendar', 'v3', credentials=credentials)
        
        # Get calendar list to test
        calendar_list = service.calendarList().list().execute()
        print(f"✓ Connected to calendar: {calendar_list['items'][0]['summary']}")
        
        # List next 5 events
        events_result = service.events().list(
            calendarId='primary',
            maxResults=5,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        print(f"✓ Found {len(events)} upcoming events")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nPossible reasons:")
        print("- The authorization code was already used")
        print("- The code expired (they expire quickly)")
        print("- The redirect URI doesn't match")
        print("\nTry running test_calender.py again to get a new code")

if __name__ == '__main__':
    handle_callback()