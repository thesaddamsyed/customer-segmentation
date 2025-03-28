"""
Email Marketing Page

This page allows users to set up and manage automated email marketing campaigns
based on customer segments and purchase history.
"""
import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import json
import uuid
import time
from dotenv import load_dotenv

# Import custom modules
from src.data_processing.data_loader import load_and_process
from src.segmentation.segmentation import CustomerSegmentation
from src.email.email_sender import EmailSender, EmailTemplateManager
from src.email.campaign_manager import CampaignManager

# Set page configuration
st.set_page_config(
    page_title="Email Marketing - Mall Customer Segmentation",
    page_icon="📧",
    layout="wide"
)

# Create required directories
os.makedirs("data", exist_ok=True)
os.makedirs("data/campaigns", exist_ok=True)
os.makedirs("data/campaigns/results", exist_ok=True)
os.makedirs("data/email_tracking", exist_ok=True)

# Initialize session state
if 'email_preview_customer' not in st.session_state:
    st.session_state.email_preview_customer = None
if 'campaign_created' not in st.session_state:
    st.session_state.campaign_created = False
if 'campaign_id' not in st.session_state:
    st.session_state.campaign_id = None
if 'execution_results' not in st.session_state:
    st.session_state.execution_results = None

# Define paths
DATA_PATH = "project2.csv"
PROCESSED_DATA_PATH = "data/processed_customer_features.csv"
MODEL_PATH = "models/segmentation_model"

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
        .template-card {
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
        .template-card:hover {
            transform: translateY(-5px);
        }
        .template-title {
            font-size: 1.2rem;
            font-weight: bold;
            color: #4527A0;
            margin-bottom: 0.5rem;
        }
        .template-description {
            font-size: 0.9rem;
            color: #6c757d;
        }
        .selected-template {
            border: 2px solid #4527A0;
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

# Function to load data
@st.cache_data
def load_cached_data():
    if os.path.exists(PROCESSED_DATA_PATH):
        # Load processed data if it exists
        customer_features = pd.read_csv(PROCESSED_DATA_PATH, index_col=0)
        transactions_df, _ = load_and_process(DATA_PATH)
        return transactions_df, customer_features
    else:
        # Process data if processed data doesn't exist
        os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
        transactions_df, customer_features = load_and_process(DATA_PATH, PROCESSED_DATA_PATH)
        return transactions_df, customer_features

# Function to load segmentation model
@st.cache_resource
def load_model():
    if os.path.exists(os.path.join(MODEL_PATH, 'kmeans.pkl')):
        # Load model if it exists
        model = CustomerSegmentation.load_model(MODEL_PATH)
        return model
    else:
        st.error("Segmentation model not found. Please run the main page first to train the model.")
        return None

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

# Main function
def main():
    # Load CSS
    load_css()
    
    # Display header
    st.markdown('<h1 class="main-header">Email Marketing</h1>', unsafe_allow_html=True)
    
    # Email Configuration Section
    with st.expander("Email Configuration Setup", expanded=not os.path.exists(".env")):
        st.markdown("### Configure Email Provider")
        st.markdown("""
        To send real emails, you need to configure your email provider details.
        This information will be securely stored in a .env file.
        
        **Note for Gmail users**: You may need to use an App Password rather than your regular password.
        [Learn how to create an App Password](https://support.google.com/accounts/answer/185833)
        """)
        
        with st.form("email_config_form"):
            email_provider = st.selectbox(
                "Email Provider",
                ["Gmail", "Outlook", "Yahoo", "Custom SMTP"],
                index=0
            )
            
            if email_provider == "Gmail":
                email_host = "smtp.gmail.com"
                email_port = 587
            elif email_provider == "Outlook":
                email_host = "smtp.office365.com"
                email_port = 587
            elif email_provider == "Yahoo":
                email_host = "smtp.mail.yahoo.com"
                email_port = 587
            else:
                email_host = st.text_input("SMTP Server Host", "smtp.example.com")
                email_port = st.number_input("SMTP Server Port", value=587)
            
            email_user = st.text_input("Email Address", placeholder="your.email@example.com")
            email_password = st.text_input("Email Password or App Password", type="password")
            
            # Only show these fields if using custom SMTP
            if email_provider == "Custom SMTP":
                st.markdown("**Optional Settings**")
                use_tls = st.checkbox("Use TLS", value=True)
                use_ssl = st.checkbox("Use SSL", value=False)
            else:
                use_tls = True
                use_ssl = False
            
            submitted = st.form_submit_button("Save Email Configuration")
        
        if submitted:
            if not email_user or not email_password:
                st.error("Email address and password are required.")
            else:
                # Create or update .env file
                env_content = f"""EMAIL_HOST={email_host}
EMAIL_PORT={email_port}
EMAIL_USER={email_user}
EMAIL_PASSWORD={email_password}
EMAIL_USE_TLS={'True' if use_tls else 'False'}
EMAIL_USE_SSL={'True' if use_ssl else 'False'}
"""
                with open(".env", "w") as f:
                    f.write(env_content)
                
                st.success("Email configuration saved successfully! You can now send real emails.")
                
                # Test the connection
                try:
                    test_sender = EmailSender(
                        host=email_host,
                        port=email_port,
                        username=email_user,
                        password=email_password
                    )
                    st.success("Connection to email server tested successfully!")
                except Exception as e:
                    st.error(f"Error connecting to email server: {str(e)}")
    
    # Load data
    with st.spinner("Loading data..."):
        transactions_df, customer_features = load_cached_data()
    
    # Load model
    with st.spinner("Loading segmentation model..."):
        model = load_model()
        
        if model is None:
            st.stop()
    
    # Get customer segments
    customer_segments = model.get_customer_segments(customer_features)
    
    # Get segment profiles
    segment_profiles = model.get_segment_profiles()
    
    # Prepare customer data for email templates
    email_ready_customers = EmailTemplateManager.prepare_customer_data_for_email(customer_segments)
    
    # Create tabs for different email marketing functions
    tab1, tab2, tab3 = st.tabs(["Campaign Setup", "Template Editor", "Campaign History"])
    
    with tab1:
        st.markdown('<h2 class="sub-header">Set Up Email Campaign</h2>', unsafe_allow_html=True)
        
        # Campaign setup form
        with st.form("campaign_setup_form"):
            # Campaign name
            campaign_name = st.text_input("Campaign Name", f"Campaign {datetime.now().strftime('%Y-%m-%d')}")
            
            # Campaign type
            campaign_type = st.selectbox(
                "Campaign Type",
                ["Segment-based", "Category-based", "Custom"]
            )
            
            # Target selection based on campaign type
            if campaign_type == "Segment-based":
                # Select segments to target
                segment_options = sorted(segment_profiles['segment_name'].unique().tolist())
                target_segments = st.multiselect(
                    "Target Segments",
                    segment_options
                )
                
                # Get segment templates
                templates = EmailTemplateManager.get_segment_templates()
                
                # Filter templates for selected segments
                selected_templates = {segment: templates[segment] for segment in target_segments if segment in templates}
            
            elif campaign_type == "Category-based":
                # Get unique categories from the primary_category column
                if 'primary_category' in customer_segments.columns:
                    available_categories = sorted(customer_segments['primary_category'].unique().tolist())
                    category_options = [cat.replace('_', ' ').title() for cat in available_categories]
                    
                    # Select categories to target
                    target_categories = st.multiselect(
                        "Target Categories",
                        options=category_options,
                        default=[category_options[0]] if category_options else []
                    )
                    
                    # Create templates for selected categories
                    selected_templates = {}
                    for category in target_categories:
                        # Create a template for each selected category
                        selected_templates[category] = {
                            'subject': f'Special Offers on {category} Products, {{first_name}}!',
                            'body_html': f"""
                            <html>
                            <body>
                                <h1>Hello {{first_name}},</h1>
                                <p>As someone who has purchased {category} products from us before, we thought you'd be interested in our latest offers:</p>
                                <ul>
                                    <li>New arrivals in our {category} collection</li>
                                    <li>Special discounts on selected {category} items</li>
                                    <li>Limited-time offers for our valued customers</li>
                                </ul>
                                <p>Visit us soon to check out these amazing deals!</p>
                                <p>Best regards,<br>The Mall Team</p>
                            </body>
                            </html>
                            """
                        }
                    
                    # Show customer counts for selected categories
                    if target_categories:
                        st.markdown("#### Customer Distribution by Category")
                        for display_category in target_categories:
                            # Convert display category back to database format
                            db_category = display_category.lower().replace(' ', '_')
                            
                            # Count customers with this primary category
                            category_customers = customer_segments[customer_segments['primary_category'] == db_category]
                            customer_count = len(category_customers)
                            total_customers = len(customer_segments)
                            
                            # Display count and percentage
                            st.info(f"**{display_category}**: {customer_count} customers ({customer_count/total_customers*100:.1f}% of total)")
                            
                            # Show a bar chart of spending in this category
                            if not category_customers.empty:
                                spend_col = f"spend_{db_category}"
                                if spend_col in customer_segments.columns:
                                    spending_data = category_customers[spend_col].dropna()
                                    if not spending_data.empty:
                                        fig = px.histogram(
                                            spending_data,
                                            nbins=20,
                                            title=f"Spending Distribution - {display_category} Customers",
                                            labels={"value": "Spending Amount ($)", "count": "Number of Customers"}
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Primary category information not found in customer data")
                    target_categories = []
                    selected_templates = {}
            
            else:  # Custom campaign
                # Custom targeting options
                st.markdown("#### Custom Targeting Criteria")
                
                # Age range
                age_min, age_max = st.slider(
                    "Age Range",
                    min_value=18,
                    max_value=80,
                    value=(25, 55)
                )
                
                # Cities
                city_options = customer_segments['city'].unique().tolist() if 'city' in customer_segments.columns else []
                target_cities = st.multiselect(
                    "Target Cities",
                    city_options,
                    default=city_options[:2] if len(city_options) >= 2 else city_options
                )
                
                # Gender
                gender_options = customer_segments['gender'].unique().tolist() if 'gender' in customer_segments.columns else []
                target_genders = st.multiselect(
                    "Target Genders",
                    gender_options,
                    default=gender_options
                )
                
                # Custom template
                custom_subject = st.text_input(
                    "Email Subject",
                    "Special Offer for {first_name}!"
                )
                
                custom_body = st.text_area(
                    "Email Body (HTML)",
                    """
                    <html>
                    <body>
                        <h1>Hello {first_name},</h1>
                        <p>We have a special offer just for you!</p>
                        <p>Visit our store to enjoy exclusive discounts on your favorite products.</p>
                        <p>Best regards,<br>The Mall Team</p>
                    </body>
                    </html>
                    """
                )
                
                # Create custom template
                selected_templates = {
                    "custom": {
                        "subject": custom_subject,
                        "body_html": custom_body
                    }
                }
            
            # Email sending options
            st.markdown("#### Email Sending Options")
            
            # Test mode
            test_mode = st.checkbox("Test Mode (No emails will be sent)", value=True)
            
            # Max emails
            max_emails = st.number_input(
                "Maximum Emails to Send",
                min_value=1,
                max_value=1000,
                value=10
            )

            # Schedule date
            include_schedule = st.checkbox("Schedule for later", value=False)
            scheduled_date = None
            if include_schedule:
                scheduled_date = st.date_input(
                    "Schedule Date",
                    value=datetime.now().date()
                )
            
            # Use email configuration from .env if available
            if os.path.exists(".env"):
                load_dotenv()
                
                # Get email configuration from .env
                email_host = os.getenv("EMAIL_HOST", "smtp.example.com")
                email_port = int(os.getenv("EMAIL_PORT", "587"))
                email_user = os.getenv("EMAIL_USER", "")
                email_password = os.getenv("EMAIL_PASSWORD", "")
                
                st.markdown("#### Email Configuration")
                st.info(f"Using saved email configuration for {email_user}. You can update it in the Email Configuration Setup section.")
            else:
                # Email configuration
                st.markdown("#### Email Configuration")
                st.warning("No saved email configuration found. Please enter your email details below or set up a configuration in the Email Configuration Setup section.")
                
                # SMTP settings
                email_host = st.text_input("SMTP Host", "smtp.example.com")
                email_port = st.number_input("SMTP Port", value=587)
                email_user = st.text_input("SMTP Username", "your_email@example.com")
                email_password = st.text_input("SMTP Password", type="password")
            
            # Submit button
            submit_button = st.form_submit_button("Set Up Campaign")
        
        # Handle form submission
        if submit_button:
            # Validate form
            if campaign_type == "Segment-based" and not target_segments:
                st.error("Please select at least one segment to target.")
            elif campaign_type == "Category-based" and not target_categories:
                st.error("Please select at least one category to target.")
            elif not selected_templates:
                st.error("No templates available for the selected targets.")
            else:
                # Prepare target data
                if campaign_type == "Segment-based":
                    # Filter customers by segment
                    filtered_customers = pd.DataFrame()
                    target_description = ", ".join(target_segments)
                    
                    for segment in target_segments:
                        segment_customers = customer_segments[customer_segments['segment_name'] == segment]
                        if not segment_customers.empty:
                            if filtered_customers.empty:
                                filtered_customers = segment_customers
                            else:
                                filtered_customers = pd.concat([filtered_customers, segment_customers])
                    
                    # Prepare customer data for email templates
                    if not filtered_customers.empty:
                        email_ready_customers = EmailTemplateManager.prepare_customer_data_for_email(filtered_customers)
                    else:
                        email_ready_customers = pd.DataFrame()
                
                elif campaign_type == "Category-based":
                    # Filter customers by category
                    filtered_customers = pd.DataFrame()
                    db_categories = [cat.lower().replace(' ', '_') for cat in target_categories]
                    target_description = ", ".join(target_categories)
                    
                    for db_category in db_categories:
                        category_customers = customer_segments[customer_segments['primary_category'] == db_category]
                        if not category_customers.empty:
                            if filtered_customers.empty:
                                filtered_customers = category_customers
                            else:
                                filtered_customers = pd.concat([filtered_customers, category_customers])
                    
                    # Remove duplicates
                    if not filtered_customers.empty:
                        filtered_customers = filtered_customers.drop_duplicates()
                        # Prepare customer data for email templates
                        email_ready_customers = EmailTemplateManager.prepare_customer_data_for_email(filtered_customers)
                    else:
                        email_ready_customers = pd.DataFrame()
                
                else:  # Custom campaign
                    # Filter customers based on custom criteria
                    filtered_customers = customer_segments.copy()
                    target_criteria = []
                    
                    if 'age' in filtered_customers.columns:
                        filtered_customers = filtered_customers[
                            (filtered_customers['age'] >= age_min) &
                            (filtered_customers['age'] <= age_max)
                        ]
                        target_criteria.append(f"Age {age_min}-{age_max}")
                    
                    if target_cities and 'city' in filtered_customers.columns:
                        filtered_customers = filtered_customers[filtered_customers['city'].isin(target_cities)]
                        target_criteria.append(f"Cities: {', '.join(target_cities)}")
                    
                    if target_genders and 'gender' in filtered_customers.columns:
                        filtered_customers = filtered_customers[filtered_customers['gender'].isin(target_genders)]
                        target_criteria.append(f"Genders: {', '.join(target_genders)}")
                    
                    target_description = "; ".join(target_criteria)
                    
                    # Prepare customer data for email templates
                    if not filtered_customers.empty:
                        email_ready_customers = EmailTemplateManager.prepare_customer_data_for_email(filtered_customers)
                    else:
                        email_ready_customers = pd.DataFrame()
                
                # Limit to max emails
                if not email_ready_customers.empty and len(email_ready_customers) > max_emails:
                    email_ready_customers = email_ready_customers.sample(n=max_emails, random_state=42)
                
                # Store the email preview customer in session state
                if not email_ready_customers.empty:
                    st.session_state.email_preview_customer = email_ready_customers.iloc[0].to_dict()
                
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
                    'target_type': campaign_type,
                    'count': len(email_ready_customers),
                    'details': target_description,
                }
                
                # Add customer_ids to target_data if the column exists
                if not email_ready_customers.empty and 'customer_id' in email_ready_customers.columns:
                    target_data['customer_ids'] = email_ready_customers['customer_id'].tolist()
                else:
                    target_data['customer_ids'] = []
                
                # Create campaign
                scheduled_date_str = scheduled_date.strftime("%Y-%m-%d") if scheduled_date else None
                campaign_id = campaign_manager.create_campaign(
                    campaign_name=campaign_name,
                    campaign_type=campaign_type,
                    target_description=target_description,
                    templates=selected_templates,
                    target_data=target_data,
                    email_config=email_config,
                    scheduled_date=scheduled_date_str
                )
                
                # Store campaign ID in session state
                st.session_state.campaign_id = campaign_id
                st.session_state.campaign_created = True
                
                st.success(f"Campaign '{campaign_name}' set up successfully!")
                
                # Display campaign summary
                st.markdown("### Campaign Summary")
                st.markdown(f"**Campaign ID**: {campaign_id}")
                st.markdown(f"**Campaign Type**: {campaign_type}")
                st.markdown(f"**Target**: {target_description}")
                st.markdown(f"**Total Customers**: {len(email_ready_customers)}")
                
                # Display email preview
                st.markdown("### Email Preview")
                
                if not email_ready_customers.empty:
                    sample_customer = st.session_state.email_preview_customer
                    
                    # Ensure required fields are present
                    if 'first_name' not in sample_customer:
                        sample_customer['first_name'] = "Sample Customer"
                    if 'email' not in sample_customer:
                        sample_customer['email'] = "sample@example.com"
                    
                    # Display preview for each template
                    for target, template in selected_templates.items():
                        st.markdown(f"#### Template for: {target}")
                        create_email_preview(template, sample_customer)
                
                # Campaign execution
                st.markdown("### Campaign Execution")
                
                if test_mode:
                    st.info("Test mode is enabled. No emails will be sent.")
                    
                    # Execute campaign button for test mode
                    if st.button("Run Test Campaign"):
                        # Simulate sending emails
                        with st.spinner("Running test campaign..."):
                            # Get campaign data
                            campaign_data = campaign_manager.get_campaign(campaign_id)
                            
                            # Update campaign status
                            campaign_manager.update_campaign_status(
                                campaign_id=campaign_id, 
                                status="Testing",
                                results={
                                    'emails_sent': len(email_ready_customers),
                                    'emails_opened': 0,
                                    'emails_clicked': 0,
                                    'test_mode': True,
                                    'details': [
                                        {'email': customer['email'], 'status': 'simulated'} 
                                        for _, customer in email_ready_customers.iterrows()
                                    ]
                                }
                            )
                            
                            # Simulate processing time
                            time.sleep(2)
                            
                            # Update campaign status
                            campaign_manager.update_campaign_status(
                                campaign_id=campaign_id, 
                                status="Tested"
                            )
                        
                        st.success(f"Test completed! {len(email_ready_customers)} emails would be sent.")
                        
                else:
                    # Check if we have valid email configuration
                    if not email_user or not email_password or email_user == "your_email@example.com":
                        st.error("Please configure your email provider in the Email Configuration Setup section before sending real emails.")
                    else:
                        # Create email sender
                        try:
                            email_sender = EmailSender(
                                host=email_host,
                                port=email_port,
                                username=email_user,
                                password=email_password,
                                enable_tracking=True
                            )
                            
                            st.success("Email configuration validated successfully!")
                            
                            # Add sample email options for testing
                            st.markdown("#### Send Test Email")
                            test_email = st.text_input("Send a test email to this address:", 
                                                      placeholder="youremail@example.com")
                            
                            if st.button("Send Test Email") and test_email:
                                with st.spinner("Sending test email..."):
                                    try:
                                        # Send test email
                                        sample_customer = st.session_state.email_preview_customer if not email_ready_customers.empty else {
                                            'first_name': 'Test',
                                            'email': test_email
                                        }
                                        
                                        success = email_sender.send_email(
                                            to_email=test_email,
                                            subject=f"Test Email from Mall Customer Segmentation",
                                            body_html=f"""<html>
                                            <body>
                                                <h1>Test Email</h1>
                                                <p>This is a test email from the Mall Customer Segmentation system.</p>
                                                <p>Your email configuration is working correctly!</p>
                                                <p>Best regards,<br>The Mall Team</p>
                                            </body>
                                            </html>""",
                                            campaign_id=campaign_id,
                                            customer_id="TEST_USER"
                                        )
                                        
                                        if success:
                                            st.success(f"Test email sent successfully to {test_email}!")
                                        else:
                                            st.error(f"Failed to send test email to {test_email}.")
                                    except Exception as e:
                                        st.error(f"Error sending test email: {str(e)}")
                            
                            # Execute campaign button
                            st.markdown("#### Execute Full Campaign")
                            if st.button("Execute Campaign"):
                                # Confirm execution
                                confirm = st.checkbox(f"I confirm that I want to send {len(email_ready_customers)} real emails. "
                                                   f"This action cannot be undone.")
                                
                                if confirm:
                                    # Send emails
                                    with st.spinner(f"Sending {len(email_ready_customers)} emails..."):
                                        try:
                                            # Update campaign status
                                            campaign_manager.update_campaign_status(
                                                campaign_id=campaign_id, 
                                                status="Executing"
                                            )
                                            
                                            # Send emails based on campaign type
                                            results = {}
                                            
                                            if campaign_type == "Segment-based":
                                                # Create segment templates dictionary
                                                segment_templates = {segment: selected_templates[segment] for segment in target_segments}
                                                
                                                # Send segment-specific emails
                                                results = email_sender.send_segment_emails(
                                                    customers=email_ready_customers,
                                                    segment_templates=segment_templates,
                                                    segment_column='segment_name',
                                                    test_mode=False,
                                                    max_emails_per_segment=max_emails // len(segment_templates) if len(segment_templates) > 0 else max_emails,
                                                    campaign_id=campaign_id
                                                )
                                            
                                            elif campaign_type == "Category-based":
                                                # Create category templates dictionary
                                                category_templates = {}
                                                for display_category in target_categories:
                                                    db_category = display_category.lower().replace(' ', '_')
                                                    if display_category in selected_templates:
                                                        category_templates[db_category] = selected_templates[display_category]
                                                
                                                # Send category-specific emails
                                                results = email_sender.send_segment_emails(
                                                    customers=email_ready_customers,
                                                    segment_templates=category_templates,
                                                    segment_column='primary_category',
                                                    test_mode=False,
                                                    max_emails_per_segment=max_emails // len(category_templates) if len(category_templates) > 0 else max_emails,
                                                    campaign_id=campaign_id
                                                )
                                            
                                            else:  # Custom campaign
                                                # Send bulk emails
                                                results = email_sender.send_bulk_emails(
                                                    customers=email_ready_customers,
                                                    subject_template=selected_templates['custom']['subject'],
                                                    body_html_template=selected_templates['custom']['body_html'],
                                                    test_mode=False,
                                                    max_emails=max_emails,
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
                                            
                                            # Store results in session state
                                            st.session_state.execution_results = {
                                                'emails_sent': total_sent,
                                                'emails_opened': 0,  # Initially 0
                                                'emails_clicked': 0,  # Initially 0
                                                'test_mode': False,
                                                'details': result_details
                                            }
                                            
                                            # Update campaign status
                                            campaign_manager.update_campaign_status(
                                                campaign_id=campaign_id, 
                                                status="Executed",
                                                results=st.session_state.execution_results
                                            )
                                            
                                            st.success(f"Campaign executed successfully! {total_sent} emails sent.")
                                            
                                            # Show details of results
                                            st.markdown("#### Sending Results")
                                            for detail in result_details:
                                                if 'segment' in detail:
                                                    st.info(f"**{detail['segment']}**: {detail['success']} sent, {detail['failed']} failed")
                                                else:
                                                    st.info(f"**Summary**: {detail['success']} sent, {detail['failed']} failed")
                                            
                                            # Add a link to the Email Tracking page
                                            st.markdown("[View Email Tracking →](/Email_Tracking)")
                                        
                                        except Exception as e:
                                            st.error(f"Error executing campaign: {str(e)}")
                                            
                                            # Update campaign status
                                            campaign_manager.update_campaign_status(
                                                campaign_id=campaign_id, 
                                                status="Failed",
                                                results={'error': str(e)}
                                            )
                                else:
                                    st.warning("Please confirm that you want to send real emails.")
                            
                        except Exception as e:
                            st.error(f"Email configuration error: {str(e)}")
                            st.markdown("""
                            Common errors:
                            - **Invalid credentials**: Check your email and password
                            - **Gmail users**: You may need to use an App Password instead of your regular password
                            - **Security settings**: Your email provider might be blocking "less secure app" access
                            - **Firewall/Network**: Your network might be blocking the connection
                            """)
        
        # Display existing campaign if one was created
        elif st.session_state.campaign_created and st.session_state.campaign_id:
            # Get campaign data
            campaign_data = campaign_manager.get_campaign(st.session_state.campaign_id)
            
            if campaign_data:
                st.markdown("### Existing Campaign")
                st.markdown(f"**Campaign ID**: {campaign_data['campaign_id']}")
                st.markdown(f"**Campaign Name**: {campaign_data['campaign_name']}")
                st.markdown(f"**Campaign Type**: {campaign_data['campaign_type']}")
                st.markdown(f"**Target**: {campaign_data['target_description']}")
                st.markdown(f"**Status**: {campaign_data['status']}")
                
                # Display execution results if available
                if campaign_data['status'] in ['Executed', 'Tested']:
                    st.markdown("### Execution Results")
                    st.markdown(f"**Emails Sent**: {campaign_data['emails_sent']}")
                    
                    # Create new campaign button
                    if st.button("Create New Campaign"):
                        st.session_state.campaign_created = False
                        st.session_state.campaign_id = None
                        st.session_state.execution_results = None
                        st.rerun()
    
    with tab2:
        st.markdown('<h2 class="sub-header">Email Template Editor</h2>', unsafe_allow_html=True)
        
        # Template selection
        template_type = st.radio(
            "Template Type",
            ["Segment Templates", "Category Templates", "Custom Template"]
        )
        
        if template_type == "Segment Templates":
            # Get segment templates
            templates = EmailTemplateManager.get_segment_templates()
            
            # Select segment to edit
            segment_options = list(templates.keys())
            selected_segment = st.selectbox("Select Segment", segment_options)
            
            if selected_segment:
                template = templates[selected_segment]
                
                # Edit template
                with st.form("edit_segment_template"):
                    edited_subject = st.text_input("Subject", template['subject'])
                    edited_body = st.text_area("Body (HTML)", template['body_html'], height=300)
                    
                    # Submit button
                    submit_button = st.form_submit_button("Update Template")
                
                # Handle form submission
                if submit_button:
                    st.success(f"Template for {selected_segment} updated successfully!")
                    
                    # Update template (in a real implementation, this would save to a database)
                    templates[selected_segment]['subject'] = edited_subject
                    templates[selected_segment]['body_html'] = edited_body
                
                # Preview template
                st.markdown("### Template Preview")
                
                # Select a sample customer for preview
                if len(email_ready_customers) > 0:
                    # Find a customer in the selected segment if possible
                    segment_customers = email_ready_customers[email_ready_customers['segment_name'] == selected_segment]
                    
                    if len(segment_customers) > 0:
                        sample_customer = segment_customers.iloc[0].to_dict()
                    else:
                        sample_customer = email_ready_customers.iloc[0].to_dict()
                    
                    # Create updated template for preview
                    preview_template = {
                        'subject': edited_subject,
                        'body_html': edited_body
                    }
                    
                    create_email_preview(preview_template, sample_customer)
        
        elif template_type == "Category Templates":
            # Get category templates
            templates = EmailTemplateManager.get_category_templates()
            
            # Select category to edit
            category_options = list(templates.keys())
            selected_category = st.selectbox("Select Category", category_options)
            
            if selected_category:
                template = templates[selected_category]
                
                # Edit template
                with st.form("edit_category_template"):
                    edited_subject = st.text_input("Subject", template['subject'])
                    edited_body = st.text_area("Body (HTML)", template['body_html'], height=300)
                    
                    # Submit button
                    submit_button = st.form_submit_button("Update Template")
                
                # Handle form submission
                if submit_button:
                    st.success(f"Template for {selected_category} updated successfully!")
                    
                    # Update template (in a real implementation, this would save to a database)
                    templates[selected_category]['subject'] = edited_subject
                    templates[selected_category]['body_html'] = edited_body
                
                # Preview template
                st.markdown("### Template Preview")
                
                # Select a sample customer for preview
                if len(email_ready_customers) > 0:
                    sample_customer = email_ready_customers.iloc[0].to_dict()
                    
                    # Create updated template for preview
                    preview_template = {
                        'subject': edited_subject,
                        'body_html': edited_body
                    }
                    
                    create_email_preview(preview_template, sample_customer)
        
        else:  # Custom Template
            # Create new template
            with st.form("create_custom_template"):
                template_name = st.text_input("Template Name", "New Custom Template")
                template_subject = st.text_input("Subject", "Special Offer for {first_name}!")
                template_body = st.text_area("Body (HTML)", """
                <html>
                <body>
                    <h1>Hello {first_name},</h1>
                    <p>We have a special offer just for you!</p>
                    <p>Visit our store to enjoy exclusive discounts on your favorite products.</p>
                    <p>Best regards,<br>The Mall Team</p>
                </body>
                </html>
                """, height=300)
                
                # Submit button
                submit_button = st.form_submit_button("Create Template")
            
            # Handle form submission
            if submit_button:
                st.success(f"Custom template '{template_name}' created successfully!")
                
                # In a real implementation, this would save to a database
                
                # Preview template
                st.markdown("### Template Preview")
                
                # Select a sample customer for preview
                if len(email_ready_customers) > 0:
                    sample_customer = email_ready_customers.iloc[0].to_dict()
                    
                    # Create template for preview
                    preview_template = {
                        'subject': template_subject,
                        'body_html': template_body
                    }
                    
                    create_email_preview(preview_template, sample_customer)
    
    with tab3:
        st.markdown('<h2 class="sub-header">Campaign History</h2>', unsafe_allow_html=True)
        
        # Load real campaign history
        campaigns_df = campaign_manager.get_campaigns()
        
        if campaigns_df.empty:
            st.info("No campaigns have been created yet. Create your first campaign in the Campaign Setup tab.")
        else:
            # Format the dataframe for display
            display_df = campaigns_df.copy()
            
            # Rename columns for better display
            display_df = display_df.rename(columns={
                'campaign_id': 'Campaign ID',
                'campaign_name': 'Campaign Name',
                'campaign_type': 'Type',
                'target_description': 'Target',
                'created_date': 'Created Date',
                'executed_date': 'Execution Date',
                'emails_sent': 'Emails Sent',
                'emails_opened': 'Emails Opened',
                'emails_clicked': 'Emails Clicked',
                'status': 'Status'
            })
            
            # Calculate open and click rates
            display_df['Open Rate'] = display_df.apply(
                lambda row: f"{(row['Emails Opened'] / row['Emails Sent'] * 100):.1f}%" if row['Emails Sent'] > 0 else "0.0%", 
                axis=1
            )
            
            display_df['Click Rate'] = display_df.apply(
                lambda row: f"{(row['Emails Clicked'] / row['Emails Sent'] * 100):.1f}%" if row['Emails Sent'] > 0 else "0.0%", 
                axis=1
            )
            
            # Select columns for display
            display_df = display_df[[
                'Campaign Name', 'Created Date', 'Type', 'Target', 
                'Emails Sent', 'Open Rate', 'Click Rate', 'Status'
            ]]
            
            # Display campaign history
            st.dataframe(display_df, use_container_width=True)
            
            # Add action buttons
            selected_campaign_id = st.selectbox(
                "Select Campaign for Details",
                options=campaigns_df['campaign_id'].tolist(),
                format_func=lambda x: f"{x} - {campaigns_df[campaigns_df['campaign_id'] == x]['campaign_name'].values[0]}"
            )
            
            if selected_campaign_id:
                # Get campaign data
                campaign_data = campaign_manager.get_campaign(selected_campaign_id)
                
                if campaign_data:
                    # Display campaign details
                    st.markdown("### Campaign Details")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Campaign ID**: {campaign_data['campaign_id']}")
                        st.markdown(f"**Campaign Name**: {campaign_data['campaign_name']}")
                        st.markdown(f"**Campaign Type**: {campaign_data['campaign_type']}")
                        st.markdown(f"**Target**: {campaign_data['target_description']}")
                    
                    with col2:
                        st.markdown(f"**Created Date**: {campaign_data['created_date']}")
                        st.markdown(f"**Scheduled Date**: {campaign_data['scheduled_date'] or 'Not scheduled'}")
                        st.markdown(f"**Execution Date**: {campaign_data['executed_date'] or 'Not executed'}")
                        st.markdown(f"**Status**: {campaign_data['status']}")
                    
                    # Display email metrics
                    st.markdown("#### Email Metrics")
                    
                    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                    
                    with metric_col1:
                        st.metric("Emails Sent", campaign_data['emails_sent'])
                    
                    with metric_col2:
                        # Calculate open rate
                        open_rate = f"{(campaign_data['emails_opened'] / campaign_data['emails_sent'] * 100):.1f}%" if campaign_data['emails_sent'] > 0 else "0.0%"
                        st.metric("Emails Opened", campaign_data['emails_opened'], open_rate)
                    
                    with metric_col3:
                        # Calculate click rate
                        click_rate = f"{(campaign_data['emails_clicked'] / campaign_data['emails_sent'] * 100):.1f}%" if campaign_data['emails_sent'] > 0 else "0.0%"
                        st.metric("Emails Clicked", campaign_data['emails_clicked'], click_rate)
                    
                    with metric_col4:
                        # Calculate CTR (click-through rate)
                        ctr = f"{(campaign_data['emails_clicked'] / campaign_data['emails_opened'] * 100):.1f}%" if campaign_data['emails_opened'] > 0 else "0.0%"
                        st.metric("CTR", ctr)
                    
                    # Action buttons
                    action_col1, action_col2 = st.columns(2)
                    
                    with action_col1:
                        # Delete campaign button
                        if st.button("Delete Campaign"):
                            if campaign_manager.delete_campaign(selected_campaign_id):
                                st.success(f"Campaign {selected_campaign_id} deleted successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete campaign {selected_campaign_id}")
                    
                    with action_col2:
                        # Duplicate campaign button
                        if st.button("Duplicate Campaign"):
                            # Create a new campaign with the same data but a new ID
                            new_campaign_id = campaign_manager.create_campaign(
                                campaign_name=f"Copy of {campaign_data['campaign_name']}",
                                campaign_type=campaign_data['campaign_type'],
                                target_description=campaign_data['target_description'],
                                templates=campaign_data['templates'],
                                target_data=campaign_data['target_data'],
                                email_config=campaign_data['email_config']
                            )
                            
                            st.success(f"Campaign duplicated successfully with new ID: {new_campaign_id}")
                            st.rerun()
            
            # Campaign performance metrics
            stats = campaign_manager.get_campaign_stats()
            
            st.markdown("### Campaign Performance")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Campaigns", stats['total_campaigns'])
            
            with col2:
                st.metric("Total Emails Sent", stats['total_emails_sent'])
            
            with col3:
                st.metric("Average Open Rate", f"{stats['open_rate']:.1f}%")
            
            with col4:
                st.metric("Average Click Rate", f"{stats['click_rate']:.1f}%")
            
            # Campaign performance chart
            st.markdown("### Campaign Performance Trends")
            
            # Only create chart if we have campaigns with emails sent
            campaigns_with_emails = campaigns_df[campaigns_df['emails_sent'] > 0]
            
            if not campaigns_with_emails.empty:
                # Calculate rates
                campaigns_with_emails['open_rate'] = campaigns_with_emails['emails_opened'] / campaigns_with_emails['emails_sent'] * 100
                campaigns_with_emails['click_rate'] = campaigns_with_emails['emails_clicked'] / campaigns_with_emails['emails_sent'] * 100
                
                # Sort by execution date
                campaigns_with_emails = campaigns_with_emails.sort_values('executed_date')
                
                # Create chart data
                chart_data = pd.DataFrame({
                    'Campaign': campaigns_with_emails['campaign_name'],
                    'Open Rate': campaigns_with_emails['open_rate'],
                    'Click Rate': campaigns_with_emails['click_rate']
                })
                
                # Create chart
                chart = pd.melt(
                    chart_data,
                    id_vars=['Campaign'],
                    value_vars=['Open Rate', 'Click Rate'],
                    var_name='Metric',
                    value_name='Rate'
                )
                
                # Display chart
                st.bar_chart(chart, x='Campaign', y='Rate', color='Metric', use_container_width=True)
            else:
                st.info("No campaign performance data available yet.")

if __name__ == "__main__":
    main() 