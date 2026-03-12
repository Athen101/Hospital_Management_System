from google_auth_oauthlib.flow import Flow
import os
import pickle
import json

print("="*60)
print("FINAL FIX - EXPLICIT REDIRECT URI")
print("="*60)

# Load credentials
with open('credentials.json', 'r') as f:
    client_config = json.load(f)

# The exact redirect URI from your credentials
REDIRECT_URI = 'http://localhost:8000/oauth2callback'
print(f"📋 Using exact redirect URI: {REDIRECT_URI}")

# Create flow with explicit redirect URI
flow = Flow.from_client_secrets_file(
    'credentials.json',
    scopes=['https://www.googleapis.com/auth/calendar'],
    redirect_uri=REDIRECT_URI
)

# Generate authorization URL
auth_url, _ = flow.authorization_url(
    access_type='offline',
    include_granted_scopes='true',
    prompt='consent'
)

print("\n🔗 STEP 1: Open this URL in your browser:")
print("="*80)
print(auth_url)
print("="*80)
print("\n🔑 STEP 2: Sign in with adithyasree341@gmail.com")
print("✅ STEP 3: Click 'Allow'")
print("📋 STEP 4: AFTER allowing, you'll see a localhost error page")
print("📋 STEP 5: Copy the ENTIRE URL from that error page")
print("\nPaste the redirect URL here:")

# Get the redirect URL from user
redirect_url = input().strip()

# Extract the code
from urllib.parse import urlparse, parse_qs
parsed = urlparse(redirect_url)
code = parse_qs(parsed.query).get('code', [None])[0]

if code:
    print(f"\n✅ Code extracted successfully!")
    
    # Exchange code for token
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    # Save token
    os.makedirs('google_tokens', exist_ok=True)
    token_path = 'google_tokens/calendar_token.pickle'
    with open(token_path, 'wb') as f:
        pickle.dump(credentials, f)
    
    print(f"✅ Token saved to: {token_path}")
    
    # Test connection
    from googleapiclient.discovery import build
    service = build('calendar', 'v3', credentials=credentials)
    calendar = service.calendars().get(calendarId='primary').execute()
    print(f"✅ Connected to calendar: {calendar['summary']}")
    
    print("\n" + "="*60)
    print("SUCCESS! Google Calendar is ready!")
    print("="*60)
else:
    print("❌ No code found in URL!")