import requests
import json
from django.conf import settings
import logging

# Set up logging
logger = logging.getLogger(__name__)

def send_email(email_type, recipient, name, details=None):
    """
    Send email via serverless function
    
    Args:
        email_type (str): Type of email (SIGNUP_WELCOME, BOOKING_CONFIRMATION, BOOKING_CANCELLED)
        recipient (str): Email address of recipient
        name (str): Name of recipient
        details (dict): Additional details for email template
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if details is None:
        details = {}
    
    # Get email service URL from settings
    EMAIL_SERVICE_URL = getattr(settings, 'EMAIL_SERVICE_URL', 'http://localhost:3000/send-email')
    
    # Log the attempt
    logger.info(f"📧 Attempting to send {email_type} email to {recipient}")
    print(f"\n🔍 ATTEMPTING TO SEND EMAIL:")
    print(f"   Type: {email_type}")
    print(f"   To: {recipient}")
    print(f"   Name: {name}")
    print(f"   Details: {details}")
    
    # Validate required fields
    if not recipient or not name:
        error_msg = "Missing required fields: recipient and name are required"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False
    
    # Prepare payload
    payload = {
        'email_type': email_type,
        'recipient': recipient,
        'name': name,
        'details': details
    }
    
    try:
        print(f"   POSTing to: {EMAIL_SERVICE_URL}")
        logger.info(f"Sending request to {EMAIL_SERVICE_URL}")
        
        # Call the serverless email service with timeout
        response = requests.post(
            EMAIL_SERVICE_URL,
            json=payload,
            timeout=10,  # 10 second timeout
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Response Status: {response.status_code}")
        print(f"   Response Body: {response.text}")
        logger.info(f"Response status: {response.status_code}")
        
        # Check response
        if response.status_code == 200:
            try:
                response_data = response.json()
                if response_data.get('message'):
                    print(f"✅ {response_data['message']}")
            except:
                pass
            print(f"✅ Email sent successfully to {recipient}")
            logger.info(f"✅ Email sent successfully to {recipient}")
            return True
        else:
            error_msg = f"Email service returned status {response.status_code}"
            print(f"❌ {error_msg}")
            logger.error(f"❌ {error_msg}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        error_msg = "Email service not running! Start with: cd email-service && serverless offline"
        print(f"❌ {error_msg}")
        print("   Make sure serverless is running on http://localhost:3000")
        logger.error(error_msg)
        return False
        
    except requests.exceptions.Timeout:
        error_msg = "Email service timeout after 10 seconds"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return False
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        return False
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        logger.exception("Unexpected error in send_email")
        return False


def test_email_service():
    """Test function to verify email service is working"""
    print("🧪 Testing email service connection...")
    
    try:
        EMAIL_SERVICE_URL = getattr(settings, 'EMAIL_SERVICE_URL', 'http://localhost:3000/send-email')
        response = requests.get(EMAIL_SERVICE_URL.replace('/send-email', ''), timeout=5)
        
        if response.status_code == 200:
            print("✅ Email service is reachable")
            return True
        else:
            print(f"⚠️ Email service returned status {response.status_code}")
            return False
    except:
        print("❌ Email service is not running")
        return False


def get_email_service_status():
    """Get email service status as JSON (for API endpoints)"""
    try:
        EMAIL_SERVICE_URL = getattr(settings, 'EMAIL_SERVICE_URL', 'http://localhost:3000/send-email')
        base_url = EMAIL_SERVICE_URL.replace('/send-email', '')
        response = requests.get(base_url, timeout=5)
        
        return {
            'running': True,
            'status_code': response.status_code,
            'url': EMAIL_SERVICE_URL
        }
    except:
        return {
            'running': False,
            'status_code': None,
            'url': EMAIL_SERVICE_URL,
            'error': 'Service not reachable'
        }
