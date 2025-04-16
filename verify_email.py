"""
Verify Email Functionality

This script tests the email sending functionality with the current configuration.
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import sys

def test_email_connection():
    """Test email connection and sending a test email"""
    print("\n===== EMAIL CONNECTION TEST =====\n")
    
    # Load environment variables
    print("Loading environment variables from .env file...")
    load_dotenv(override=True)
    
    # Get email configuration from .env
    email_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    email_port = int(os.getenv("EMAIL_PORT", "465"))
    email_user = os.getenv("EMAIL_USER", "")
    email_password = os.getenv("EMAIL_PASSWORD", "")
    
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
        
        # Ask for recipient email
        recipient = input("\nEnter recipient email address (press Enter to use your own email): ").strip()
        if not recipient:
            recipient = email_user
            print(f"Using {email_user} as recipient")
        
        # Create a test email
        print(f"\nSending test email to {recipient}...")
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Test Email from Customer Segmentation App"
        msg['From'] = email_user
        msg['To'] = recipient
        
        body_text = "This is a test email from the Customer Segmentation application."
        body_html = """
        <html>
        <body>
            <h1>Test Email</h1>
            <p>This is a test email from the Customer Segmentation application.</p>
            <p>If you received this, the email functionality is working properly.</p>
            <p>Timestamp: """ + str(os.times()) + """</p>
        </body>
        </html>
        """
        
        text_part = MIMEText(body_text, 'plain')
        html_part = MIMEText(body_html, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send the email
        server.sendmail(email_user, recipient, msg.as_string())
        
        print("Test email sent successfully!")
        server.quit()
        
        print("\nConnection and email test successful!")
        return True
        
    except Exception as e:
        print(f"Email test failed: {str(e)}")
        print("\nPossible causes:")
        print("1. Incorrect email/password in .env file")
        print("2. Less secure app access is disabled for Gmail (use App Password instead)")
        print("3. Network or firewall issues")
        print("4. SMTP server restrictions")
        return False

def check_gmail_setup():
    """Check if Gmail configuration is set up correctly"""
    email_user = os.getenv("EMAIL_USER", "")
    
    if "gmail.com" in email_user.lower():
        print("\n===== GMAIL CONFIGURATION CHECK =====\n")
        print("You are using a Gmail account. Make sure you have:")
        print("1. Enabled 2-Step Verification for your Google account")
        print("2. Created an App Password:")
        print("   - Go to your Google Account → Security → App Passwords")
        print("   - Select 'Mail' as the app and your device")
        print("   - Use the generated 16-character password in your .env file")
        print("3. Make sure the password in .env does NOT have spaces")
        print("\nFor more information, visit: https://support.google.com/accounts/answer/185833")

if __name__ == "__main__":
    # Check if Gmail is being used
    load_dotenv(override=True)
    check_gmail_setup()
    
    # Run email test
    success = test_email_connection()
    
    if not success:
        print("\nEmail functionality test FAILED.")
        sys.exit(1)
    else:
        print("\nEmail functionality test PASSED.")
        sys.exit(0) 