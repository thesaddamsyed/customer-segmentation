"""
Email sender module for sending automated emails to customers.
"""
import os
import smtplib
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Optional
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from dotenv import load_dotenv


class EmailSender:
    """
    Class for sending automated emails to customers.
    """
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, 
                 username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the EmailSender class.
        
        Args:
            host: SMTP server host
            port: SMTP server port
            username: SMTP server username
            password: SMTP server password
        """
        # Load environment variables if not provided
        load_dotenv()
        
        self.host = host or os.getenv('EMAIL_HOST')
        self.port = port or int(os.getenv('EMAIL_PORT', '587'))
        self.username = username or os.getenv('EMAIL_USER')
        self.password = password or os.getenv('EMAIL_PASSWORD')
        
        # Validate configuration
        if not all([self.host, self.port, self.username, self.password]):
            raise ValueError(
                "Email configuration is incomplete. Please provide host, port, username, and password "
                "either as parameters or in a .env file."
            )
    
    def send_email(self, to_email: str, subject: str, body_html: str, body_text: Optional[str] = None) -> bool:
        """
        Send an email to a customer.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML content of the email
            body_text: Plain text content of the email (optional)
            
        Returns:
            True if the email was sent successfully, False otherwise
        """
        # Validate email address
        try:
            validate_email(to_email)
        except EmailNotValidError:
            print(f"Invalid email address: {to_email}")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.username
        msg['To'] = to_email
        
        # Add plain text version if provided, otherwise create from HTML
        if body_text is None:
            # Simple conversion from HTML to text (not perfect but works for basic HTML)
            body_text = body_html.replace('<br>', '\n').replace('<p>', '\n').replace('</p>', '\n')
            body_text = body_text.replace('<h1>', '\n').replace('</h1>', '\n')
            body_text = body_text.replace('<h2>', '\n').replace('</h2>', '\n')
            body_text = body_text.replace('<li>', '\n- ').replace('</li>', '')
            body_text = body_text.replace('<ul>', '\n').replace('</ul>', '\n')
            body_text = body_text.replace('<ol>', '\n').replace('</ol>', '\n')
            body_text = body_text.replace('<strong>', '').replace('</strong>', '')
            body_text = body_text.replace('<em>', '').replace('</em>', '')
            body_text = body_text.replace('<a href="', '').replace('">', ' (').replace('</a>', ')')
            
            # Remove any remaining HTML tags
            import re
            body_text = re.sub('<[^<]+?>', '', body_text)
        
        # Attach parts
        part1 = MIMEText(body_text, 'plain')
        part2 = MIMEText(body_html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        try:
            # Connect to server
            server = smtplib.SMTP(self.host, self.port)
            server.ehlo()
            server.starttls()
            server.login(self.username, self.password)
            
            # Send email
            server.sendmail(self.username, to_email, msg.as_string())
            server.quit()
            
            print(f"Email sent to {to_email}")
            return True
        
        except Exception as e:
            print(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_bulk_emails(self, customers: pd.DataFrame, subject_template: str, 
                         body_html_template: str, body_text_template: Optional[str] = None,
                         test_mode: bool = False, max_emails: Optional[int] = None) -> Dict[str, int]:
        """
        Send bulk emails to customers.
        
        Args:
            customers: DataFrame with customer data (must include 'email' column)
            subject_template: Template for email subject (can include {placeholders})
            body_html_template: Template for HTML email body (can include {placeholders})
            body_text_template: Template for plain text email body (optional)
            test_mode: If True, emails will not be sent but logged
            max_emails: Maximum number of emails to send (optional)
            
        Returns:
            Dictionary with counts of successful and failed emails
        """
        if 'email' not in customers.columns:
            raise ValueError("Customer DataFrame must include 'email' column")
        
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
                    success = self.send_email(customer['email'], subject, body_html, body_text)
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
                           max_emails_per_segment: Optional[int] = None) -> Dict[str, Dict[str, int]]:
        """
        Send segment-specific emails to customers.
        
        Args:
            customers: DataFrame with customer data (must include 'email' and segment_column)
            segment_templates: Dictionary mapping segment names to templates
                               (each with 'subject', 'body_html', and optionally 'body_text')
            segment_column: Column name containing segment names
            test_mode: If True, emails will not be sent but logged
            max_emails_per_segment: Maximum number of emails to send per segment (optional)
            
        Returns:
            Dictionary with results for each segment
        """
        if 'email' not in customers.columns:
            raise ValueError("Customer DataFrame must include 'email' column")
        
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
                test_mode
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
            email_df['last_purchase_date'] = pd.to_datetime(email_df['last_purchase_date'])
        
        # Ensure primary category is available
        if 'primary_category' not in email_df.columns and 'category' in email_df.columns:
            email_df['primary_category'] = email_df['category']
        
        return email_df 