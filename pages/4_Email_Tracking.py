"""
Email Tracking Page

This page provides tracking endpoints for email opens and clicks,
and shows tracking statistics.
"""
import os
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import base64
import urllib.parse
import json
from PIL import Image
import io

# Import custom modules
from src.email.email_tracker import EmailTracker
from src.email.campaign_manager import CampaignManager

# Set page configuration
st.set_page_config(
    page_title="Email Tracking - Mall Customer Segmentation",
    page_icon="📊",
    layout="wide"
)

# Create required directories
os.makedirs("data", exist_ok=True)
os.makedirs("data/campaigns", exist_ok=True)
os.makedirs("data/campaigns/results", exist_ok=True)
os.makedirs("data/email_tracking", exist_ok=True)

# Initialize trackers
email_tracker = EmailTracker()
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
        .metric-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 1.2rem 0.8rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
            margin-bottom: 1rem;
            min-height: 110px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            overflow: hidden;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: bold;
            color: #4527A0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #6c757d;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
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

# Create a 1x1 pixel image for tracking
def create_tracking_pixel():
    """Create a 1x1 transparent pixel for tracking email opens"""
    img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()

# Main function
def main():
    # Load CSS
    load_css()
    
    # Get the query parameters
    query_params = st.query_params
    
    # Check if this is a tracking request
    if 'action' in query_params and query_params['action'] in ['open', 'click']:
        # Handle tracking request
        action = query_params['action']
        
        if action == 'open' and all(param in query_params for param in ['tid', 'cid', 'uid']):
            # Record email open
            tracking_id = query_params['tid']
            campaign_id = query_params['cid']
            customer_id = query_params['uid']
            email = query_params.get('email', 'unknown@example.com')
            
            # Record the open
            email_tracker.record_open(tracking_id, campaign_id, customer_id, email)
            
            # Update campaign stats
            stats = email_tracker.update_campaign_stats(campaign_id)
            campaign_manager.update_campaign_status(campaign_id, "Tracked", stats)
            
            # Return a tracking pixel
            st.image(create_tracking_pixel(), width=1)
            
        elif action == 'click' and all(param in query_params for param in ['tid', 'cid', 'uid', 'url']):
            # Record email click
            tracking_id = query_params['tid']
            campaign_id = query_params['cid']
            customer_id = query_params['uid']
            email = query_params.get('email', 'unknown@example.com')
            link_id = query_params.get('lid', 'unknown')
            
            # Decode URL
            encoded_url = query_params['url']
            try:
                url = base64.urlsafe_b64decode(encoded_url.encode()).decode()
            except:
                url = "unknown"
            
            # Record the click
            email_tracker.record_click(tracking_id, campaign_id, customer_id, email, link_id, url)
            
            # Update campaign stats
            stats = email_tracker.update_campaign_stats(campaign_id)
            campaign_manager.update_campaign_status(campaign_id, "Tracked", stats)
            
            # Redirect to the original URL
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{url}\'">', unsafe_allow_html=True)
        
        else:
            st.error("Invalid tracking request")
    
    else:
        # Display the normal page content
        st.markdown('<h1 class="main-header">Email Tracking</h1>', unsafe_allow_html=True)
        
        # Add explanation about email tracking
        with st.expander("How Email Tracking Works", expanded=False):
            st.markdown("""
            ### Understanding Email Tracking
            
            This page provides tracking information for your email campaigns. Here's how it works:
            
            **1. Open Tracking:** 
            - A tiny invisible pixel is added to each email
            - When recipients open the email, this pixel loads, registering an "open"
            - This allows us to see who opened your email and when
            
            **2. Click Tracking:**
            - Links in your emails are replaced with tracking links
            - When recipients click these links, we record the click before redirecting them
            - This lets you see which links are most effective
            
            **3. Campaign Performance:**
            - Track open rates, click rates, and click-through rates
            - See which segments respond best to your campaigns
            - Analyze the best times for engagement
            
            **Privacy Note:** Email tracking is a standard practice in email marketing, but it's good to be transparent with your customers about your tracking methods.
            """)
        
        # Create tabs for different tracking functions
        tab1, tab2 = st.tabs(["Campaign Tracking", "Tracking Analytics"])
        
        with tab1:
            st.markdown('<h2 class="sub-header">Campaign Tracking</h2>', unsafe_allow_html=True)
            
            # Get campaigns
            campaigns_df = campaign_manager.get_campaigns()
            
            if campaigns_df.empty:
                st.info("No campaigns have been created yet.")
            else:
                # Display all campaigns
                st.markdown("### All Campaigns")
                
                # Format dataframe for display
                display_df = campaigns_df.copy()
                
                # Rename columns
                display_df = display_df.rename(columns={
                    'campaign_id': 'Campaign ID',
                    'campaign_name': 'Campaign Name',
                    'campaign_type': 'Type',
                    'emails_sent': 'Emails Sent',
                    'emails_opened': 'Opens',
                    'emails_clicked': 'Clicks',
                    'created_date': 'Created Date',
                    'executed_date': 'Executed Date',
                    'status': 'Status'
                })
                
                # Calculate rates for campaigns with emails sent
                display_df['Open Rate'] = display_df.apply(
                    lambda row: f"{(row['Opens'] / row['Emails Sent'] * 100):.1f}%" if row['Emails Sent'] > 0 else "N/A",
                    axis=1
                )
                
                display_df['Click Rate'] = display_df.apply(
                    lambda row: f"{(row['Clicks'] / row['Emails Sent'] * 100):.1f}%" if row['Emails Sent'] > 0 else "N/A",
                    axis=1
                )
                
                display_df['CTR'] = display_df.apply(
                    lambda row: f"{(row['Clicks'] / row['Opens'] * 100):.1f}%" if row['Opens'] > 0 else "N/A",
                    axis=1
                )
                
                # Select columns for display
                display_df = display_df[[
                    'Campaign Name', 'Created Date', 'Executed Date', 'Status', 'Emails Sent', 
                    'Opens', 'Open Rate', 'Clicks', 'Click Rate'
                ]]
                
                # Display dataframe
                st.dataframe(display_df, use_container_width=True)
                
                # Filter campaigns with emails sent for detailed tracking
                campaigns_with_emails = campaigns_df[campaigns_df['emails_sent'] > 0]
                
                if campaigns_with_emails.empty:
                    st.info("No campaigns have sent emails yet. Execute a campaign to see detailed tracking.")
                else:
                    # Select campaign for detailed tracking
                    st.markdown("### Detailed Email Tracking")
                    st.info("Select a campaign that has sent emails to view detailed tracking information.")
                    
                    selected_campaign_id = st.selectbox(
                        "Select Campaign for Detailed Tracking",
                        options=campaigns_with_emails['campaign_id'].tolist(),
                        format_func=lambda x: f"{x} - {campaigns_with_emails[campaigns_with_emails['campaign_id'] == x]['campaign_name'].values[0]}"
                    )
                    
                    if selected_campaign_id:
                        # Get campaign data
                        campaign_data = campaign_manager.get_campaign(selected_campaign_id)
                        
                        if campaign_data:
                            # Display campaign metrics
                            st.markdown("### Campaign Metrics")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Emails Sent", campaign_data['emails_sent'])
                            
                            with col2:
                                open_rate = f"{(campaign_data['emails_opened'] / campaign_data['emails_sent'] * 100):.1f}%" if campaign_data['emails_sent'] > 0 else "0.0%"
                                st.metric("Opens", campaign_data['emails_opened'], open_rate)
                            
                            with col3:
                                click_rate = f"{(campaign_data['emails_clicked'] / campaign_data['emails_sent'] * 100):.1f}%" if campaign_data['emails_sent'] > 0 else "0.0%"
                                st.metric("Clicks", campaign_data['emails_clicked'], click_rate)
                            
                            with col4:
                                ctr = f"{(campaign_data['emails_clicked'] / campaign_data['emails_opened'] * 100):.1f}%" if campaign_data['emails_opened'] > 0 else "0.0%"
                                st.metric("CTR", ctr)
                            
                            # Get detailed tracking data
                            opens_df = email_tracker.get_open_stats(selected_campaign_id)
                            clicks_df = email_tracker.get_click_stats(selected_campaign_id)
                            
                            # Display opens over time
                            if not opens_df.empty:
                                st.markdown("### Opens Over Time")
                                
                                # Convert timestamp to datetime
                                opens_df['timestamp'] = pd.to_datetime(opens_df['timestamp'])
                                
                                # Group by date and count opens
                                opens_by_date = opens_df.groupby(opens_df['timestamp'].dt.date).size().reset_index(name='opens')
                                
                                # Create chart
                                fig = px.line(
                                    opens_by_date,
                                    x='timestamp',
                                    y='opens',
                                    title="Email Opens Over Time",
                                    labels={'timestamp': 'Date', 'opens': 'Number of Opens'}
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Display clicks over time
                            if not clicks_df.empty:
                                st.markdown("### Clicks Over Time")
                                
                                # Convert timestamp to datetime
                                clicks_df['timestamp'] = pd.to_datetime(clicks_df['timestamp'])
                                
                                # Group by date and count clicks
                                clicks_by_date = clicks_df.groupby(clicks_df['timestamp'].dt.date).size().reset_index(name='clicks')
                                
                                # Create chart
                                fig = px.line(
                                    clicks_by_date,
                                    x='timestamp',
                                    y='clicks',
                                    title="Email Clicks Over Time",
                                    labels={'timestamp': 'Date', 'clicks': 'Number of Clicks'}
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Display most clicked links
                                st.markdown("### Most Clicked Links")
                                
                                # Group by link URL and count clicks
                                links_df = clicks_df.groupby('link_url').size().reset_index(name='clicks')
                                links_df = links_df.sort_values('clicks', ascending=False).head(10)
                                
                                # Create chart
                                fig = px.bar(
                                    links_df,
                                    x='clicks',
                                    y='link_url',
                                    title="Most Clicked Links",
                                    labels={'clicks': 'Number of Clicks', 'link_url': 'Link URL'},
                                    orientation='h'
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.markdown('<h2 class="sub-header">Tracking Analytics</h2>', unsafe_allow_html=True)
            
            # Get all tracking data
            opens_df = email_tracker.get_open_stats()
            clicks_df = email_tracker.get_click_stats()
            
            if opens_df.empty and clicks_df.empty:
                st.info("No tracking data available yet.")
            else:
                # Overall metrics
                st.markdown("### Overall Tracking Metrics")
                
                # Calculate metrics
                total_opens = len(opens_df)
                total_clicks = len(clicks_df)
                unique_opens = len(opens_df['customer_id'].unique()) if not opens_df.empty else 0
                unique_clicks = len(clicks_df['customer_id'].unique()) if not clicks_df.empty else 0
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Opens", total_opens)
                
                with col2:
                    st.metric("Unique Opens", unique_opens)
                
                with col3:
                    st.metric("Total Clicks", total_clicks)
                
                with col4:
                    st.metric("Unique Clicks", unique_clicks)
                
                # Display opens over time
                if not opens_df.empty:
                    st.markdown("### Overall Opens Over Time")
                    
                    # Convert timestamp to datetime
                    opens_df['timestamp'] = pd.to_datetime(opens_df['timestamp'])
                    
                    # Group by date and count opens
                    opens_by_date = opens_df.groupby(opens_df['timestamp'].dt.date).size().reset_index(name='opens')
                    
                    # Create chart
                    fig = px.line(
                        opens_by_date,
                        x='timestamp',
                        y='opens',
                        title="Email Opens Over Time (All Campaigns)",
                        labels={'timestamp': 'Date', 'opens': 'Number of Opens'}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Display clicks over time
                if not clicks_df.empty:
                    st.markdown("### Overall Clicks Over Time")
                    
                    # Convert timestamp to datetime
                    clicks_df['timestamp'] = pd.to_datetime(clicks_df['timestamp'])
                    
                    # Group by date and count clicks
                    clicks_by_date = clicks_df.groupby(clicks_df['timestamp'].dt.date).size().reset_index(name='clicks')
                    
                    # Create chart
                    fig = px.line(
                        clicks_by_date,
                        x='timestamp',
                        y='clicks',
                        title="Email Clicks Over Time (All Campaigns)",
                        labels={'timestamp': 'Date', 'clicks': 'Number of Clicks'}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main() 