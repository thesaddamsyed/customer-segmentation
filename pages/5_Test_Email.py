"""
Test Email Page

This page allows testing email functionality with a single test customer.
"""
import os
import streamlit as st
import pandas as pd
import uuid
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Import custom modules
from src.email.email_sender import EmailSender, EmailTemplateManager
from src.email.campaign_manager import CampaignManager

# Set page configuration
st.set_page_config(
    page_title="Test Email - Mall Customer Segmentation",
    page_icon="🧪",
    layout="wide"
)

# Create required directories
os.makedirs("data", exist_ok=True)
os.makedirs("data/campaigns", exist_ok=True)
os.makedirs("data/campaigns/results", exist_ok=True)
os.makedirs("data/email_tracking", exist_ok=True)
os.makedirs("test_data", exist_ok=True)

# Initialize campaign manager
campaign_manager = CampaignManager()

# Custom CSS
def load_css():
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #4527A0;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #5E35B1;
            margin-bottom: 1.5rem;
        }
        .email-preview {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
            border: 1px solid #e0e0e0;
            overflow-wrap: break-word;
            word-wrap: break-word;
        }
        .email-header {
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 1rem;
            margin-bottom: 1rem;
        }
        .email-subject {
            font-weight: bold;
            font-size: 1.2rem;
            color: #333;
            overflow-wrap: break-word;
            word-wrap: break-word;
        }
        .email-from {
            color: #666;
            font-size: 0.9rem;
        }
        .email-to {
            color: #666;
            font-size: 0.9rem;
            overflow-wrap: break-word;
            word-wrap: break-word;
        }
        .email-body {
            padding: 1rem 0;
            overflow-wrap: break-word;
            word-wrap: break-word;
        }
        .info-box {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
        }
        .status-success {
            color: #28a745;
            font-weight: bold;
        }
        .status-error {
            color: #dc3545;
            font-weight: bold;
        }
        .guide-box {
            background-color: #e8f4f8;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            border-left: 5px solid #4285F4;
        }
        .provider-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
            cursor: pointer;
            transition: transform 0.2s;
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        .provider-card:hover {
            transform: translateY(-5px);
        }
        .selected-provider {
            border: 2px solid #4527A0;
        }
        .provider-title {
            font-size: 1.2rem;
            font-weight: bold;
            color: #4527A0;
            margin-bottom: 0.5rem;
        }
        .provider-description {
            font-size: 0.9rem;
            color: #6c757d;
        }
        /* Add spacing to chart containers */
        .chart-container {
            margin-bottom: 2rem;
        }
        /* Override Streamlit default spacing */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 100%;
        }
        /* Fix dataframe overflow */
        .stDataFrame {
            overflow-x: auto;
        }
        /* Ensure text doesn't overflow */
        .text-container {
            overflow-wrap: break-word;
            word-wrap: break-word;
        }
        /* Fix plotly chart overflow */
        .js-plotly-plot {
            overflow: hidden;
        }
    </style>
    """, unsafe_allow_html=True)

# Create email preview
def create_email_preview(template, customer):
    """Create a preview of an email template for a customer."""
    st.subheader("Email Subject")
    subject = template['subject'].format(**customer)
    st.markdown(f"**{subject}**")
    
    st.subheader("Email Body")
    try:
        body_html = template['body_html'].format(**customer)
        st.markdown(body_html, unsafe_allow_html=True)
    except KeyError as e:
        st.error(f"Error in template: Missing field {e}")
        st.markdown(template['body_html'])

def create_test_customer():
    """Create a test customer if none exists."""
    test_file = "test_data/test_customer.csv"
    
    if not os.path.exists(test_file):
        # Create a test customer with a placeholder email
        customer_id = str(uuid.uuid4())
        customer_data = {
            'customer_id': [customer_id],
            'id': [customer_id],
            'email': ['test@example.com'],
            'first_name': ['Test'],
            'last_name': ['User'],
            'age': [35],
            'gender': ['Male'],
            'city': ['Test City'],
            'spending_score': [80],
            'annual_income': [75000],
            'segment_name': ['High Value'],
            'primary_category': ['Electronics'],
            'category': ['Electronics'],
            'recency': [5],
            'frequency': [8],
            'monetary': [1200]
        }
        
        # Create DataFrame and save
        df = pd.DataFrame(customer_data)
        df.to_csv(test_file, index=False)
        return df
    else:
        # Load existing test customer
        return pd.read_csv(test_file)

def main():
    # Load CSS
    load_css()
    
    # Display header
    st.markdown('<h1 class="main-header">Test Email Feature</h1>', unsafe_allow_html=True)
    
    # Create test customer
    test_customer_df = create_test_customer()
    
    # Prepare customer data for email templates
    email_ready_customers = EmailTemplateManager.prepare_customer_data_for_email(test_customer_df)
    test_customer = email_ready_customers.iloc[0].to_dict() if not email_ready_customers.empty else {}
    
    # Display test customer info
    st.markdown('<h2 class="sub-header">Test Customer Details</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.text_input("Customer ID", test_customer.get('customer_id', ''), disabled=True)
        email = st.text_input("Email Address", test_customer.get('email', 'test@example.com'))
        first_name = st.text_input("First Name", test_customer.get('first_name', 'Test'))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        segment_name = st.selectbox(
            "Customer Segment", 
            ["High Value", "Low Value", "Standard", "VIP"],
            index=0
        )
        primary_category = st.selectbox(
            "Primary Category",
            ["Electronics", "Clothing", "Home Goods", "Food", "Beauty"],
            index=0
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Update test customer with form values
    if st.button("Update Test Customer"):
        # Update values
        test_customer_df.at[0, 'email'] = email
        test_customer_df.at[0, 'first_name'] = first_name
        test_customer_df.at[0, 'segment_name'] = segment_name
        test_customer_df.at[0, 'primary_category'] = primary_category
        test_customer_df.at[0, 'category'] = primary_category
        
        # Save updated customer
        test_customer_df.to_csv("test_data/test_customer.csv", index=False)
        
        # Update test customer dict
        email_ready_customers = EmailTemplateManager.prepare_customer_data_for_email(test_customer_df)
        test_customer = email_ready_customers.iloc[0].to_dict()
        
        st.success("Test customer updated successfully!")
        st.rerun()
    
    # Email Configuration Section
    st.markdown('<h2 class="sub-header">Email Configuration</h2>', unsafe_allow_html=True)
    
    # Add email provider guide
    with st.expander("How to Set Up Email Providers (Gmail, Outlook, etc.)", expanded=True):
        st.markdown('<div class="guide-box">', unsafe_allow_html=True)
        st.markdown("""
        ## Gmail Setup Guide
        
        Since you're using a Gmail account, you need to create an **App Password** instead of using your regular password:
        
        ### Step 1: Enable 2-Step Verification
        1. Go to your [Google Account](https://myaccount.google.com/)
        2. Select **Security** from the left menu
        3. Under "Signing in to Google," select **2-Step Verification** → **Get started**
        4. Follow the on-screen steps to enable it
        
        ### Step 2: Create an App Password
        1. Go back to the [Security](https://myaccount.google.com/security) page
        2. Under "Signing in to Google," select **App passwords** (you might need to sign in again)
        3. At the bottom, select **Select app** → **Mail**
        4. Select **Select device** → **Other**
        5. Enter "Mall Customer Segmentation" → **Generate**
        6. Google will display a 16-character App Password
        7. Copy this password and use it below (NO SPACES NEEDED)
        8. Click **Done**
        
        ### Step 3: Configure Email Settings
        - **SMTP Host**: smtp.gmail.com
        - **SMTP Port**: 465 (recommended SSL connection)
        - **SMTP Username**: Your full Gmail address
        - **SMTP Password**: The 16-character App Password (no spaces)
        
        ### Common Issues & Solutions:
        - If you see "Username and Password not accepted" error, verify you've copied the App Password correctly with no spaces
        - If you see "Application-specific password required", this confirms you need an App Password
        - Try using port 465 with SSL instead of port 587 with TLS as Gmail prefers this method
        - Make sure you're using the correct Gmail address that generated the App Password
        - If issues persist, try generating a new App Password
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="guide-box">', unsafe_allow_html=True)
        st.markdown("""
        ## Outlook/Hotmail Setup Guide
        
        ### Configure Email Settings
        - **SMTP Host**: smtp.office365.com
        - **SMTP Port**: 587
        - **SMTP Username**: Your full Outlook/Hotmail email address
        - **SMTP Password**: Your account password
        
        If you have 2-factor authentication enabled, you'll need to create an app password:
        1. Sign in to your Microsoft account at [account.microsoft.com](https://account.microsoft.com/)
        2. Go to **Security** → **Advanced security options**
        3. Under **App passwords**, select **Create a new app password**
        4. Use this app password instead of your regular password
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="guide-box">', unsafe_allow_html=True)
        st.markdown("""
        ## Yahoo Mail Setup Guide
        
        ### Configure Email Settings
        - **SMTP Host**: smtp.mail.yahoo.com
        - **SMTP Port**: 587
        - **SMTP Username**: Your full Yahoo email address
        - **SMTP Password**: Your app password (not your regular Yahoo password)
        
        To generate an app password:
        1. Sign in to your Yahoo account
        2. Go to **Account Info** → **Account Security**
        3. Click **Generate app password**
        4. Select **Other app** and name it "Mall Customer Segmentation"
        5. Copy the app password and use it here
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Check if .env file exists
    if os.path.exists(".env"):
        load_dotenv()
        
        # Get email configuration from .env
        email_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        email_port = int(os.getenv("EMAIL_PORT", "587"))
        email_user = os.getenv("EMAIL_USER", "")
        email_password = os.getenv("EMAIL_PASSWORD", "")
        
        # Display current configuration
        st.info(f"Using saved email configuration for {email_user}")
        
        # Allow updating configuration
        st.markdown("### Update Email Configuration")
        
        # Email provider selection
        email_provider = st.selectbox(
            "Email Provider",
            ["Gmail", "Outlook", "Yahoo", "Custom"],
            index=0 if "gmail" in email_host else (1 if "office365" in email_host else (2 if "yahoo" in email_host else 3))
        )
        
        # Set host and port based on provider
        if email_provider == "Gmail":
            new_email_host = "smtp.gmail.com"
            new_email_port = 465
        elif email_provider == "Outlook":
            new_email_host = "smtp.office365.com"
            new_email_port = 587
        elif email_provider == "Yahoo":
            new_email_host = "smtp.mail.yahoo.com"
            new_email_port = 587
        else:
            new_email_host = st.text_input("SMTP Host", email_host)
            new_email_port = st.number_input("SMTP Port", value=email_port)
            
        # Email credentials
        new_email_user = st.text_input("SMTP Username (Email Address)", email_user)
        new_email_password = st.text_input("SMTP Password (App Password for Gmail/Yahoo)", type="password")
        
        # Save configuration button
        if st.button("Update Email Configuration"):
            # Create .env file with new configuration
            with open(".env", "w") as f:
                f.write(f"EMAIL_HOST={new_email_host}\n")
                f.write(f"EMAIL_PORT={new_email_port}\n")
                f.write(f"EMAIL_USER={new_email_user}\n")
                f.write(f"EMAIL_PASSWORD={new_email_password}\n")
            
            st.success("Email configuration updated successfully!")
            st.rerun()
    else:
        st.warning("No saved email configuration found. Please set up your email configuration below.")
        
        # Email provider selection
        email_provider = st.selectbox(
            "Email Provider",
            ["Gmail", "Outlook", "Yahoo", "Custom"],
            index=0
        )
        
        # Set host and port based on provider
        if email_provider == "Gmail":
            email_host = "smtp.gmail.com"
            email_port = 465
        elif email_provider == "Outlook":
            email_host = "smtp.office365.com"
            email_port = 587
        elif email_provider == "Yahoo":
            email_host = "smtp.mail.yahoo.com"
            email_port = 587
        else:
            email_host = st.text_input("SMTP Host", "smtp.example.com")
            email_port = st.number_input("SMTP Port", value=587)
            
        # Email credentials
        email_user = st.text_input("SMTP Username (Email Address)")
        email_password = st.text_input("SMTP Password (App Password for Gmail/Yahoo)", type="password")
        st.caption("For Gmail, use an App Password as described in the guide above.")
        
        # Save configuration button
        if st.button("Save Email Configuration"):
            if not email_user or not email_password:
                st.error("Please provide both username and password.")
            else:
                # Create .env file
                with open(".env", "w") as f:
                    f.write(f"EMAIL_HOST={email_host}\n")
                    f.write(f"EMAIL_PORT={email_port}\n")
                    f.write(f"EMAIL_USER={email_user}\n")
                    f.write(f"EMAIL_PASSWORD={email_password}\n")
                
                st.success("Email configuration saved successfully!")
                st.rerun()
    
    # Test Email Section
    st.markdown('<h2 class="sub-header">Send Test Email</h2>', unsafe_allow_html=True)
    
    # Check if email is configured
    if not os.path.exists(".env") or not email_user or not email_password:
        st.warning("⚠️ Please configure your email provider before sending test emails.")
    
    # Email content
    st.markdown("### Email Content")
    
    # Email template
    email_subject = st.text_input(
        "Email Subject",
        "Special Offer for {first_name}!"
    )
    
    email_body = st.text_area(
        "Email Body (HTML)",
        """
        <html>
        <body>
            <h1>Hello {first_name},</h1>
            <p>We have a special offer just for you as a <b>{segment_name}</b> customer!</p>
            <p>Visit our store to enjoy exclusive discounts on {primary_category} products.</p>
            <p>Check out our <a href="https://www.example.com/products">latest products</a>!</p>
            <p>Best regards,<br>The Mall Team</p>
        </body>
        </html>
        """,
        height=200
    )
    
    # Create template dict
    test_template = {
        'subject': email_subject,
        'body_html': email_body
    }
    
    # Show preview
    st.markdown("### Email Preview")
    create_email_preview(test_template, test_customer)
    
    # Verify connection before sending
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Verify Email Connection"):
            if not os.path.exists(".env") or not email_user or not email_password:
                st.error("Please configure your email provider first.")
            else:
                try:
                    with st.spinner("Testing email connection..."):
                        # Test connection based on port
                        try:
                            if email_port == 465:
                                # Use SSL
                                import smtplib
                                server = smtplib.SMTP_SSL(email_host, email_port)
                                status = "Connected to server using SSL"
                            else:
                                # Use TLS
                                import smtplib
                                server = smtplib.SMTP(email_host, email_port)
                                server.ehlo()
                                server.starttls()
                                server.ehlo()
                                status = "Connected to server using TLS"
                            
                            # Try to login
                            st.info(status)
                            server.login(email_user, email_password)
                            server.quit()
                            
                            st.success(f"✅ Email connection successful! Your configuration is working correctly.")
                            
                            # Show the actual configuration being used (helpful for debugging)
                            with st.expander("Connection Details"):
                                st.code(f"""
Host: {email_host}
Port: {email_port}
Username: {email_user}
SSL/TLS: {"SSL" if email_port == 465 else "TLS"}
                                """)
                            
                        except Exception as e:
                            error_msg = str(e)
                            st.error(f"❌ Email connection failed: {error_msg}")
                            
                            # Provide specific guidance based on error
                            if "Application-specific password required" in error_msg:
                                st.warning("""
                                Gmail requires an **App Password**. Please make sure:
                                1. You have 2-Step Verification enabled
                                2. You're using an App Password (not your regular Gmail password)
                                3. The App Password is entered without spaces
                                """)
                            elif "Username and Password not accepted" in error_msg:
                                st.warning("""
                                Authentication failed. Please check:
                                1. Your email address is correct
                                2. App Password is entered correctly (no spaces)
                                3. Try generating a new App Password
                                """)
                            elif "Connection refused" in error_msg:
                                st.warning(f"""
                                Connection to {email_host}:{email_port} refused. Please check:
                                1. The host and port are correct
                                2. Your network allows SMTP connections
                                3. Try the alternative port: {"587 (TLS)" if email_port == 465 else "465 (SSL)"}
                                """)
                
                except Exception as e:
                    st.error(f"Error sending email: {str(e)}")
                    st.markdown("""
                    ### Troubleshooting Email Errors
                    
                    Common errors:
                    - **Authentication failed**: Check your username and password
                    - **Gmail users**: Make sure you're using an App Password, not your regular password
                    - **Security settings**: Your email provider might be blocking the connection
                    - **Network issues**: Your network might be restricting outgoing SMTP connections
                    """)
    
    with col2:
        # Send test email
        if st.button("Send Test Email"):
            if not os.path.exists(".env") or not email_user or not email_password:
                st.error("Please configure your email provider first.")
            elif not test_customer.get('email'):
                st.error("Please provide a valid email address for the test customer.")
            else:
                # Create a test campaign
                campaign_id = campaign_manager.create_campaign(
                    campaign_name=f"Test Campaign {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    campaign_type="Test",
                    target_description="Single test customer",
                    templates={"custom": test_template},
                    target_data={
                        'target_type': "Test",
                        'count': 1,
                        'details': "Test email",
                        'customer_ids': [test_customer.get('customer_id')]
                    },
                    email_config={
                        'host': email_host,
                        'port': email_port,
                        'username': email_user,
                        'password': email_password,
                        'test_mode': False,
                        'max_emails': 1
                    }
                )
                
                # Create email sender
                try:
                    with st.spinner("Sending test email..."):
                        # Load configuration
                        load_dotenv()
                        host = os.getenv("EMAIL_HOST")
                        port = int(os.getenv("EMAIL_PORT"))
                        user = os.getenv("EMAIL_USER")
                        password = os.getenv("EMAIL_PASSWORD")
                        
                        email_sender = EmailSender(
                            host=host,
                            port=port,
                            username=user,
                            password=password,
                            enable_tracking=True
                        )
                        
                        # Format template with customer data
                        subject = email_subject.format(**test_customer)
                        body_html = email_body.format(**test_customer)
                        
                        # Send email
                        success = email_sender.send_email(
                            to_email=test_customer['email'],
                            subject=subject,
                            body_html=body_html,
                            campaign_id=campaign_id,
                            customer_id=test_customer['customer_id']
                        )
                        
                        # Update campaign status
                        if success:
                            campaign_manager.update_campaign_status(
                                campaign_id=campaign_id,
                                status="Executed",
                                results={
                                    'emails_sent': 1,
                                    'emails_opened': 0,
                                    'emails_clicked': 0,
                                    'test_mode': False,
                                    'details': [{'email': test_customer['email'], 'status': 'sent'}]
                                }
                            )
                            st.success(f"✅ Test email sent successfully to {test_customer['email']}!")
                            st.markdown("### What's Next?")
                            st.markdown("""
                            1. Check your email inbox for the test message
                            2. Open the email to track an "open" event
                            3. Click any links to track "click" events
                            4. Go to the [Email Tracking](/Email_Tracking) page to see your results
                            """)
                        else:
                            campaign_manager.update_campaign_status(
                                campaign_id=campaign_id,
                                status="Failed",
                                results={'error': "Failed to send email"}
                            )
                            st.error(f"Failed to send test email to {test_customer['email']}.")
                
                except Exception as e:
                    st.error(f"Error sending email: {str(e)}")
                    st.markdown("""
                    ### Troubleshooting Email Errors
                    
                    Common errors:
                    - **Authentication failed**: Check your username and password
                    - **Gmail users**: Make sure you're using an App Password, not your regular password
                    - **Security settings**: Your email provider might be blocking the connection
                    - **Network issues**: Your network might be restricting outgoing SMTP connections
                    """)

if __name__ == "__main__":
    main() 