from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import pickle
import json

def final_oauth_fixed():
    """OAuth test that shows you exactly what URIs are configured"""
    
    print("="*60)
    print("Google Calendar OAuth - Diagnostic Mode")
    print("="*60)
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("❌ ERROR: credentials.json not found!")
        print("Please download it from Google Cloud Console and place it here:")
        print(os.getcwd())
        return
    
    print("✓ credentials.json found")
    
    # Read and display the redirect URIs from credentials file
    with open('credentials.json', 'r') as f:
        creds_data = json.load(f)
    
    redirect_uris = creds_data.get('web', {}).get('redirect_uris', [])
    
    print("\n📋 Redirect URIs configured in your credentials.json:")
    for i, uri in enumerate(redirect_uris, 1):
        print(f"   {i}. {uri}")
    
    if not redirect_uris:
        print("   ⚠️  No redirect URIs found in credentials.json!")
        print("\nPlease add redirect URIs in Google Cloud Console:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Click on your OAuth 2.0 Client ID")
        print("3. Add http://localhost:8080/ to 'Authorized redirect URIs'")
        print("4. Click Save and download the JSON again")
        return
    
    # Try each redirect URI
    print("\n🔄 Attempting authentication with each redirect URI...")
    
    for redirect_uri in redirect_uris:
        print(f"\n--- Trying: {redirect_uri} ---")
        
        try:
            # Create flow with this specific redirect URI
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            
            # Override the redirect URI
            flow.redirect_uri = redirect_uri
            
            # Extract port from redirect URI
            import re
            port_match = re.search(r':(\d+)', redirect_uri)
            if port_match:
                port = int(port_match.group(1))
            else:
                port = 8080
            
            print(f"   Using port: {port}")
            print("   Opening browser...")
            
            # Run local server
            credentials = flow.run_local_server(
                host='localhost',
                port=port,
                open_browser=True
            )
            
            # If we get here, it worked!
            print(f"\n✅ SUCCESS with redirect URI: {redirect_uri}")
            
            # Save the credentials
            os.makedirs('google_tokens', exist_ok=True)
            token_path = 'google_tokens/calendar_token.pickle'
            with open(token_path, 'wb') as token_file:
                pickle.dump(credentials, token_file)
            
            print(f"✓ Token saved to: {token_path}")
            
            # Test connection
            service = build('calendar', 'v3', credentials=credentials)
            calendar = service.calendars().get(calendarId='primary').execute()
            print(f"✓ Connected to calendar: {calendar['summary']}")
            
            print("\n✅ Google Calendar is ready to use!")
            return
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:100]}...")
            continue
    
    print("\n❌ All redirect URIs failed.")
    print("\nPlease update your Google Cloud Console:")
    print("1. Go to https://console.cloud.google.com/apis/credentials")
    print("2. Edit your OAuth 2.0 Client ID")
    print("3. Under 'Authorized redirect URIs', add BOTH:")
    print("   - http://localhost:8000/oauth2callback")
    print("   - http://localhost:8080/")
    print("   - http://localhost:8080")
    print("4. Click SAVE")
    print("5. Download the JSON again and replace credentials.json")
    print("6. Run this script again")

if __name__ == '__main__':
    final_oauth_fixed()