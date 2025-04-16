"""
Test Email Campaign

This page allows users to send test email campaigns to the test customers
based on segment or product category.
"""
import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
import json
import smtplib

# Import custom modules
from src.email.email_sender import EmailSender, EmailTemplateManager
from src.email.campaign_manager import CampaignManager
from dotenv import load_dotenv

# Set page configuration
st.set_page_config(
    page_title="Test Email Campaign - Mall Customer Segmentation",
    page_icon="📧",
    layout="wide"
)

# Initialize session state variables
if 'campaign_setup_complete' not in st.session_state:
    st.session_state.campaign_setup_complete = False
if 'campaign_id' not in st.session_state:
    st.session_state.campaign_id = None
if 'campaign_summary' not in st.session_state:
    st.session_state.campaign_summary = {}
if 'filtered_customers' not in st.session_state:
    st.session_state.filtered_customers = pd.DataFrame()
if 'selected_templates' not in st.session_state:
    st.session_state.selected_templates = {}
if 'email_preview_customer' not in st.session_state:
    st.session_state.email_preview_customer = {}
if 'campaign_executed' not in st.session_state:
    st.session_state.campaign_executed = False
if 'test_mode' not in st.session_state:
    st.session_state.test_mode = True
if 'execution_confirmed' not in st.session_state:
    st.session_state.execution_confirmed = False

# Constants
TEST_DATA_PATH = "data/test_customers.csv"

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
    </style>
    """, unsafe_allow_html=True)

# Function to load test data
def load_test_data():
    """Load test customer data from CSV file"""
    try:
        if os.path.exists(TEST_DATA_PATH):
            return pd.read_csv(TEST_DATA_PATH)
        else:
            st.error(f"Test data file not found at {TEST_DATA_PATH}. Please add test customers first.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading test data: {e}")
        return pd.DataFrame()

# Function to create email preview
def create_email_preview(template, customer_data):
    try:
        subject = template['subject'].format(**customer_data)
        body_html = template['body_html'].format(**customer_data)
        
        st.markdown('<div class="email-preview">', unsafe_allow_html=True)
        
        # Email header
        st.markdown('<div class="email-header">', unsafe_allow_html=True)
        st.markdown(f'<div class="email-subject">Subject: {subject}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="email-from">From: Mall Marketing Team &lt;marketing@mall.com&gt;</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="email-to">To: {customer_data["email"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Email body
        st.markdown('<div class="email-body">', unsafe_allow_html=True)
        st.markdown(body_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        return True
    except KeyError as e:
        st.warning(f"Missing data for email template: {e}")
        return False
    except Exception as e:
        st.error(f"Error creating email preview: {e}")
        return False

# Callback for campaign setup form
def handle_campaign_setup_form(target_type, campaign_name, target_segments, target_categories, test_mode, max_emails, email_user, email_password, email_host, email_port, email_ready_customers, selected_templates):
    # Store the test mode in session state
    st.session_state.test_mode = test_mode
    
    # Validate form
    if target_type == "Segment-based" and not target_segments:
        st.error("Please select at least one segment to target.")
        return False
    elif target_type == "Category-based" and not target_categories:
        st.error("Please select at least one category to target.")
        return False
    elif not selected_templates:
        st.error("No templates available for the selected targets.")
        return False
    elif not email_user or not email_password:
        st.error("Email configuration is missing. Please set up your email first.")
        return False
    
    # Prepare target data
    if target_type == "Segment-based":
        # Filter customers by segment
        filtered_customers = email_ready_customers[email_ready_customers['segment_name'].isin(target_segments)]
        target_description = ", ".join(target_segments)
    else:  # Category-based
        # Filter customers by category
        filtered_customers = email_ready_customers[email_ready_customers['primary_category'].isin(target_categories)]
        target_description = ", ".join(target_categories)
    
    # Limit to max emails
    if not filtered_customers.empty and len(filtered_customers) > max_emails:
        filtered_customers = filtered_customers.sample(n=max_emails, random_state=42)
    
    if filtered_customers.empty:
        st.error("No customers match the selected criteria.")
        return False
    
    # Store the filtered customers and templates in session state
    st.session_state.filtered_customers = filtered_customers
    st.session_state.selected_templates = selected_templates
    
    # Store the email preview customer in session state
    st.session_state.email_preview_customer = filtered_customers.iloc[0].to_dict()
    
    # Create email config
    email_config = {
        'host': email_host,
        'port': email_port,
        'username': email_user,
        'password': email_password,
        'test_mode': test_mode,
        'max_emails': max_emails
    }
    
    # Prepare target data for storage
    target_data = {
        'target_type': target_type,
        'count': len(filtered_customers),
        'details': target_description,
        'customer_ids': filtered_customers['customer_id'].tolist() if 'customer_id' in filtered_customers.columns else []
    }
    
    # Initialize campaign manager
    campaign_manager = CampaignManager()
    
    # Create campaign
    campaign_id = campaign_manager.create_campaign(
        campaign_name=campaign_name,
        campaign_type=target_type,
        target_description=target_description,
        templates=selected_templates,
        target_data=target_data,
        email_config=email_config
    )
    
    # Store campaign info in session state
    st.session_state.campaign_id = campaign_id
    st.session_state.campaign_summary = {
        'campaign_id': campaign_id,
        'campaign_name': campaign_name,
        'campaign_type': target_type,
        'target_description': target_description,
        'total_customers': len(filtered_customers),
        'test_mode': test_mode
    }
    
    # Set campaign setup complete flag
    st.session_state.campaign_setup_complete = True
    
    return True

# Callback for running test campaign
def run_test_campaign():
    # Check if campaign setup is complete
    if not st.session_state.campaign_setup_complete:
        st.error("Please set up a campaign first.")
        return
    
    # Get campaign info from session state
    campaign_id = st.session_state.campaign_id
    filtered_customers = st.session_state.filtered_customers
    
    # Check if filtered customers is empty
    if filtered_customers.empty:
        st.error("No customers match the selected criteria. Cannot run test campaign.")
        return
    
    # Initialize campaign manager
    campaign_manager = CampaignManager()
    
    # Simulate sending emails
    with st.spinner("Running test campaign..."):
        # Update campaign status
        campaign_manager.update_campaign_status(
            campaign_id=campaign_id, 
            status="Testing"
        )
        
        # Simulate processing time
        time.sleep(2)
        
        # Create expected results
        results = {
            'emails_sent': len(filtered_customers),
            'emails_opened': 0,
            'emails_clicked': 0,
            'test_mode': True,
            'details': [
                {'email': customer['email'], 'status': 'simulated'} 
                for _, customer in filtered_customers.iterrows()
            ]
        }
        
        # Update campaign status
        campaign_manager.update_campaign_status(
            campaign_id=campaign_id, 
            status="Tested",
            results=results
        )
    
    # Set campaign executed flag
    st.session_state.campaign_executed = True
    st.rerun()

# Create a new fixed function for checkbox handling 
def handle_confirmation_change():
    """Toggle the execution confirmation state"""
    if 'execution_confirmed' not in st.session_state:
        st.session_state.execution_confirmed = False
    else:
        st.session_state.execution_confirmed = not st.session_state.execution_confirmed
    print(f"Execution confirmed: {st.session_state.execution_confirmed}")  # Debug log

# Callback for executing real campaign
def execute_real_campaign():
    # Check if campaign setup is complete
    if not st.session_state.campaign_setup_complete:
        st.error("Please set up a campaign first.")
        return
    
    # Check if execution is confirmed
    if not st.session_state.execution_confirmed:
        st.warning("Please confirm that you want to send real emails.")
        return
    
    # Get campaign info from session state
    campaign_id = st.session_state.campaign_id
    filtered_customers = st.session_state.filtered_customers
    selected_templates = st.session_state.selected_templates
    campaign_summary = st.session_state.campaign_summary
    
    # Check if filtered customers is empty
    if filtered_customers.empty:
        st.error("No customers match the selected criteria. Cannot run campaign.")
        return
    
    # Check if selected templates is empty
    if not selected_templates:
        st.error("No email templates available for the selected targets.")
        return
    
    # Get email configuration from .env
    email_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    email_port = int(os.getenv("EMAIL_PORT", "465"))
    email_user = os.getenv("EMAIL_USER", "")
    email_password = os.getenv("EMAIL_PASSWORD", "")
    
    # Initialize campaign manager
    campaign_manager = CampaignManager()
    
    # Send emails
    with st.spinner(f"Sending emails..."):
        try:
            # Create email sender
            email_sender = EmailSender(
                host=email_host,
                port=email_port,
                username=email_user,
                password=email_password,
                enable_tracking=True
            )
            
            # Update campaign status
            campaign_manager.update_campaign_status(
                campaign_id=campaign_id, 
                status="Executing"
            )
            
            # Send emails based on campaign type
            results = {}
            target_type = campaign_summary['campaign_type']
            
            if target_type == "Segment-based":
                # Get target segments from description
                target_segments = campaign_summary['target_description'].split(", ")
                
                # Create segment templates dictionary
                segment_templates = {segment: selected_templates[segment] for segment in target_segments if segment in selected_templates}
                
                # Check if segment templates is empty after filtering
                if not segment_templates:
                    st.error("No templates available for the selected segments.")
                    return
                
                # Send segment-specific emails
                max_emails = len(filtered_customers)
                results = email_sender.send_segment_emails(
                    customers=filtered_customers,
                    segment_templates=segment_templates,
                    segment_column='segment_name',
                    test_mode=False,
                    max_emails_per_segment=max_emails // len(segment_templates) if len(segment_templates) > 0 else max_emails,
                    campaign_id=campaign_id
                )
            
            else:  # Category-based
                # Get target categories from description
                target_categories = campaign_summary['target_description'].split(", ")
                
                # Create category templates dictionary
                category_templates = {}
                for display_category, template in selected_templates.items():
                    db_category = display_category.lower().replace(' ', '_')
                    category_templates[db_category] = template
                
                # Check if category templates is empty
                if not category_templates:
                    st.error("No templates available for the selected categories.")
                    return
                
                # Send category-specific emails
                max_emails = len(filtered_customers)
                results = email_sender.send_segment_emails(
                    customers=filtered_customers,
                    segment_templates=category_templates,
                    segment_column='primary_category',
                    test_mode=False,
                    max_emails_per_segment=max_emails // len(category_templates) if len(category_templates) > 0 else max_emails,
                    campaign_id=campaign_id
                )
            
            # Calculate total sent
            total_sent = 0
            result_details = []
            
            if isinstance(results, dict):
                if 'success' in results:
                    # For bulk emails
                    total_sent = results['success']
                    result_details = [{'status': 'summary', 'success': results['success'], 'failed': results['failed']}]
                else:
                    # For segment emails
                    for segment, segment_results in results.items():
                        if segment != 'other':
                            total_sent += segment_results['success']
                            result_details.append({
                                'segment': segment, 
                                'success': segment_results['success'], 
                                'failed': segment_results['failed']
                            })
            
            # Update campaign status
            campaign_manager.update_campaign_status(
                campaign_id=campaign_id, 
                status="Executed",
                results={
                    'emails_sent': total_sent,
                    'emails_opened': 0,  # Initially 0
                    'emails_clicked': 0,  # Initially 0
                    'test_mode': False,
                    'details': result_details
                }
            )
            
            # Store results in session state
            st.session_state.campaign_results = {
                'total_sent': total_sent,
                'details': result_details
            }
            
            # Set campaign executed flag
            st.session_state.campaign_executed = True
            st.rerun()
            
        except Exception as e:
            st.error(f"Error executing campaign: {str(e)}")
            
            # Update campaign status
            campaign_manager.update_campaign_status(
                campaign_id=campaign_id, 
                status="Failed",
                results={'error': str(e)}
            )

# Function to reset campaign
def reset_campaign():
    st.session_state.campaign_setup_complete = False
    st.session_state.campaign_id = None
    st.session_state.campaign_summary = {}
    st.session_state.filtered_customers = pd.DataFrame()
    st.session_state.selected_templates = {}
    st.session_state.email_preview_customer = {}
    st.session_state.campaign_executed = False
    st.session_state.test_mode = True
    st.session_state.execution_confirmed = False
    if 'campaign_results' in st.session_state:
        del st.session_state.campaign_results
    st.rerun()

# Function to show email diagnostic information
def show_email_diagnostic():
    """Show diagnostic information for email configuration"""
    with st.expander("📧 Email Configuration Diagnostics"):
        # Load environment variables
        load_dotenv(override=True)
        
        # Get email configuration from .env
        email_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        email_port = int(os.getenv("EMAIL_PORT", "465"))
        email_user = os.getenv("EMAIL_USER", "")
        email_password = os.getenv("EMAIL_PASSWORD", "")
        
        # Display configuration
        st.write("### Email Configuration")
        st.write(f"**Host:** {email_host}")
        st.write(f"**Port:** {email_port}")
        st.write(f"**Username:** {email_user}")
        st.write(f"**Password Length:** {len(email_password) if email_password else 0} characters")
        
        # Gmail-specific guidance
        if "gmail.com" in email_user.lower():
            st.warning("""
            #### Gmail Configuration Note
            Since you're using Gmail, make sure you have:
            1. Enabled 2-Step Verification for your Google account
            2. Created an App Password:
               - Go to your Google Account → Security → App Passwords
               - Select 'Mail' as the app and your device
               - Use the generated 16-character password in your .env file
            3. Make sure the password in .env does NOT have spaces
            """)
        
        # Test connection button
        if st.button("Test Email Connection"):
            with st.spinner("Testing connection to email server..."):
                try:
                    # Connect to SMTP server
                    if email_port == 465:
                        server = smtplib.SMTP_SSL(email_host, email_port)
                    else:
                        server = smtplib.SMTP(email_host, email_port)
                        server.starttls()
                    
                    # Login
                    server.login(email_user, email_password)
                    st.success("✅ Connection to email server successful!")
                    server.quit()
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
                    st.info("""
                    **Common solutions:**
                    - For Gmail: Use an App Password instead of your regular password
                    - Check that your email and password are correct in the .env file
                    - Make sure your network allows SMTP connections
                    - Check if your email provider allows app access
                    """)

# Main function
def main():
    # Load CSS
    load_css()
    
    # Display header
    st.markdown('<h1 class="main-header">Test Email Campaign</h1>', unsafe_allow_html=True)
    
    # Display email diagnostics
    show_email_diagnostic()
    
    # Display helpful introduction
    st.info("""
    **Welcome to the Test Email Campaign page!**
    
    This page allows you to create and test email campaigns using your test customer data.
    
    1. First, set up your campaign by selecting target segments or categories
    2. Review the email preview that will be sent
    3. Run the campaign in test mode or send real emails
    
    Make sure you have added test customers in the Test Data Manager page before proceeding.
    """)
    
    # Load environment variables
    load_dotenv(override=True)
    
    # Get email configuration from .env
    email_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    email_port = int(os.getenv("EMAIL_PORT", "465"))
    email_user = os.getenv("EMAIL_USER", "")
    email_password = os.getenv("EMAIL_PASSWORD", "")
    
    # Load test data
    test_data = load_test_data()
    
    if test_data.empty:
        st.warning("No test customer data found. Please add test customers in the Test Data Manager page first.")
        st.markdown("[Go to Test Data Manager](/Test_Data_Manager)")
        return
    
    # Prepare test customer data for email templates
    email_ready_customers = EmailTemplateManager.prepare_customer_data_for_email(test_data)
    
    # Check if campaign setup is complete
    if not st.session_state.campaign_setup_complete:
        # Campaign setup form
        with st.form(key="test_campaign_form"):
            st.markdown('<h2 class="sub-header">Test Campaign Setup</h2>', unsafe_allow_html=True)
            
            # Campaign name
            campaign_name = st.text_input(
                "Campaign Name", 
                f"Test Campaign {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # Target type
            target_type = st.radio(
                "Target Type",
                ["Segment-based", "Category-based"],
                index=0
            )
            
            # Add empty variable initialization before the conditional
            target_segments = []
            target_categories = []
            selected_templates = {}
            
            # Select target based on type
            if target_type == "Segment-based":
                if len(test_data['segment_name'].unique()) > 0:
                    default_segment = [sorted(test_data['segment_name'].unique())[0]]
                else:
                    default_segment = []
                    
                target_segments = st.multiselect(
                    "Target Segments",
                    options=sorted(test_data['segment_name'].unique()),
                    default=default_segment
                )
                
                # Get segment templates
                templates = EmailTemplateManager.get_segment_templates()
                
                # Filter templates for selected segments
                selected_templates = {segment: templates[segment] for segment in target_segments if segment in templates}
                
                # Display target counts
                if target_segments:
                    st.write("Target Customer Counts:")
                    for segment in target_segments:
                        segment_count = len(test_data[test_data['segment_name'] == segment])
                        st.write(f"- {segment}: {segment_count} customers")
                
            else:  # Category-based
                if len(test_data['primary_category'].unique()) > 0:
                    default_category = [sorted(test_data['primary_category'].unique())[0]]
                else:
                    default_category = []
                    
                target_categories = st.multiselect(
                    "Target Categories",
                    options=sorted(test_data['primary_category'].unique()),
                    default=default_category
                )
                
                # Get category templates
                templates = EmailTemplateManager.get_category_templates()
                
                # Convert database categories to display categories for templates
                selected_templates = {}
                for db_category in target_categories:
                    display_category = db_category.replace('_', ' ').title()
                    if db_category in templates:
                        selected_templates[display_category] = templates[db_category]
                
                # Display target counts
                if target_categories:
                    st.write("Target Customer Counts:")
                    for category in target_categories:
                        category_count = len(test_data[test_data['primary_category'] == category])
                        st.write(f"- {category}: {category_count} customers")
            
            # Test mode option
            test_mode = st.checkbox("Test Mode (No emails will be sent)", value=True)
            
            # Max emails
            max_emails = st.number_input(
                "Maximum Emails to Send",
                min_value=1,
                max_value=100,
                value=5
            )
            
            # Email configuration info
            st.markdown("#### Email Configuration")
            
            if email_user and email_password:
                st.info(f"Using email configuration: {email_user} @ {email_host}:{email_port}")
            else:
                st.error("Email configuration not found. Please set up your email in the Email Configuration Setup section of the Email Marketing page.")
            
            # Submit button
            submit_button = st.form_submit_button("Set Up Campaign")
        
        # Handle form submission outside the form (but check for the form submission)
        if submit_button:
            # Handle form submission
            if target_type == "Segment-based":
                handle_campaign_setup_form(
                    target_type=target_type,
                    campaign_name=campaign_name,
                    target_segments=target_segments,
                    target_categories=[],
                    test_mode=test_mode,
                    max_emails=max_emails,
                    email_user=email_user,
                    email_password=email_password,
                    email_host=email_host,
                    email_port=email_port,
                    email_ready_customers=email_ready_customers,
                    selected_templates=selected_templates
                )
            else:  # Category-based
                handle_campaign_setup_form(
                    target_type=target_type,
                    campaign_name=campaign_name,
                    target_segments=[],
                    target_categories=target_categories,
                    test_mode=test_mode,
                    max_emails=max_emails,
                    email_user=email_user,
                    email_password=email_password,
                    email_host=email_host,
                    email_port=email_port,
                    email_ready_customers=email_ready_customers,
                    selected_templates=selected_templates
                )
    
    # Display campaign summary if setup is complete
    if st.session_state.campaign_setup_complete:
        # Get campaign info from session state
        campaign_summary = st.session_state.campaign_summary
        selected_templates = st.session_state.selected_templates
        filtered_customers = st.session_state.filtered_customers
        
        st.success(f"Campaign '{campaign_summary['campaign_name']}' set up successfully!")
        
        # Reset button at the top right
        col1, col2 = st.columns([10, 2])
        with col2:
            st.button("Reset Campaign", on_click=reset_campaign)
        
        with col1:
            # Display campaign summary
            st.markdown("### Campaign Summary")
            st.markdown(f"**Campaign ID**: {campaign_summary['campaign_id']}")
            st.markdown(f"**Campaign Type**: {campaign_summary['campaign_type']}")
            st.markdown(f"**Target**: {campaign_summary['target_description']}")
            st.markdown(f"**Total Customers**: {campaign_summary['total_customers']}")
            st.markdown(f"**Mode**: {'Test Mode (No emails will be sent)' if campaign_summary['test_mode'] else 'Live Mode (Real emails will be sent)'}")
        
        # Display email preview
        st.markdown("### Email Preview")
        
        sample_customer = st.session_state.email_preview_customer
        
        for target, template in selected_templates.items():
            st.markdown(f"#### Template for: {target}")
            create_email_preview(template, sample_customer)
        
        # Campaign execution
        st.markdown("### Campaign Execution")
        
        # If campaign has been executed
        if st.session_state.campaign_executed:
            if st.session_state.test_mode:
                st.success(f"Test completed! {len(filtered_customers)} emails would be sent.")
                
                # Show test recipients
                st.markdown("#### Test Recipients")
                st.dataframe(filtered_customers[['email', 'first_name', 'last_name', 'segment_name', 'primary_category']], use_container_width=True)
            else:
                # Get results from session state
                campaign_results = st.session_state.get('campaign_results', {})
                
                if campaign_results:
                    st.success(f"Campaign executed successfully! {campaign_results.get('total_sent', 0)} emails sent.")
                    
                    # Show details of results
                    st.markdown("#### Sending Results")
                    for detail in campaign_results.get('details', []):
                        if 'segment' in detail:
                            st.info(f"**{detail['segment']}**: {detail['success']} sent, {detail['failed']} failed")
                        else:
                            st.info(f"**Summary**: {detail['success']} sent, {detail['failed']} failed")
                else:
                    st.info("Campaign execution results not available.")
        else:
            # Execution buttons based on mode
            if st.session_state.test_mode:
                st.info("Test mode is enabled. No emails will be sent.")
                
                # Execute campaign button for test mode
                st.button("Run Test Campaign", on_click=run_test_campaign)
            else:
                # Create email sender to validate configuration
                try:
                    email_sender = EmailSender(
                        host=email_host,
                        port=email_port,
                        username=email_user,
                        password=email_password,
                        enable_tracking=True
                    )
                    
                    st.success("Email configuration validated successfully!")
                    
                    # Confirmation checkbox - FIXED IMPLEMENTATION
                    confirm = st.checkbox(
                        "I confirm that I want to send these emails", 
                        value=st.session_state.get('execution_confirmed', False),
                        key="confirm_checkbox",
                        on_change=handle_confirmation_change
                    )
                    
                    # Execute button - directly check the current state
                    if st.button("Execute Campaign", disabled=not st.session_state.get('execution_confirmed', False)):
                        execute_real_campaign()
                    
                except Exception as e:
                    st.error(f"Email configuration error: {str(e)}")
                    st.info("""
                    **Common solutions:**
                    • Check your email and password
                    • Gmail users: Use an App Password
                    • Check your email provider's security settings
                    """)

# Run the app
if __name__ == "__main__":
    main() 