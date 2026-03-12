import requests
import json
from django.conf import settings

def send_email(email_type, recipient, name, details=None):
    """
    Send email via serverless function
    """
    if details is None:
        details = {}
    
    # Email service URL
    EMAIL_SERVICE_URL = 'http://localhost:3000/send-email'
    
    print(f"\n🔍 ATTEMPTING TO SEND EMAIL:")
    print(f"   Type: {email_type}")
    print(f"   To: {recipient}")
    print(f"   Name: {name}")
    print(f"   Details: {details}")
    
    try:
        payload = {
            'email_type': email_type,
            'recipient': recipient,
            'name': name,
            'details': details
        }
        
        print(f"   POSTing to: {EMAIL_SERVICE_URL}")
        
        # Call the serverless email service
        response = requests.post(
            EMAIL_SERVICE_URL,
            json=payload,
            timeout=10
        )
        
        print(f"   Response Status: {response.status_code}")
        print(f"   Response Body: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Email sent successfully to {recipient}")
            return True
        else:
            print(f"❌ Email failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Email service not running! Start with: cd email-service && serverless offline")
        print("   Make sure serverless is running on http://localhost:3000")
        return False
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False