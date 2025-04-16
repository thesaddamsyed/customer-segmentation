import os
import smtplib

def check_and_fix_config():
    print("Email Configuration Verification")
    print("===============================")
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("❌ .env file not found. Creating a new one with correct settings.")
        create_new_config()
        return
    
    # Load current settings manually
    settings = {}
    try:
        with open(".env", "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    settings[key] = value
    except Exception as e:
        print(f"Error reading .env file: {e}")
        create_new_config()
        return
    
    # Get current settings
    email_host = settings.get("EMAIL_HOST", "")
    email_port = settings.get("EMAIL_PORT", "")
    email_user = settings.get("EMAIL_USER", "")
    email_password = settings.get("EMAIL_PASSWORD", "")
    
    # Check settings
    needs_update = False
    
    # Check host
    if email_host != "smtp.gmail.com":
        print(f"❌ Host is incorrect: {email_host}")
        email_host = "smtp.gmail.com"
        needs_update = True
    else:
        print(f"✓ Host is correct: {email_host}")
    
    # Check port
    if email_port != "465":
        print(f"❌ Port is incorrect: {email_port}")
        email_port = "465"
        needs_update = True
    else:
        print(f"✓ Port is correct: {email_port}")
    
    # Check username
    if email_user.lower() == "himowachk@gmail.com":
        print(f"❌ Email has a typo: {email_user}")
        email_user = "himowahck@gmail.com"
        needs_update = True
    elif email_user.lower() != "himowahck@gmail.com":
        print(f"❌ Email is incorrect: {email_user}")
        email_user = "himowahck@gmail.com"
        needs_update = True
    else:
        print(f"✓ Email is correct: {email_user}")
    
    # Check password (without displaying it)
    if email_password != "ngdjxropnixsftal":
        print("❌ Password is incorrect or outdated")
        email_password = "ngdjxropnixsftal"
        needs_update = True
    else:
        print("✓ Password is correct")
    
    # Update if needed
    if needs_update:
        print("\nUpdating configuration...")
        create_new_config(email_host, email_port, email_user, email_password)
    else:
        print("\nAll settings are correct!")
    
    # Test connection
    test_connection(email_host, int(email_port), email_user, email_password)

def create_new_config(host="smtp.gmail.com", port="465", user="himowahck@gmail.com", password="ngdjxropnixsftal"):
    """Create a new .env file with the correct settings."""
    env_content = f"""EMAIL_HOST={host}
EMAIL_PORT={port}
EMAIL_USER={user}
EMAIL_PASSWORD={password}
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
"""
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✓ Created new .env file with correct settings")

def test_connection(host, port, user, password):
    """Test the email connection."""
    print("\nTesting connection to Gmail...")
    
    try:
        # Create SSL connection
        server = smtplib.SMTP_SSL(host, port)
        
        # Login
        server.login(user, password)
        
        # Close connection
        server.quit()
        
        print("✓ Connection successful!")
        print("\nYour email configuration is now correct and should work in the application.")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nPlease check your internet connection and try again.")

if __name__ == "__main__":
    check_and_fix_config() 