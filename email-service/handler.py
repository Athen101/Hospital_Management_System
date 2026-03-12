import json
import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def send_email(event, context):
    """Lambda function to send emails"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        email_type = body.get('email_type')
        recipient = body.get('recipient')
        name = body.get('name')
        details = body.get('details', {})
        
        # Validate required fields
        if not all([email_type, recipient, name]):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Missing required fields'})
            }
        
        # Get SMTP settings from environment
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        
        if not smtp_username or not smtp_password:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'SMTP credentials not configured'})
            }
        
        # Create email content based on type
        if email_type == 'SIGNUP_WELCOME':
            subject = f"Welcome to Hospital Management System, {name}!"
            html_content = f"""
            <html>
                <body>
                    <h2>Welcome to HMS!</h2>
                    <p>Dear {name},</p>
                    <p>Thank you for registering with Hospital Management System.</p>
                    <p>You can now log in and start using our services.</p>
                    <p>Best regards,<br>HMS Team</p>
                </body>
            </html>
            """
        elif email_type == 'BOOKING_CONFIRMATION':
            subject = f"Appointment Confirmation - Dr. {details.get('doctor_name')}"
            html_content = f"""
            <html>
                <body>
                    <h2>Appointment Confirmed!</h2>
                    <p>Dear {name},</p>
                    <p>Your appointment has been confirmed:</p>
                    <ul>
                        <li><strong>Doctor:</strong> Dr. {details.get('doctor_name')}</li>
                        <li><strong>Date:</strong> {details.get('date')}</li>
                        <li><strong>Time:</strong> {details.get('time')}</li>
                    </ul>
                    <p>Best regards,<br>HMS Team</p>
                </body>
            </html>
            """
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Invalid email type: {email_type}'})
            }
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))
        
        # Send email with shorter timeout
        logger.info(f"Sending {email_type} email to {recipient}")
        
        # Use a try-except specifically for SMTP
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)  # Add timeout
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            server.quit()
            logger.info(f"✅ Email sent successfully to {recipient}")
        except smtplib.SMTPAuthenticationError:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'SMTP authentication failed. Check your email/password.'})
            }
        except Exception as smtp_error:
            logger.error(f"SMTP error: {str(smtp_error)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'SMTP error: {str(smtp_error)}'})
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Email sent successfully',
                'recipient': recipient
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }