from google_auth_oauthlib.flow import InstalledAppFlow
import os
import pickle

print("="*50)
print("Google Calendar Authentication (Port 8000)")
print("="*50)

# Use port 8000 to match your credentials
flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json',
    scopes=['https://www.googleapis.com/auth/calendar']
)

try:
    credentials = flow.run_local_server(
        host='localhost',
        port=8000,
        open_browser=True,
        success_message='✅ Authentication successful! You can close this window.'
    )
    
    # Save the credentials
    os.makedirs('google_tokens', exist_ok=True)
    with open('google_tokens/calendar_token.pickle', 'wb') as f:
        pickle.dump(credentials, f)
    
    print("\n✅ SUCCESS! Google Calendar connected!")
    print(f"✓ Token saved to: google_tokens/calendar_token.pickle")
    
    # Test the connection
    from googleapiclient.discovery import build
    service = build('calendar', 'v3', credentials=credentials)
    calendar = service.calendars().get(calendarId='primary').execute()
    print(f"✓ Connected to calendar: {calendar['summary']}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nMake sure you're signed into the correct Google account")