# Mall Customer Segmentation System

A comprehensive customer segmentation and marketing automation system for mall retailers.

## Features

- **Customer Segmentation**: Automatically categorize customers into segments (VIP, Regular, At-Risk, New, etc.) based on purchase patterns
- **Interactive Dashboard**: Visualize key business metrics and customer insights
- **Automated Email Marketing**: Send targeted emails to customers based on their segment and purchase history
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

## Installation

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your email configuration (for the automated email feature)
4. Run the application:
   ```
   streamlit run app.py
   ```

## Email Configuration

To use the automated email feature, create a `.env` file with the following variables:
```
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USER=your_email@example.com
EMAIL_PASSWORD=your_password
```

## Usage

1. Upload your customer data or use the provided sample data
2. Navigate through the different pages to explore insights and manage customer segments
3. Set up automated email campaigns based on customer segments
4. Monitor customer behavior and segment changes over time

## License

MIT 