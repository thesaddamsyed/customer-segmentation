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

# Import custom modules
from src.data_processing.data_loader import load_and_process
from src.segmentation.segmentation import CustomerSegmentation
from src.email.email_sender import EmailSender, EmailTemplateManager

# Set page configuration
st.set_page_config(
    page_title="Email Marketing - Mall Customer Segmentation",
    page_icon="📧",
    layout="wide"
)

# Define paths
DATA_PATH = "project2.csv"
PROCESSED_DATA_PATH = "data/processed_customer_features.csv"
MODEL_PATH = "models/segmentation_model"

# Custom CSS
def load_css():
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #4527A0;
            text-align: center;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #5E35B1;
            margin-bottom: 1rem;
        }
        .email-preview {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
            border: 1px solid #e0e0e0;
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
        }
        .email-from {
            color: #666;
            font-size: 0.9rem;
        }
        .email-to {
            color: #666;
            font-size: 0.9rem;
        }
        .email-body {
            padding: 1rem 0;
        }
        .template-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
            cursor: pointer;
            transition: transform 0.2s;
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
                segment_options = segment_profiles['segment_name'].tolist()
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
            
            # Email configuration
            st.markdown("#### Email Configuration")
            
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
                st.success(f"Campaign '{campaign_name}' set up successfully!")
                
                # Display campaign summary
                st.markdown("### Campaign Summary")
                
                if campaign_type == "Segment-based":
                    # Count customers in each segment
                    segment_counts = {
                        segment: len(customer_segments[customer_segments['segment_name'] == segment])
                        for segment in target_segments
                    }
                    
                    # Display segment counts
                    st.markdown("#### Target Segments")
                    for segment, count in segment_counts.items():
                        st.markdown(f"- **{segment}**: {count} customers")
                    
                    # Total customers
                    total_customers = sum(segment_counts.values())
                    st.markdown(f"**Total Customers**: {total_customers}")
                    
                elif campaign_type == "Category-based":
                    # Count customers for each category
                    category_counts = {}
                    filtered_customers = pd.DataFrame()
                    
                    for display_category in target_categories:
                        # Convert display category back to database format
                        db_category = display_category.lower().replace(' ', '_')
                        
                        # Count customers with this primary category
                        category_customers = customer_segments[customer_segments['primary_category'] == db_category]
                        count = len(category_customers)
                        category_counts[display_category] = count
                        
                        # Add these customers to our filtered list
                        if not category_customers.empty:
                            if filtered_customers.empty:
                                filtered_customers = category_customers
                            else:
                                filtered_customers = pd.concat([filtered_customers, category_customers])
                    
                    # Display category counts
                    st.markdown("#### Target Categories")
                    for category, count in category_counts.items():
                        st.markdown(f"- **{category}**: {count} customers")
                    
                    # Total customers
                    total_customers = sum(category_counts.values())
                    st.markdown(f"**Total Customers**: {total_customers}")
                    
                    # Remove duplicates
                    if not filtered_customers.empty:
                        filtered_customers = filtered_customers.drop_duplicates()
                        # Prepare customer data for email templates
                        email_ready_customers = EmailTemplateManager.prepare_customer_data_for_email(filtered_customers)
                
                else:  # Custom campaign
                    # Filter customers based on custom criteria
                    filtered_customers = customer_segments.copy()
                    
                    if 'age' in filtered_customers.columns:
                        filtered_customers = filtered_customers[
                            (filtered_customers['age'] >= age_min) &
                            (filtered_customers['age'] <= age_max)
                        ]
                    
                    if target_cities and 'city' in filtered_customers.columns:
                        filtered_customers = filtered_customers[filtered_customers['city'].isin(target_cities)]
                    
                    if target_genders and 'gender' in filtered_customers.columns:
                        filtered_customers = filtered_customers[filtered_customers['gender'].isin(target_genders)]
                    
                    # Display custom criteria
                    st.markdown("#### Target Criteria")
                    st.markdown(f"- **Age Range**: {age_min} to {age_max}")
                    st.markdown(f"- **Cities**: {', '.join(target_cities)}")
                    st.markdown(f"- **Genders**: {', '.join(target_genders)}")
                    
                    # Total customers
                    total_customers = len(filtered_customers)
                    st.markdown(f"**Total Customers**: {total_customers}")
                    
                    # Prepare customer data for email templates
                    if not filtered_customers.empty:
                        email_ready_customers = EmailTemplateManager.prepare_customer_data_for_email(filtered_customers)
                
                # Display email preview
                st.markdown("### Email Preview")
                
                # Select a sample customer for preview
                if len(email_ready_customers) > 0:
                    sample_customer = email_ready_customers.iloc[0].to_dict()
                    
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
                    
                    # Display test results
                    st.markdown("#### Test Results")
                    st.markdown(f"- **Total Emails**: {min(total_customers, max_emails)}")
                    st.markdown(f"- **Status**: Success (Test Mode)")
                    
                else:
                    # Create email sender
                    try:
                        email_sender = EmailSender(
                            host=email_host,
                            port=email_port,
                            username=email_user,
                            password=email_password
                        )
                        
                        st.success("Email configuration validated successfully!")
                        
                        # Execute campaign button
                        if st.button("Execute Campaign"):
                            st.warning("This would send real emails if not in test mode.")
                            
                            # In a real implementation, this would send the emails
                            # For now, we'll just simulate it
                            st.success(f"Campaign executed successfully! {min(total_customers, max_emails)} emails would be sent.")
                            
                    except Exception as e:
                        st.error(f"Email configuration error: {str(e)}")
    
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
        
        # In a real implementation, this would load campaign history from a database
        # For now, we'll display a sample history
        
        # Create sample campaign history
        campaign_history = pd.DataFrame({
            'Campaign Name': [
                'VIP Customer Appreciation',
                'Win-back Campaign',
                'New Product Launch',
                'Holiday Special'
            ],
            'Date': [
                '2023-12-15',
                '2023-11-20',
                '2023-10-05',
                '2023-09-10'
            ],
            'Type': [
                'Segment-based',
                'Segment-based',
                'Category-based',
                'Custom'
            ],
            'Target': [
                'VIP',
                'At Risk',
                'Electronics',
                'All Customers'
            ],
            'Emails Sent': [
                120,
                85,
                210,
                450
            ],
            'Open Rate': [
                '45%',
                '32%',
                '38%',
                '41%'
            ],
            'Click Rate': [
                '12%',
                '8%',
                '15%',
                '10%'
            ]
        })
        
        # Display campaign history
        st.dataframe(campaign_history, use_container_width=True)
        
        # Campaign performance metrics
        st.markdown("### Campaign Performance")
        
        # Create sample metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Campaigns", "4")
        
        with col2:
            st.metric("Total Emails Sent", "865")
        
        with col3:
            st.metric("Average Open Rate", "39%")
        
        with col4:
            st.metric("Average Click Rate", "11%")
        
        # Campaign performance chart
        st.markdown("### Campaign Performance Trends")
        
        # Create sample data for chart
        chart_data = pd.DataFrame({
            'Campaign': campaign_history['Campaign Name'],
            'Open Rate': [45, 32, 38, 41],
            'Click Rate': [12, 8, 15, 10]
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
        
        st.info("This is a sample campaign history. In a real implementation, this would show actual campaign data.")

if __name__ == "__main__":
    main() 