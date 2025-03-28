# Mall Customer Segmentation System

A comprehensive customer segmentation and marketing automation system for mall retailers.

## Features

- **Customer Segmentation**: Automatically categorize customers into segments (VIP, Regular, At-Risk, New, etc.) based on purchase patterns
- **Interactive Dashboard**: Visualize key business metrics and customer insights
- **Automated Email Marketing**: Send targeted emails to customers based on their segment and purchase history
- **Email Campaign Tracking**: Track email opens and clicks to measure campaign effectiveness
- **Product Recommendations**: Suggest products to customers based on their previous purchases
- **Offer Management**: Create and manage special offers for different customer segments

## Project Structure

- `app.py`: Main Streamlit application entry point
- `pages/`: Contains all the pages for the multi-page Streamlit app
- `src/`: Source code for data processing, segmentation, and email functionality
- `models/`: Trained machine learning models for customer segmentation
- `utils/`: Utility functions used across the application
- `data/`: Data files (processed versions of the original dataset)
- `config/`: Configuration files for the application
- `test_data/`: Test customer data for email functionality testing

## Installation

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   streamlit run app.py
   ```

## Email Functionality

### Setting Up Email Provider

The system includes a built-in email configuration system that supports:
- Gmail (recommended to use with SSL on port 465)
- Outlook
- Yahoo Mail
- Custom SMTP providers

To set up email for the first time:

1. Navigate to the "Test Email" page
2. Select your email provider
3. Enter your credentials:
   - For Gmail: Use your Gmail address and an App Password (requires 2-Step Verification)
   - For other providers: Use your email address and password
4. Save the configuration, which will be stored in a `.env` file

### Email Features

- **Test Email Page**: Send test emails to verify your configuration and template designs
- **Email Marketing Page**: Create and send targeted campaigns to specific customer segments
- **Email Template Management**: Create and customize email templates for different campaigns
- **Email Tracking**: Track email opens and clicks to measure campaign effectiveness
- **Campaign Analytics**: View campaign results and engagement metrics

### Gmail Setup (Recommended)

If using Gmail:
1. Enable 2-Step Verification in your Google Account security settings
2. Generate an App Password for the application
3. Use SSL (port 465) for the most reliable connection
4. Enter the App Password without spaces

## Usage

1. Upload your customer data or use the provided sample data
2. Navigate through the different pages to explore insights and manage customer segments
3. Set up email configuration in the "Test Email" page
4. Test email functionality with a single customer
5. Create targeted email campaigns based on customer segments
6. Monitor campaign results and customer engagement

## License

MIT 