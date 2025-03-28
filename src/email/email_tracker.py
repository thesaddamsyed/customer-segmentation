"""
Email Tracker for tracking email opens and clicks.

This module provides functionality to generate tracking links and pixels for emails,
and to record email opens and clicks.
"""
import os
import pandas as pd
import json
import uuid
import base64
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Placeholder for a proper tracking server
TRACKING_BASE_URL = "https://example.com/tracking"

class EmailTracker:
    """
    Class for tracking email opens and clicks.
    """
    
    def __init__(self, data_dir: str = "data/email_tracking"):
        """
        Initialize the EmailTracker class.
        
        Args:
            data_dir: Directory to store tracking data
        """
        self.data_dir = data_dir
        self.opens_file = os.path.join(data_dir, "opens.csv")
        self.clicks_file = os.path.join(data_dir, "clicks.csv")
        
        # Create directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Create tracking files if they don't exist
        self._create_tracking_files()
    
    def _create_tracking_files(self):
        """
        Create tracking CSV files with headers if they don't exist.
        """
        # Create opens file if it doesn't exist
        if not os.path.exists(self.opens_file):
            opens_df = pd.DataFrame(columns=[
                'tracking_id', 'campaign_id', 'customer_id', 'email', 'timestamp'
            ])
            opens_df.to_csv(self.opens_file, index=False)
        
        # Create clicks file if it doesn't exist
        if not os.path.exists(self.clicks_file):
            clicks_df = pd.DataFrame(columns=[
                'tracking_id', 'campaign_id', 'customer_id', 'email', 'link_id', 'link_url', 'timestamp'
            ])
            clicks_df.to_csv(self.clicks_file, index=False)
    
    def generate_tracking_pixel(self, campaign_id: str, customer_id: str, email: str) -> Tuple[str, str]:
        """
        Generate a tracking pixel for an email.
        
        Args:
            campaign_id: Campaign ID
            customer_id: Customer ID
            email: Customer email address
            
        Returns:
            Tuple of (tracking ID, tracking pixel HTML)
        """
        # Generate tracking ID
        tracking_id = str(uuid.uuid4())
        
        # Use a fallback ID if customer_id is None or empty
        safe_customer_id = customer_id if customer_id else f"unknown-{tracking_id[:8]}"
        
        # Generate tracking URL
        tracking_url = f"{TRACKING_BASE_URL}/open?tid={tracking_id}&cid={campaign_id}&uid={safe_customer_id}"
        
        # Generate tracking pixel HTML
        tracking_pixel = f'<img src="{tracking_url}" width="1" height="1" alt="" style="display:none;">'
        
        return tracking_id, tracking_pixel
    
    def generate_tracking_links(self, campaign_id: str, customer_id: str, email: str, 
                              html_content: str, links: List[str]) -> Tuple[str, Dict[str, str]]:
        """
        Replace links in HTML content with tracking links.
        
        Args:
            campaign_id: Campaign ID
            customer_id: Customer ID
            email: Customer email address
            html_content: HTML content with links
            links: List of links to track
            
        Returns:
            Tuple of (modified HTML content, dictionary mapping tracking IDs to original links)
        """
        # Dictionary to store tracking links
        tracking_links = {}
        
        # Modified HTML content
        modified_html = html_content
        
        # Use a fallback ID if customer_id is None or empty
        safe_customer_id = customer_id if customer_id else f"unknown-{str(uuid.uuid4())[:8]}"
        
        # Replace each link with a tracking link
        for link in links:
            # Generate tracking ID
            tracking_id = str(uuid.uuid4())
            
            # Generate tracking URL
            tracking_url = f"{TRACKING_BASE_URL}/click?tid={tracking_id}&cid={campaign_id}&uid={safe_customer_id}&url={base64.urlsafe_b64encode(link.encode()).decode()}"
            
            # Replace link in HTML content
            modified_html = modified_html.replace(f'href="{link}"', f'href="{tracking_url}"')
            
            # Store tracking link
            tracking_links[tracking_id] = link
        
        return modified_html, tracking_links
    
    def record_open(self, tracking_id: str, campaign_id: str, customer_id: str, email: str) -> bool:
        """
        Record an email open.
        
        Args:
            tracking_id: Tracking ID
            campaign_id: Campaign ID
            customer_id: Customer ID
            email: Customer email address
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing opens
            opens_df = pd.read_csv(self.opens_file)
            
            # Create new row
            new_row = pd.DataFrame({
                'tracking_id': [tracking_id],
                'campaign_id': [campaign_id],
                'customer_id': [customer_id],
                'email': [email],
                'timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            })
            
            # Append new row
            opens_df = pd.concat([opens_df, new_row], ignore_index=True)
            
            # Save updated CSV
            opens_df.to_csv(self.opens_file, index=False)
            
            return True
        
        except Exception as e:
            print(f"Error recording email open: {str(e)}")
            return False
    
    def record_click(self, tracking_id: str, campaign_id: str, customer_id: str, 
                    email: str, link_id: str, link_url: str) -> bool:
        """
        Record an email link click.
        
        Args:
            tracking_id: Tracking ID
            campaign_id: Campaign ID
            customer_id: Customer ID
            email: Customer email address
            link_id: Link ID
            link_url: Original link URL
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing clicks
            clicks_df = pd.read_csv(self.clicks_file)
            
            # Create new row
            new_row = pd.DataFrame({
                'tracking_id': [tracking_id],
                'campaign_id': [campaign_id],
                'customer_id': [customer_id],
                'email': [email],
                'link_id': [link_id],
                'link_url': [link_url],
                'timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            })
            
            # Append new row
            clicks_df = pd.concat([clicks_df, new_row], ignore_index=True)
            
            # Save updated CSV
            clicks_df.to_csv(self.clicks_file, index=False)
            
            return True
        
        except Exception as e:
            print(f"Error recording email click: {str(e)}")
            return False
    
    def get_open_stats(self, campaign_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get statistics on email opens.
        
        Args:
            campaign_id: Campaign ID (optional, if not provided returns stats for all campaigns)
            
        Returns:
            DataFrame with open statistics
        """
        try:
            # Load opens
            opens_df = pd.read_csv(self.opens_file)
            
            # Filter by campaign if provided
            if campaign_id:
                opens_df = opens_df[opens_df['campaign_id'] == campaign_id]
            
            return opens_df
        
        except Exception as e:
            print(f"Error getting open statistics: {str(e)}")
            return pd.DataFrame()
    
    def get_click_stats(self, campaign_id: Optional[str] = None) -> pd.DataFrame:
        """
        Get statistics on email clicks.
        
        Args:
            campaign_id: Campaign ID (optional, if not provided returns stats for all campaigns)
            
        Returns:
            DataFrame with click statistics
        """
        try:
            # Load clicks
            clicks_df = pd.read_csv(self.clicks_file)
            
            # Filter by campaign if provided
            if campaign_id:
                clicks_df = clicks_df[clicks_df['campaign_id'] == campaign_id]
            
            return clicks_df
        
        except Exception as e:
            print(f"Error getting click statistics: {str(e)}")
            return pd.DataFrame()
    
    def update_campaign_stats(self, campaign_id: str) -> Dict[str, int]:
        """
        Update statistics for a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Dictionary with updated statistics
        """
        # Get open and click stats
        opens_df = self.get_open_stats(campaign_id)
        clicks_df = self.get_click_stats(campaign_id)
        
        # Count unique customers who opened emails
        unique_opens = len(opens_df['customer_id'].unique())
        
        # Count unique customers who clicked links
        unique_clicks = len(clicks_df['customer_id'].unique())
        
        return {
            'emails_opened': unique_opens,
            'emails_clicked': unique_clicks
        } 