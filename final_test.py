import smtplib

# Correct credentials from user
email = "himowahck@gmail.com"
password = "ngdjxropnixsftal"

print(f"Testing Gmail connection with {email}")

try:
    # Connect with SSL
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    
    # Login
    server.login(email, password)
    
    # If login successful, send test email
    server.sendmail(
        email, 
        email,  # Send to self
        "Subject: Test Email\n\nThis is a test email to verify Gmail connection."
    )
    
    # Close connection
    server.quit()
    
    print("SUCCESS! Authentication worked correctly.")
    print("An email has been sent to your inbox.")
    
    print("\nUse these EXACT credentials in your application:")
    print(f"Email: {email}")
    print(f"Password: {password}")
    
except Exception as e:
    print(f"ERROR: {e}")
    
    if "Username and Password not accepted" in str(e):
        print("\nAuthentication failed. Check that:")
        print("1. You're using the correct email address")
        print("2. The App Password is correct (no typos)")
        print("3. 2-Step Verification is enabled on your account")
    else:
        print(f"\nConnection error: {e}")

print("\nCritical note: The application logs show it was trying to use 'himowachk@gmail.com'")
print("instead of your correct email 'himowahck@gmail.com'. This typo is the likely issue.") 