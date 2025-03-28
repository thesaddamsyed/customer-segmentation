"""
Email sender module for sending automated emails to customers.
"""
import os
import smtplib
import pandas as pd
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Optional
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from dotenv import load_dotenv
import logging
import numpy as np

# Import email tracker
from src.email.email_tracker import EmailTracker


class EmailSender:
    """
    Class for sending automated emails to customers.
    """
    
    def __init__(self, host="localhost", port=25, username="", password="", enable_tracking=True):
        """
        Initialize the email sender with SMTP settings.
        
        Args:
            host (str): SMTP host server
            port (int): SMTP port (usually 587 for TLS or 465 for SSL)
            username (str): SMTP username
            password (str): SMTP password
            enable_tracking (bool): Whether to enable tracking of email opens and clicks
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.enable_tracking = enable_tracking
        self.tracker = EmailTracker() if enable_tracking else None
        self.logger = self._setup_logger()
        
        # Determine connection type based on port
        self.use_ssl = (self.port == 465)
    
    def _setup_logger(self):
        """Set up a logger for the email sender."""
        logger = logging.getLogger("EmailSender")
        logger.setLevel(logging.INFO)
        
        # Create handler if it doesn't exist
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _validate_email(self, email):
        """
        Validate an email address format.
        
        Args:
            email (str): Email address to validate
            
        Returns:
            bool: True if the email address is valid, False otherwise
        """
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False
    
    def _extract_links(self, html_content: str) -> List[str]:
        """
        Extract links from HTML content.
        
        Args:
            html_content: HTML content
            
        Returns:
            List of links
        """
        # Regular expression to find links
        link_pattern = re.compile(r'href="(https?://[^"]+)"')
        
        # Find all links
        links = link_pattern.findall(html_content)
        
        return links
    
    def _add_tracking(self, campaign_id: str, customer_id: str, email: str, 
                     html_content: str) -> str:
        """
        Add tracking to an email.
        
        Args:
            campaign_id: Campaign ID
            customer_id: Customer ID
            email: Customer email address
            html_content: HTML content
            
        Returns:
            HTML content with tracking added
        """
        if not self.enable_tracking:
            return html_content
        
        # Extract links from HTML content
        links = self._extract_links(html_content)
        
        # Add tracking to links
        if links:
            html_content, _ = self.tracker.generate_tracking_links(
                campaign_id=campaign_id,
                customer_id=customer_id,
                email=email,
                html_content=html_content,
                links=links
            )
        
        # Add tracking pixel
        tracking_id, tracking_pixel = self.tracker.generate_tracking_pixel(
            campaign_id=campaign_id,
            customer_id=customer_id,
            email=email
        )
        
        # Add tracking pixel before </body>
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{tracking_pixel}</body>')
        else:
            html_content = f'{html_content}{tracking_pixel}'
        
        return html_content
    
    def send_email(self, to_email, subject, body_html, campaign_id=None, customer_id=None):
        """
        Send an email to a recipient with HTML content and optional tracking.
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body_html (str): HTML content of the email
            campaign_id (str, optional): Campaign ID for tracking
            customer_id (str, optional): Customer ID for tracking
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Validate email address format
            if not self._validate_email(to_email):
                self.logger.error(f"Invalid recipient email address: {to_email}")
                return False
            
            if not self._validate_email(self.username):
                self.logger.error(f"Invalid sender email address: {self.username}")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.username
            msg['To'] = to_email
            
            # Add tracking if enabled
            if self.enable_tracking and self.tracker and campaign_id and customer_id:
                try:
                    self.logger.info(f"Adding tracking for campaign {campaign_id}, customer {customer_id}")
                    body_html = self.tracker.add_tracking_to_email(
                        body_html, campaign_id, customer_id
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to add tracking to email: {str(e)}")
            
            # Attach HTML part
            html_part = MIMEText(body_html, 'html')
            msg.attach(html_part)
            
            # Connect to SMTP server and send email
            self.logger.info(f"Connecting to {self.host}:{self.port} {'with SSL' if self.use_ssl else 'with TLS'}")
            
            try:
                if self.use_ssl:
                    # Use SSL connection (port 465)
                    server = smtplib.SMTP_SSL(self.host, self.port)
                else:
                    # Use TLS connection (port 587)
                    server = smtplib.SMTP(self.host, self.port)
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                
                # Login if credentials provided
                if self.username and self.password:
                    self.logger.info(f"Authenticating as {self.username}")
                    server.login(self.username, self.password)
                
                # Send email
                self.logger.info(f"Sending email to {to_email}")
                server.sendmail(self.username, to_email, msg.as_string())
                server.quit()
                
                # Log success
                self.logger.info(f"Email sent successfully to {to_email}")
                
                # Track email sent event if tracking enabled
                if self.enable_tracking and self.tracker and campaign_id and customer_id:
                    self.tracker.track_email_sent(campaign_id, customer_id)
                
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                self.logger.error(f"SMTP Authentication Error: {str(e)}")
                if "gmail" in self.host.lower():
                    self.logger.warning("Gmail requires an App Password if 2-Step Verification is enabled")
                print(f"SMTP Authentication Error: {str(e)}")
                print("If using Gmail, make sure to use an App Password and not your regular password.")
                return False
                
            except smtplib.SMTPSenderRefused as e:
                self.logger.error(f"SMTP Sender Refused: {str(e)}")
                print(f"The email server refused the sender address: {self.username}")
                return False
                
            except smtplib.SMTPRecipientsRefused as e:
                self.logger.error(f"SMTP Recipients Refused: {str(e)}")
                print(f"The email server refused the recipient address: {to_email}")
                return False
                
            except smtplib.SMTPDataError as e:
                self.logger.error(f"SMTP Data Error: {str(e)}")
                print(f"The server responded with an unexpected error code: {str(e)}")
                return False
                
            except smtplib.SMTPConnectError as e:
                self.logger.error(f"SMTP Connect Error: {str(e)}")
                print(f"Error connecting to the server: {str(e)}")
                if not self.use_ssl and self.port == 587:
                    print("Try using port 465 with SSL instead of port 587 with TLS")
                return False
                
            except smtplib.SMTPException as e:
                self.logger.error(f"SMTP Error: {str(e)}")
                print(f"An error occurred while sending the email: {str(e)}")
                return False
                
            except Exception as e:
                self.logger.error(f"Unexpected error sending email: {str(e)}")
                print(f"An unexpected error occurred: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error preparing email: {str(e)}")
            print(f"Error preparing email: {str(e)}")
            return False
    
    def send_bulk_emails(self, customers: pd.DataFrame, subject_template: str, 
                         body_html_template: str, body_text_template: Optional[str] = None,
                         test_mode: bool = False, max_emails: Optional[int] = None,
                         campaign_id: Optional[str] = None) -> Dict[str, int]:
        """
        Send bulk emails to customers.
        
        Args:
            customers: DataFrame with customer data (must include 'email' and 'customer_id' columns)
            subject_template: Template for email subject (can include {placeholders})
            body_html_template: Template for HTML email body (can include {placeholders})
            body_text_template: Template for plain text email body (optional)
            test_mode: If True, emails will not be sent but logged
            max_emails: Maximum number of emails to send (optional)
            campaign_id: Campaign ID for tracking (optional)
            
        Returns:
            Dictionary with counts of successful and failed emails
        """
        if 'email' not in customers.columns:
            raise ValueError("Customer DataFrame must include 'email' column")
        
        # Check if customer_id is present for tracking
        has_customer_id = 'customer_id' in customers.columns
        if self.enable_tracking and campaign_id and not has_customer_id:
            print("Warning: Customer DataFrame is missing 'customer_id' column. Email tracking will be limited.")
        
        # Initialize counters
        results = {'success': 0, 'failed': 0, 'skipped': 0}
        
        # Limit number of emails if specified
        if max_emails is not None:
            customers = customers.head(max_emails)
        
        # Send emails to each customer
        for _, customer in customers.iterrows():
            # Skip if email is missing
            if pd.isna(customer['email']):
                results['skipped'] += 1
                continue
            
            # Format templates with customer data
            try:
                subject = subject_template.format(**customer.to_dict())
                body_html = body_html_template.format(**customer.to_dict())
                
                if body_text_template:
                    body_text = body_text_template.format(**customer.to_dict())
                else:
                    body_text = None
                
                # Send email (or log in test mode)
                if test_mode:
                    print(f"TEST MODE: Would send email to {customer['email']}")
                    print(f"Subject: {subject}")
                    print(f"Body: {body_html[:100]}...")
                    results['success'] += 1
                else:
                    # Get customer_id if available, otherwise use None
                    customer_id = customer.get('customer_id') if has_customer_id else None
                    success = self.send_email(
                        customer['email'], 
                        subject, 
                        body_html, 
                        body_text,
                        campaign_id=campaign_id,
                        customer_id=customer_id
                    )
                    if success:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
            
            except Exception as e:
                print(f"Error preparing email for {customer['email']}: {str(e)}")
                results['failed'] += 1
        
        return results
    
    def send_segment_emails(self, customers: pd.DataFrame, segment_templates: Dict[str, Dict[str, str]],
                           segment_column: str = 'segment_name', test_mode: bool = False,
                           max_emails_per_segment: Optional[int] = None,
                           campaign_id: Optional[str] = None) -> Dict[str, Dict[str, int]]:
        """
        Send segment-specific emails to customers.
        
        Args:
            customers: DataFrame with customer data (must include 'email', 'customer_id' and segment_column)
            segment_templates: Dictionary mapping segment names to templates
                               (each with 'subject', 'body_html', and optionally 'body_text')
            segment_column: Column name containing segment names
            test_mode: If True, emails will not be sent but logged
            max_emails_per_segment: Maximum number of emails to send per segment (optional)
            campaign_id: Campaign ID for tracking (optional)
            
        Returns:
            Dictionary with results for each segment
        """
        if 'email' not in customers.columns:
            raise ValueError("Customer DataFrame must include 'email' column")
        
        # Check if customer_id is present for tracking
        if self.enable_tracking and campaign_id and 'customer_id' not in customers.columns:
            print("Warning: Customer DataFrame is missing 'customer_id' column. Email tracking will be limited.")
        
        if segment_column not in customers.columns:
            raise ValueError(f"Customer DataFrame must include '{segment_column}' column")
        
        # Initialize results dictionary
        results = {segment: {'success': 0, 'failed': 0, 'skipped': 0} 
                  for segment in segment_templates.keys()}
        results['other'] = {'success': 0, 'failed': 0, 'skipped': 0}
        
        # Group customers by segment
        for segment, segment_df in customers.groupby(segment_column):
            # Skip if no template for this segment
            if segment not in segment_templates:
                print(f"No template found for segment: {segment}")
                results['other']['skipped'] += len(segment_df)
                continue
            
            # Get templates for this segment
            templates = segment_templates[segment]
            
            # Limit number of emails if specified
            if max_emails_per_segment is not None:
                segment_df = segment_df.head(max_emails_per_segment)
            
            # Send emails to customers in this segment
            segment_results = self.send_bulk_emails(
                segment_df,
                templates['subject'],
                templates['body_html'],
                templates.get('body_text'),
                test_mode,
                campaign_id=campaign_id
            )
            
            # Update results
            results[segment]['success'] += segment_results['success']
            results[segment]['failed'] += segment_results['failed']
            results[segment]['skipped'] += segment_results['skipped']
        
        return results


class EmailTemplateManager:
    """
    Class for managing email templates for different customer segments.
    """
    
    @staticmethod
    def get_segment_templates() -> Dict[str, Dict[str, str]]:
        """
        Get email templates for different customer segments.
        
        Returns:
            Dictionary mapping segment names to templates
        """
        templates = {}
        
        # VIP customers
        templates['VIP'] = {
            'subject': 'Exclusive VIP Offers Just for You, {first_name}!',
            'body_html': """
            <html>
            <body>
                <h1>Hello {first_name},</h1>
                <p>As one of our most valued customers, we're excited to share these exclusive VIP offers with you:</p>
                <ul>
                    <li>Early access to our new {primary_category} collection</li>
                    <li>Special 20% discount on your next purchase</li>
                    <li>Complimentary gift with purchases over $100</li>
                </ul>
                <p>Thank you for your continued loyalty. We truly appreciate your business!</p>
                <p>Best regards,<br>The Mall Team</p>
            </body>
            </html>
            """
        }
        
        # At Risk customers
        templates['At Risk'] = {
            'subject': 'We Miss You, {first_name}! Special Offer Inside',
            'body_html': """
            <html>
            <body>
                <h1>Hello {first_name},</h1>
                <p>We've noticed it's been a while since your last visit, and we miss you!</p>
                <p>To welcome you back, we're offering a special 15% discount on your favorite {primary_category} products.</p>
                <p>Your last purchase with us was on {last_purchase_date:%B %d, %Y}. We'd love to see you again soon!</p>
                <p>Best regards,<br>The Mall Team</p>
            </body>
            </html>
            """
        }
        
        # New customers
        templates['New'] = {
            'subject': 'Welcome to Our Community, {first_name}!',
            'body_html': """
            <html>
            <body>
                <h1>Welcome, {first_name}!</h1>
                <p>Thank you for your recent purchase with us. We're thrilled to have you as a customer!</p>
                <p>Here are some benefits you might enjoy:</p>
                <ul>
                    <li>10% off your next purchase with code WELCOME10</li>
                    <li>Free shipping on orders over $50</li>
                    <li>Exclusive access to new arrivals</li>
                </ul>
                <p>We hope to see you again soon!</p>
                <p>Best regards,<br>The Mall Team</p>
            </body>
            </html>
            """
        }
        
        # Regular customers
        templates['Regular'] = {
            'subject': 'Thank You for Being a Loyal Customer, {first_name}!',
            'body_html': """
            <html>
            <body>
                <h1>Hello {first_name},</h1>
                <p>Thank you for being a loyal customer! We appreciate your continued support.</p>
                <p>Based on your interest in {primary_category}, we thought you might like our new arrivals:</p>
                <ul>
                    <li>New seasonal {primary_category} collection</li>
                    <li>Complementary products that pair well with your previous purchases</li>
                    <li>Special offers on related items</li>
                </ul>
                <p>We look forward to seeing you again soon!</p>
                <p>Best regards,<br>The Mall Team</p>
            </body>
            </html>
            """
        }
        
        # Occasional customers
        templates['Occasional'] = {
            'subject': 'Special Offers on {primary_category} Products, {first_name}!',
            'body_html': """
            <html>
            <body>
                <h1>Hello {first_name},</h1>
                <p>We have some exciting offers that we think you'll love!</p>
                <p>Since you've shown interest in {primary_category}, we wanted to let you know about our current promotions:</p>
                <ul>
                    <li>Seasonal discounts on {primary_category} products</li>
                    <li>Buy one, get one 50% off on selected items</li>
                    <li>Limited-time offers on new arrivals</li>
                </ul>
                <p>We hope to see you soon!</p>
                <p>Best regards,<br>The Mall Team</p>
            </body>
            </html>
            """
        }
        
        return templates
    
    @staticmethod
    def get_category_templates() -> Dict[str, Dict[str, str]]:
        """
        Get email templates for different product categories.
        
        Returns:
            Dictionary mapping category names to templates
        """
        templates = {}
        
        # Electronics
        templates['electronics'] = {
            'subject': 'New Electronics Arrivals and Special Offers, {first_name}!',
            'body_html': """
            <html>
            <body>
                <h1>Hello {first_name},</h1>
                <p>As someone who has purchased electronics from us before, we thought you'd be interested in our latest arrivals:</p>
                <ul>
                    <li>New smartphone models with exclusive launch discounts</li>
                    <li>Smart home devices to make your life easier</li>
                    <li>Accessories for your existing electronics</li>
                </ul>
                <p>Visit us soon to check out these exciting new products!</p>
                <p>Best regards,<br>The Mall Team</p>
            </body>
            </html>
            """
        }
        
        # Clothing
        templates['clothing'] = {
            'subject': 'New Fashion Arrivals Just for You, {first_name}!',
            'body_html': """
            <html>
            <body>
                <h1>Hello {first_name},</h1>
                <p>Our new seasonal collection has arrived, and we thought you'd want to be among the first to know!</p>
                <ul>
                    <li>Trendy new styles for the season</li>
                    <li>Limited edition designer collaborations</li>
                    <li>Special discounts on selected fashion items</li>
                </ul>
                <p>Come visit us to refresh your wardrobe with the latest trends!</p>
                <p>Best regards,<br>The Mall Team</p>
            </body>
            </html>
            """
        }
        
        # Home & Kitchen
        templates['home_kitchen'] = {
            'subject': 'Enhance Your Home with Our Latest Offers, {first_name}!',
            'body_html': """
            <html>
            <body>
                <h1>Hello {first_name},</h1>
                <p>Make your home even more comfortable with our latest home and kitchen products:</p>
                <ul>
                    <li>New kitchen appliances to make cooking a breeze</li>
                    <li>Home decor items to refresh your living space</li>
                    <li>Special bundle offers on kitchen essentials</li>
                </ul>
                <p>Visit us soon to discover how to enhance your home!</p>
                <p>Best regards,<br>The Mall Team</p>
            </body>
            </html>
            """
        }
        
        # Groceries
        templates['groceries'] = {
            'subject': 'Fresh Deals on Groceries This Week, {first_name}!',
            'body_html': """
            <html>
            <body>
                <h1>Hello {first_name},</h1>
                <p>Check out our special offers on groceries this week:</p>
                <ul>
                    <li>Fresh produce at discounted prices</li>
                    <li>Buy one, get one free on selected items</li>
                    <li>Special discounts on premium grocery brands</li>
                </ul>
                <p>Visit us soon to stock up on your favorite groceries!</p>
                <p>Best regards,<br>The Mall Team</p>
            </body>
            </html>
            """
        }
        
        return templates
    
    @staticmethod
    def prepare_customer_data_for_email(df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare customer data for email templates.
        
        Args:
            df: DataFrame with customer data
            
        Returns:
            DataFrame with additional fields for email templates
        """
        # Create a copy to avoid modifying the original dataframe
        email_df = df.copy()
        
        # Extract first name from email if not available
        if 'first_name' not in email_df.columns:
            email_df['first_name'] = email_df['email'].apply(
                lambda x: x.split('@')[0].split('.')[0].title() if isinstance(x, str) else 'Valued Customer'
            )
        
        # Format dates for email templates
        if 'last_purchase_date' in email_df.columns:
            # Handle zero values
            email_df['last_purchase_date'] = email_df['last_purchase_date'].replace(0, np.nan)
            email_df['last_purchase_date'] = email_df['last_purchase_date'].replace('0', np.nan)
            
            # Try to parse with error handling
            try:
                email_df['last_purchase_date'] = pd.to_datetime(email_df['last_purchase_date'], errors='coerce')
            except:
                # If standard parsing fails, try with mixed format
                email_df['last_purchase_date'] = pd.to_datetime(email_df['last_purchase_date'], format='mixed', errors='coerce')
            
            # Handle NaT values with today's date
            email_df = email_df.assign(last_purchase_date=email_df['last_purchase_date'].fillna(pd.Timestamp('today')))
            
            # Format dates as strings for template use
            email_df['formatted_last_purchase'] = email_df['last_purchase_date'].dt.strftime('%d %b, %Y')
        
        # Ensure primary category is available
        if 'primary_category' not in email_df.columns and 'category' in email_df.columns:
            email_df['primary_category'] = email_df['category']
        
        # Ensure customer_id is available
        if 'customer_id' not in email_df.columns and 'id' in email_df.columns:
            email_df['customer_id'] = email_df['id']
        
        return email_df 