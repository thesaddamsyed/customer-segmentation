"""
Test script to verify email sending functionality.
"""
import os
import sys
import time
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Set up logging to show all messages
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

def load_env_file():
    """Load environment variables from .env file manually."""
    env_vars = {}
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    env_vars[key] = value
        return env_vars
    except Exception as e:
        print(f"Error loading .env file: {e}")
        return {}

def test_email_sending():
    """
    Test email sending functionality with the current configuration.
    """
    print("\n===== EMAIL SENDING TEST =====\n")
    
    # Load environment variables
    print("Loading environment variables from .env file...")
    env_vars = load_env_file()
    
    # Get email configuration from .env
    email_host = env_vars.get("EMAIL_HOST", "smtp.gmail.com")
    email_port = int(env_vars.get("EMAIL_PORT", "465"))
    email_user = env_vars.get("EMAIL_USER", "")
    email_password = env_vars.get("EMAIL_PASSWORD", "")
    
    print(f"\nEmail configuration:")
    print(f"Host: {email_host}")
    print(f"Port: {email_port}")
    print(f"User: {email_user}")
    print(f"Password length: {len(email_password) if email_password else 0}")
    
    if not email_user or not email_password:
        print("Error: Missing email username or password in .env file")
        return False
    
    # Test connection
    print("\nTesting connection...")
    try:
        print(f"Connecting to {email_host}:{email_port} with SSL...")
        server = smtplib.SMTP_SSL(email_host, email_port)
        
        print(f"Authenticating as {email_user}...")
        server.login(email_user, email_password)
        
        print("Authentication successful!")
        server.quit()
        
        print("Connection test successful!")
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
    
    # Get recipient email
    recipient = input("\nEnter recipient email address (press Enter to use your own email): ").strip()
    if not recipient:
        recipient = email_user
        print(f"Using {email_user} as recipient")
    
    # Send test email
    print(f"\nSending test email to {recipient}...")
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Test Email from Customer Segmentation App"
        msg['From'] = email_user
        msg['To'] = recipient
        
        body_html = """<html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #4527A0;">Test Email</h2>
            <p>Your email configuration is working correctly!</p>
            <p>This is a test email sent from the Customer Segmentation app.</p>
            <p>Best regards,<br>Customer Segmentation App</p>
        </body>
        </html>"""
        
        html_part = MIMEText(body_html, 'html')
        msg.attach(html_part)
        
        # Connect to server
        server = smtplib.SMTP_SSL(email_host, email_port)
        server.login(email_user, email_password)
        
        # Send email
        server.sendmail(email_user, recipient, msg.as_string())
        server.quit()
        
        print("\n✅ Success! The email was sent correctly.")
        print("If you don't see the email in your inbox, check your spam folder.")
        return True
    except Exception as e:
        print(f"\n❌ Exception while sending email: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        result = test_email_sending()
        print("\n===== TEST COMPLETE =====")
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 