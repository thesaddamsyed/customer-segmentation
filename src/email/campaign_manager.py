"""
Campaign Manager for email marketing campaigns.

This module handles the storage, tracking, and management of email marketing campaigns.
"""
import os
import pandas as pd
import numpy as np
import json
from datetime import datetime
from typing import Dict, List, Optional, Union
import csv


class CampaignManager:
    """
    Class for managing email marketing campaigns.
    """
    
    def __init__(self, data_dir: str = "data/campaigns"):
        """
        Initialize the CampaignManager class.
        
        Args:
            data_dir: Directory to store campaign data
        """
        self.data_dir = data_dir
        self.campaigns_file = os.path.join(data_dir, "campaigns.csv")
        self.campaign_results_dir = os.path.join(data_dir, "results")
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.campaign_results_dir, exist_ok=True)
        
        # Create campaigns file if it doesn't exist
        if not os.path.exists(self.campaigns_file):
            self._create_campaigns_file()
    
    def _create_campaigns_file(self):
        """
        Create the campaigns CSV file with headers.
        """
        with open(self.campaigns_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                'campaign_id', 
                'campaign_name', 
                'campaign_type', 
                'target_description', 
                'created_date',
                'scheduled_date',
                'executed_date',
                'emails_sent',
                'emails_opened',
                'emails_clicked',
                'status'
            ])
    
    def create_campaign(self, 
                       campaign_name: str, 
                       campaign_type: str, 
                       target_description: str,
                       templates: Dict,
                       target_data: Dict,
                       email_config: Dict,
                       scheduled_date: Optional[str] = None) -> str:
        """
        Create a new campaign and save its data.
        
        Args:
            campaign_name: Name of the campaign
            campaign_type: Type of campaign (segment-based, category-based, custom)
            target_description: Description of the target audience
            templates: Dictionary of email templates
            target_data: Dictionary of target data
            email_config: Dictionary of email configuration
            scheduled_date: Date to schedule the campaign (optional)
            
        Returns:
            Campaign ID
        """
        # Generate campaign ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        campaign_id = f"CAMP{timestamp}"
        
        # Create campaign data
        campaign_data = {
            'campaign_id': campaign_id,
            'campaign_name': campaign_name,
            'campaign_type': campaign_type,
            'target_description': target_description,
            'created_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'scheduled_date': scheduled_date,
            'executed_date': None,
            'emails_sent': 0,
            'emails_opened': 0,
            'emails_clicked': 0,
            'status': 'Created',
            'templates': templates,
            'target_data': target_data,
            'email_config': email_config
        }
        
        # Save campaign data
        self._save_campaign_data(campaign_id, campaign_data)
        
        # Add campaign to campaigns file
        self._add_campaign_to_csv(campaign_data)
        
        return campaign_id
    
    def _save_campaign_data(self, campaign_id: str, campaign_data: Dict):
        """
        Save campaign data to a JSON file.
        
        Args:
            campaign_id: Campaign ID
            campaign_data: Campaign data
        """
        # Create file path
        file_path = os.path.join(self.data_dir, f"{campaign_id}.json")
        
        # Save data
        with open(file_path, 'w') as file:
            json.dump(campaign_data, file, indent=2)
    
    def _add_campaign_to_csv(self, campaign_data: Dict):
        """
        Add a campaign to the campaigns CSV file.
        
        Args:
            campaign_data: Campaign data
        """
        # Extract data to write to CSV
        row = [
            campaign_data['campaign_id'],
            campaign_data['campaign_name'],
            campaign_data['campaign_type'],
            campaign_data['target_description'],
            campaign_data['created_date'],
            campaign_data['scheduled_date'] or '',
            campaign_data['executed_date'] or '',
            campaign_data['emails_sent'],
            campaign_data['emails_opened'],
            campaign_data['emails_clicked'],
            campaign_data['status']
        ]
        
        # Append to CSV
        with open(self.campaigns_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)
    
    def get_campaigns(self) -> pd.DataFrame:
        """
        Get all campaigns.
        
        Returns:
            DataFrame with campaign data
        """
        if os.path.exists(self.campaigns_file):
            return pd.read_csv(self.campaigns_file)
        return pd.DataFrame()
    
    def get_campaign(self, campaign_id: str) -> Dict:
        """
        Get campaign data by ID.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Campaign data
        """
        file_path = os.path.join(self.data_dir, f"{campaign_id}.json")
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return json.load(file)
        
        return {}
    
    def update_campaign_status(self, campaign_id: str, status: str, results: Optional[Dict] = None):
        """
        Update campaign status and results.
        
        Args:
            campaign_id: Campaign ID
            status: New status
            results: Campaign results (optional)
        """
        # Get campaign data
        campaign_data = self.get_campaign(campaign_id)
        
        if not campaign_data:
            return
        
        # Update status
        campaign_data['status'] = status
        
        # Update results if provided
        if results:
            if status == 'Executed':
                campaign_data['executed_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                campaign_data['emails_sent'] = results.get('emails_sent', 0)
                campaign_data['emails_opened'] = results.get('emails_opened', 0)
                campaign_data['emails_clicked'] = results.get('emails_clicked', 0)
            
            # Save results data
            self._save_campaign_results(campaign_id, results)
        
        # Save updated campaign data
        self._save_campaign_data(campaign_id, campaign_data)
        
        # Update campaigns CSV
        self._update_campaign_in_csv(campaign_data)
    
    def _save_campaign_results(self, campaign_id: str, results: Dict):
        """
        Save campaign results to a JSON file.
        
        Args:
            campaign_id: Campaign ID
            results: Campaign results
        """
        # Create file path
        file_path = os.path.join(self.campaign_results_dir, f"{campaign_id}_results.json")
        
        # Save data
        with open(file_path, 'w') as file:
            json.dump(results, file, indent=2)
    
    def _update_campaign_in_csv(self, campaign_data: Dict):
        """
        Update a campaign in the campaigns CSV file.
        
        Args:
            campaign_data: Campaign data
        """
        # Read existing data
        campaigns_df = pd.read_csv(self.campaigns_file)
        
        # Find campaign by ID
        mask = campaigns_df['campaign_id'] == campaign_data['campaign_id']
        
        if mask.any():
            # Update fields
            campaigns_df.loc[mask, 'status'] = campaign_data['status']
            
            if campaign_data.get('executed_date'):
                campaigns_df.loc[mask, 'executed_date'] = campaign_data['executed_date']
                campaigns_df.loc[mask, 'emails_sent'] = campaign_data['emails_sent']
                campaigns_df.loc[mask, 'emails_opened'] = campaign_data['emails_opened']
                campaigns_df.loc[mask, 'emails_clicked'] = campaign_data['emails_clicked']
            
            # Save updated CSV
            campaigns_df.to_csv(self.campaigns_file, index=False)
    
    def delete_campaign(self, campaign_id: str) -> bool:
        """
        Delete a campaign.
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            True if successful, False otherwise
        """
        # Check if campaign exists
        file_path = os.path.join(self.data_dir, f"{campaign_id}.json")
        
        if not os.path.exists(file_path):
            return False
        
        # Delete campaign file
        os.remove(file_path)
        
        # Delete results file if it exists
        results_path = os.path.join(self.campaign_results_dir, f"{campaign_id}_results.json")
        if os.path.exists(results_path):
            os.remove(results_path)
        
        # Remove from campaigns CSV
        campaigns_df = pd.read_csv(self.campaigns_file)
        campaigns_df = campaigns_df[campaigns_df['campaign_id'] != campaign_id]
        campaigns_df.to_csv(self.campaigns_file, index=False)
        
        return True
    
    def get_campaign_stats(self) -> Dict:
        """
        Get overall campaign statistics.
        
        Returns:
            Dictionary with campaign statistics
        """
        campaigns_df = self.get_campaigns()
        
        if campaigns_df.empty:
            return {
                'total_campaigns': 0,
                'total_emails_sent': 0,
                'open_rate': 0,
                'click_rate': 0
            }
        
        # Calculate statistics
        total_campaigns = len(campaigns_df)
        total_emails_sent = campaigns_df['emails_sent'].sum()
        
        # Avoid division by zero
        if total_emails_sent > 0:
            open_rate = (campaigns_df['emails_opened'].sum() / total_emails_sent) * 100
            click_rate = (campaigns_df['emails_clicked'].sum() / total_emails_sent) * 100
        else:
            open_rate = 0
            click_rate = 0
        
        return {
            'total_campaigns': total_campaigns,
            'total_emails_sent': total_emails_sent,
            'open_rate': open_rate,
            'click_rate': click_rate
        } 