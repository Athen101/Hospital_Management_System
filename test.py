import requests
import json

def test_email_service():
    """Directly test the email service"""
    
    email_service_url = 'http://localhost:3000/send-email'
    
    payload = {
        'email_type': 'BOOKING_CONFIRMATION',
        'recipient': 'your-email@gmail.com',  # Replace with your email
        'name': 'Test User',
        'details': {
            'doctor_name': 'Dr. Smith',
            'patient_name': 'Test Patient',
            'date': '2026-03-15',
            'time': '10:00 AM - 11:00 AM',
            'specialization': 'Cardiology'
        }
    }
    
    try:
        print(f"Sending test email to {payload['recipient']}...")
        response = requests.post(email_service_url, json=payload, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Email service is working!")
        else:
            print("❌ Email service returned error")
            
    except requests.exceptions.ConnectionError:
        print("❌ Email service not running! Start with: serverless offline")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_email_service()