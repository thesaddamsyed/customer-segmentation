"""
Customer Profiles Page

This page allows users to view and analyze individual customer profiles,
including purchase history, segment information, and personalized recommendations.
"""
import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Import custom modules
from src.data_processing.data_loader import load_and_process
from src.segmentation.segmentation import CustomerSegmentation
from src.visualization.dashboard import (
    create_customer_location_map
)

# Set page configuration
st.set_page_config(
    page_title="Customer Profiles - Mall Customer Segmentation",
    page_icon="👤",
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
        /* Main Theme Colors */
        :root {
            --dark-bg: #121212;
            --dark-surface: #1e1e1e;
            --dark-card: #252525;
            --dark-card-hover: #2d2d2d;
            --accent-primary: #9c64ff;
            --accent-secondary: #7d56c2;
            --accent-tertiary: #6247aa;
            --text-primary: #ffffff;
            --text-secondary: #b0b0b0;
            --text-tertiary: #777777;
            --border-light: #333333;
        }
        
        /* Main Headers */
        .main-header {
            font-size: 2.5rem;
            color: var(--accent-primary);
            text-align: center;
            margin-bottom: 1.5rem;
            font-weight: 600;
        }
        .sub-header {
            font-size: 1.5rem;
            color: var(--accent-primary);
            margin-bottom: 1.5rem;
            font-weight: 500;
        }
        h3 {
            color: var(--accent-primary);
            font-size: 1.3rem;
            margin-top: 1rem;
            margin-bottom: 1.2rem;
            font-weight: 600;
            border-bottom: 2px solid var(--border-light);
            padding-bottom: 0.5rem;
            display: inline-block;
        }

        /* Overall Background */
        .block-container, .css-1offfwp, [data-testid="stAppViewContainer"] {
            background-color: var(--dark-bg);
        }
        
        /* Streamlit default text */
        .css-nahz7x, p, li, div {
            color: var(--text-primary) !important;
        }
        
        /* Customer Profile Card */
        .profile-card {
            background-color: var(--dark-card);
            border-radius: 12px;
            padding: 1.8rem;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
            margin-bottom: 2rem;
            height: 100%;
            border-top: 5px solid var(--accent-primary);
            transition: transform 0.2s;
        }
        .profile-card:hover {
            transform: translateY(-5px);
            background-color: var(--dark-card-hover);
        }
        
        /* Profile Header Section */
        .profile-header {
            display: flex;
            align-items: center;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-light);
            padding-bottom: 1rem;
        }
        .profile-avatar {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--accent-tertiary), var(--accent-primary));
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            font-weight: bold;
            font-size: 1.8rem;
            margin-right: 1.2rem;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.25);
        }
        .profile-name {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text-primary);
            overflow-wrap: break-word;
            word-wrap: break-word;
            margin-bottom: 0.2rem;
        }
        .profile-segment {
            display: inline-block;
            padding: 0.25rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: bold;
            color: white;
            background: linear-gradient(135deg, var(--accent-tertiary), var(--accent-primary));
            margin-left: 0.5rem;
            vertical-align: middle;
        }
        
        /* Profile Info Fields */
        .profile-info {
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
            margin-bottom: 1.5rem;
        }
        .profile-info-item {
            display: flex;
            flex-direction: column;
        }
        .profile-info-label {
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 0.2rem;
        }
        .profile-info-value {
            font-size: 1.1rem;
            color: var(--text-primary);
            font-weight: 500;
            overflow-wrap: break-word;
            word-wrap: break-word;
        }
        
        /* Metric Cards */
        .metric-card {
            background-color: var(--dark-surface);
            border-radius: 10px;
            padding: 1.2rem 1rem;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
            text-align: center;
            margin-bottom: 1.2rem;
            min-height: 110px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            overflow: hidden;
            transition: all 0.3s;
            border-left: 4px solid var(--accent-primary);
        }
        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: bold;
            color: var(--accent-primary);
            margin-bottom: 0.5rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .metric-label {
            font-size: 0.9rem;
            color: var(--text-secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        /* Stats Container */
        .stats-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.8rem;
            margin: 1.2rem 0;
        }
        .stat-box {
            background-color: var(--dark-card);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
            box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15);
            transition: all 0.2s;
        }
        .stat-box:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        .stat-value {
            font-size: 1.3rem;
            font-weight: bold;
            color: var(--accent-primary);
            margin-bottom: 0.3rem;
        }
        .stat-label {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }
        
        /* Transaction Items */
        .trans-item {
            display: flex;
            justify-content: space-between;
            padding: 0.8rem;
            border-bottom: 1px solid var(--border-light);
            transition: background-color 0.2s;
        }
        .trans-item:hover {
            background-color: var(--dark-surface);
        }
        .trans-date {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        .trans-amount {
            font-weight: 600;
            color: var(--text-primary);
        }
        
        /* Recommendation Cards */
        .recommendation-card {
            background-color: var(--dark-card);
            border-radius: 10px;
            padding: 1.2rem;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
            margin-bottom: 1.2rem;
            height: 100%;
            transition: all 0.2s;
            border-left: 4px solid var(--accent-secondary);
            border-top: 1px solid var(--border-light);
            border-right: 1px solid var(--border-light);
            border-bottom: 1px solid var(--border-light);
        }
        .recommendation-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 14px rgba(0, 0, 0, 0.25);
        }
        .recommendation-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--accent-primary);
            margin-bottom: 0.7rem;
            overflow-wrap: break-word;
        }
        .recommendation-text {
            font-size: 0.95rem;
            color: var(--text-secondary);
            line-height: 1.5;
        }
        
        /* Tab Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: var(--dark-bg);
            padding: 5px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: var(--dark-surface);
            border-radius: 8px 8px 0 0;
            padding: 8px 16px;
            margin-right: 4px;
            color: var(--text-primary) !important;
            font-weight: 500;
            border: 1px solid var(--border-light);
        }
        .stTabs [aria-selected="true"] {
            background-color: var(--accent-primary) !important;
            color: white !important;
            border: 1px solid var(--accent-primary);
            font-weight: 600;
        }
        .stTabs [data-baseweb="tab-panel"] {
            background-color: var(--dark-surface);
            border-radius: 0 0 8px 8px;
            border: 1px solid var(--border-light);
            border-top: none;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }
        /* Ensure tab text is clearly visible */
        .stTabs [data-baseweb="tab-list"] button {
            color: var(--text-primary) !important;
        }
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            color: white !important;
        }
        
        /* Ensure all text in tab panels is visible */
        .stTabs [data-baseweb="tab-panel"] h3 {
            color: var(--accent-primary);
            background-color: transparent;
            padding: 5px 10px;
            border-radius: 4px;
            margin-top: 1rem;
            margin-bottom: 1.5rem;
            display: inline-block;
            font-weight: 600;
            border-bottom: 2px solid var(--accent-primary);
        }
        
        /* Additional headings within tabs */
        .stTabs [data-baseweb="tab-panel"] h4 {
            color: var(--accent-primary);
            font-size: 1.1rem;
            margin-top: 1rem;
            margin-bottom: 0.8rem;
            font-weight: 500;
        }
        
        /* Chart title styling */
        .stTabs [data-baseweb="tab-panel"] .js-plotly-plot .plotly .main-svg .infolayer .g-gtitle .annotation .text {
            fill: var(--text-primary) !important;
        }
        
        /* Info block styling for better contrast */
        .stTabs [data-baseweb="tab-panel"] .stAlert {
            background-color: var(--dark-card) !important;
            border: 1px solid var(--border-light);
        }
        
        /* Text in tab panels */
        .stTabs [data-baseweb="tab-panel"] p {
            color: var(--text-primary);
        }
        
        /* Chart Containers */
        .chart-container {
            background-color: var(--dark-card);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            margin-bottom: 2rem;
        }
        
        /* Utility Classes */
        .text-center {
            text-align: center;
        }
        .text-primary {
            color: var(--accent-primary);
        }
        .rounded {
            border-radius: 8px;
        }
        .shadow {
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        
        /* Streamlit Overrides */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 100%;
        }
        
        /* DataFrame styling */
        .stDataFrame {
            overflow-x: auto;
            color: var(--text-primary);
        }
        .stDataFrame table {
            width: 100%;
            color: var(--text-primary);
            background-color: var(--dark-card);
        }
        .stDataFrame th {
            background-color: var(--dark-surface);
            color: var(--text-primary);
            border-bottom: 1px solid var(--border-light);
        }
        .stDataFrame td {
            white-space: nowrap;
            color: var(--text-primary);
            border-bottom: 1px solid var(--border-light);
        }
        /* Row hover */
        .stDataFrame tr:hover td {
            background-color: var(--dark-card-hover);
        }
        
        .text-container {
            overflow-wrap: break-word;
            word-wrap: break-word;
        }
        .js-plotly-plot {
            overflow: hidden;
        }
        
        /* Info and Alert Styling */
        .stAlert {
            border-radius: 8px;
            padding: 1rem;
            background-color: var(--dark-card) !important;
            color: var(--text-primary) !important;
        }
        .stAlert>div {
            padding: 0.5rem 1rem;
            border-radius: 8px;
            color: var(--text-primary);
        }
        
        /* Sidebar Improvements */
        [data-testid="stSidebar"] {
            background-color: var(--dark-bg);
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 1.2rem;
            background-color: var(--dark-bg);
        }
        [data-testid="stSidebar"] .stButton>button {
            width: 100%;
            background-color: var(--accent-primary);
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            border: none;
            transition: all 0.2s;
        }
        [data-testid="stSidebar"] .stButton>button:hover {
            background-color: var(--accent-secondary);
            transform: translateY(-2px);
        }
        
        /* Form inputs styling */
        [data-testid="stTextInput"] > div > div > input {
            background-color: var(--dark-surface);
            color: var(--text-primary);
            border: 1px solid var(--border-light);
        }
        
        /* Select boxes */
        [data-testid="stSelectbox"] {
            color: var(--text-primary);
        }
        [data-testid="stSelectbox"] > div > div > div {
            background-color: var(--dark-surface);
            color: var(--text-primary);
            border: 1px solid var(--border-light);
        }
        
        /* Radio buttons */
        [data-testid="stRadio"] > div {
            background-color: var(--dark-surface);
            color: var(--text-primary);
            border-radius: 8px;
            padding: 10px;
        }
        [data-testid="stRadio"] label {
            color: var(--text-primary) !important;
        }
        
        /* Charts - ensure dark theme compatibility */
        .plot-container .plot-surface {
            fill: var(--dark-card) !important;
        }
        .plot-container .xaxislayer-above path, .plot-container .yaxislayer-above path {
            stroke: var(--text-secondary) !important;
        }
        .plot-container .xaxislayer-above text, .plot-container .yaxislayer-above text {
            fill: var(--text-secondary) !important;
        }
        .plot-container .overplot .trace .points path {
            stroke: var(--accent-primary) !important;
        }
        
        /* Tab Section Headers */
        .tab-section-header {
            background-color: var(--dark-card);
            padding: 10px 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid var(--accent-primary);
            box-shadow: 0 2px 5px rgba(0,0,0,0.15);
        }
        .tab-section-header h3 {
            color: var(--accent-primary);
            margin: 0;
            padding: 0;
            font-size: 1.3rem;
            font-weight: 600;
            border-bottom: none;
            display: block;
        }
        
        /* Responsive Adjustments */
        @media (max-width: 992px) {
            .profile-avatar {
                width: 60px;
                height: 60px;
                font-size: 1.5rem;
            }
            .profile-name {
                font-size: 1.3rem;
            }
            .metric-value {
                font-size: 1.5rem;
            }
        }
        @media (max-width: 768px) {
            .stats-container {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        @media (max-width: 576px) {
            .profile-header {
                flex-direction: column;
                align-items: center;
                text-align: center;
            }
            .profile-avatar {
                margin-right: 0;
                margin-bottom: 1rem;
            }
            .stats-container {
                grid-template-columns: 1fr;
            }
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

# Function to generate customer avatar
def generate_avatar(customer_id, first_name):
    if first_name:
        initials = first_name[0].upper()
    else:
        initials = customer_id[:1].upper()
    
    return f"""
    <div class="profile-avatar">
        {initials}
    </div>
    """

# Function to generate product recommendations
def generate_product_recommendations(customer_data, transactions_df):
    recommendations = []
    
    # Get customer's primary category
    primary_category = customer_data.get('primary_category', '')
    
    if primary_category:
        # Find popular products in the customer's primary category
        category_products = transactions_df[transactions_df['category'] == primary_category]
        popular_products = category_products['product_name'].value_counts().head(3).index.tolist()
        
        for product in popular_products:
            recommendations.append({
                'title': product,
                'reason': f"Popular {primary_category} product that matches your interests"
            })
    
    # Add some general recommendations if we don't have enough
    if len(recommendations) < 3:
        general_products = transactions_df['product_name'].value_counts().head(5).index.tolist()
        for product in general_products:
            if len(recommendations) < 3 and product not in [r['title'] for r in recommendations]:
                recommendations.append({
                    'title': product,
                    'reason': "Popular product that many customers enjoy"
                })
    
    return recommendations

# Function to generate special offers
def generate_special_offers(customer_data):
    offers = []
    segment = customer_data.get('segment_name', '')
    
    if segment == 'VIP':
        offers.append({
            'title': "20% Off Next Purchase",
            'text': "As a VIP customer, enjoy 20% off your next purchase of any amount."
        })
        offers.append({
            'title': "Early Access to New Products",
            'text': "Get exclusive early access to our new product launches."
        })
    
    elif segment == 'At Risk':
        offers.append({
            'title': "We Miss You! 15% Off",
            'text': "We haven't seen you in a while. Come back and enjoy 15% off your next purchase."
        })
        offers.append({
            'title': "Free Shipping",
            'text': "Enjoy free shipping on your next order, no minimum purchase required."
        })
    
    elif segment == 'New':
        offers.append({
            'title': "Welcome Offer: 10% Off",
            'text': "As a new customer, enjoy 10% off your next purchase."
        })
        offers.append({
            'title': "Free Gift with Purchase",
            'text': "Receive a free gift with your next purchase of $50 or more."
        })
    
    else:
        offers.append({
            'title': "10% Off $100+ Purchase",
            'text': "Enjoy 10% off your next purchase of $100 or more."
        })
        offers.append({
            'title': "Buy One, Get One 50% Off",
            'text': "Buy any item and get a second item of equal or lesser value for 50% off."
        })
    
    return offers

# Main function
def main():
    # Load CSS
    load_css()
    
    # Display header
    st.markdown('<h1 class="main-header">Customer Profiles</h1>', unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading data..."):
        transactions_df, customer_features = load_cached_data()
        
        # Create a proper city column from one-hot encoded city columns
        city_columns = [col for col in customer_features.columns if col.startswith('city_')]
        
        if city_columns and 'city' not in customer_features.columns:
            
            
            # Create a new city column
            customer_features['city'] = 'Unknown'
            
            # For each city column, set the city name for rows where the column value is 1
            for city_col in city_columns:
                city_name = city_col.replace('city_', '')
                customer_features.loc[customer_features[city_col] == 1, 'city'] = city_name
            
            
        
        # Load model
        with st.spinner("Loading segmentation model..."):
            model = load_model()
            
            if model is None:
                st.stop()
    
    # Get customer segments
    customer_segments = model.get_customer_segments(customer_features)
    
    # Combine customer features and segments
    customer_data = customer_segments.copy()
    
    # Ensure city column is in customer_data
    if 'city' in customer_features.columns and 'city' not in customer_data.columns:
        customer_data['city'] = customer_features['city']
    
    # Create sidebar for customer selection
    st.sidebar.markdown("## Customer Selection")
    
    # Add a reset button
    if st.sidebar.button("Reset Filters"):
        # This will trigger a rerun with default values
        st.experimental_rerun()
    
    # Filter options
    filter_option = st.sidebar.radio(
        "Filter By",
        ["Customer ID", "Segment", "City", "All Customers"]
    )
    
    # Display total customer count
    st.sidebar.write(f"Total Customers: {len(customer_data)}")
    
    if filter_option == "Customer ID":
        # Get list of customer IDs
        customer_ids = customer_data.index.tolist()
        
        # Customer ID search
        search_id = st.sidebar.text_input("Search Customer ID")
        
        if search_id:
            # Filter customer IDs by search term
            filtered_ids = [cid for cid in customer_ids if search_id.upper() in cid.upper()]
            
            if filtered_ids:
                st.sidebar.write(f"Found {len(filtered_ids)} matching customers")
                selected_customer_id = st.sidebar.selectbox("Select Customer", filtered_ids)
            else:
                st.sidebar.warning("No customers found matching the search term.")
                selected_customer_id = None
        else:
            # If no search term, show all customers
            selected_customer_id = st.sidebar.selectbox("Select Customer", customer_ids[:100])  # Limit to first 100 for performance
    
    elif filter_option == "Segment":
        # Get list of segments
        segments = sorted(customer_data['segment_name'].unique().tolist())
        
        # Display segment counts
        segment_counts = customer_data['segment_name'].value_counts().to_dict()
        segment_info = [f"{segment} ({segment_counts.get(segment, 0)} customers)" for segment in segments]
        
        # Segment selection
        selected_segment_info = st.sidebar.selectbox("Select Segment", segment_info)
        selected_segment = selected_segment_info.split(" (")[0]  # Extract segment name
        
        # Filter customers by segment
        segment_customers = customer_data[customer_data['segment_name'] == selected_segment]
        
        st.sidebar.write(f"Showing {len(segment_customers)} customers in segment '{selected_segment}'")
        
        # Customer selection from filtered list
        selected_customer_id = st.sidebar.selectbox(
            f"Select {selected_segment} Customer",
            segment_customers.index.tolist()[:100]  # Limit to first 100 for performance
        )
    
    elif filter_option == "City":
        # Get list of cities
        if 'city' in customer_data.columns:
            # More robust approach to get valid cities
            try:
                # First, ensure we have the city column
                st.sidebar.write(f"City column found: {customer_data['city'].name}")
                
                # Convert to string and handle NaN values
                customer_data['city_clean'] = customer_data['city'].fillna('Unknown')
                customer_data['city_clean'] = customer_data['city_clean'].astype(str)
                customer_data['city_clean'] = customer_data['city_clean'].str.strip()
                
                # Filter out empty values
                valid_cities_mask = (customer_data['city_clean'] != '') & (customer_data['city_clean'] != 'Unknown')
                valid_cities_df = customer_data[valid_cities_mask]
                
                # Get unique cities
                cities = valid_cities_df['city_clean'].unique().tolist()
                
                st.sidebar.write(f"Found {len(cities)} cities with data")
                
                if len(cities) > 0:
                    # Sort cities and add count information
                    city_counts = valid_cities_df['city_clean'].value_counts().to_dict()
                    city_info = [f"{city} ({city_counts.get(city, 0)} customers)" for city in sorted(cities)]
                    
                    # City selection
                    selected_city_info = st.sidebar.selectbox("Select City", city_info)
                    selected_city = selected_city_info.split(" (")[0]  # Extract city name
                    
                    # Filter customers by city
                    city_customers = customer_data[customer_data['city_clean'] == selected_city]
                    
                    st.sidebar.write(f"Showing {len(city_customers)} customers in {selected_city}")
                    
                    # Customer selection from filtered list
                    if len(city_customers) > 0:
                        selected_customer_id = st.sidebar.selectbox(
                            f"Select Customer from {selected_city}",
                            city_customers.index.tolist()[:100]  # Limit to first 100 for performance
                        )
                    else:
                        st.sidebar.warning(f"No customers found in {selected_city}")
                        selected_customer_id = st.sidebar.selectbox(
                            "Select Customer",
                            customer_data.index.tolist()[:100]  # Limit to first 100 for performance
                        )
                else:
                    st.sidebar.warning("No valid city information found in the dataset.")
                    # Show the actual city values for debugging
                    st.sidebar.write(f"Raw city values sample: {customer_data['city'].dropna().sample(min(5, len(customer_data['city'].dropna()))).tolist()}")
                    
                    selected_customer_id = st.sidebar.selectbox(
                        "Select Customer",
                        customer_data.index.tolist()[:100]  # Limit to first 100 for performance
                    )
            except Exception as e:
                st.sidebar.error(f"Error processing city data: {e}")
                st.sidebar.write("City data could not be processed. Using all customers instead.")
                selected_customer_id = st.sidebar.selectbox(
                    "Select Customer",
                    customer_data.index.tolist()[:100]  # Limit to first 100 for performance
                )
        else:
            st.sidebar.warning("City information not available in the dataset.")
            st.sidebar.write(f"Available columns: {customer_data.columns.tolist()}")
            selected_customer_id = st.sidebar.selectbox(
                "Select Customer",
                customer_data.index.tolist()[:100]  # Limit to first 100 for performance
            )
    
    else:  # All Customers
        # Customer selection from all customers
        selected_customer_id = st.sidebar.selectbox(
            "Select Customer",
            customer_data.index.tolist()[:100]  # Limit to first 100 for performance
        )
    
    # Display customer profile if a customer is selected
    if selected_customer_id:
        # Get customer data
        customer = customer_data.loc[selected_customer_id].to_dict()
        
        # Get customer transactions
        customer_transactions = transactions_df[transactions_df['customer_id'] == selected_customer_id].copy()
        
        # Sort transactions by date (most recent first)
        if 'invoice_date' in customer_transactions.columns:
            try:
                # Handle zero values
                customer_transactions['invoice_date'] = customer_transactions['invoice_date'].replace(0, np.nan)
                customer_transactions['invoice_date'] = customer_transactions['invoice_date'].replace('0', np.nan)
                
                # Try multiple date formats with error handling
                customer_transactions['invoice_date'] = pd.to_datetime(customer_transactions['invoice_date'], errors='coerce')
                
                # Remove rows with invalid dates for sorting
                valid_dates = customer_transactions.dropna(subset=['invoice_date'])
                if not valid_dates.empty:
                    customer_transactions = valid_dates.sort_values('invoice_date', ascending=False)
            except Exception as e:
                st.warning(f"Error processing dates: {e}")
                # Keep original order if date processing fails
        
        # Extract first name from email
        if 'email' in customer:
            first_name = customer['email'].split('@')[0].split('.')[0].title()
        else:
            first_name = "Customer"
        
        # Create customer profile card
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        
        # Profile header
        st.markdown('<div class="profile-header">', unsafe_allow_html=True)
        st.markdown(generate_avatar(selected_customer_id, first_name), unsafe_allow_html=True)
        st.markdown(f"""
        <div>
            <div class="profile-name">{first_name} <span class="profile-segment">{customer.get('segment_name', 'Unknown')}</span></div>
            <div>{customer.get('email', 'No email available')}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Profile information
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="profile-info">', unsafe_allow_html=True)
            
            # Customer ID
            st.markdown(f"""
            <div class="profile-info-item">
                <div class="profile-info-label">Customer ID:</div>
                <div class="profile-info-value">{selected_customer_id}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Gender
            if 'gender' in customer:
                st.markdown(f"""
                <div class="profile-info-item">
                    <div class="profile-info-label">Gender:</div>
                    <div class="profile-info-value">{customer['gender']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Age
            if 'age' in customer:
                st.markdown(f"""
                <div class="profile-info-item">
                    <div class="profile-info-label">Age:</div>
                    <div class="profile-info-value">{customer['age']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # City
            if 'city' in customer:
                st.markdown(f"""
                <div class="profile-info-item">
                    <div class="profile-info-label">City:</div>
                    <div class="profile-info-value">{customer['city']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="profile-info">', unsafe_allow_html=True)
            
            # First purchase date
            if 'first_purchase_date' in customer:
                try:
                    # Handle invalid date values
                    if pd.notna(customer['first_purchase_date']) and customer['first_purchase_date'] != 0 and customer['first_purchase_date'] != '0':
                        first_purchase = pd.to_datetime(customer['first_purchase_date'], errors='coerce')
                        if pd.notna(first_purchase):
                            first_purchase = first_purchase.strftime('%B %d, %Y')
                        else:
                            first_purchase = "Not available"
                    else:
                        first_purchase = "Not available"
                except:
                    first_purchase = "Not available"
                
                st.markdown(f"""
                <div class="profile-info-item">
                    <div class="profile-info-label">First Purchase:</div>
                    <div class="profile-info-value">{first_purchase}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Last purchase date
            if 'last_purchase_date' in customer:
                try:
                    # Handle invalid date values
                    if pd.notna(customer['last_purchase_date']) and customer['last_purchase_date'] != 0 and customer['last_purchase_date'] != '0':
                        last_purchase = pd.to_datetime(customer['last_purchase_date'], errors='coerce')
                        if pd.notna(last_purchase):
                            last_purchase = last_purchase.strftime('%B %d, %Y')
                        else:
                            last_purchase = "Not available"
                    else:
                        last_purchase = "Not available"
                except:
                    last_purchase = "Not available"
                
                st.markdown(f"""
                <div class="profile-info-item">
                    <div class="profile-info-label">Last Purchase:</div>
                    <div class="profile-info-value">{last_purchase}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Days since last purchase
            if 'recency' in customer:
                st.markdown(f"""
                <div class="profile-info-item">
                    <div class="profile-info-label">Days Since Purchase:</div>
                    <div class="profile-info-value">{int(customer['recency'])}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Primary category
            if 'primary_category' in customer:
                st.markdown(f"""
                <div class="profile-info-item">
                    <div class="profile-info-label">Primary Category:</div>
                    <div class="profile-info-value">{customer['primary_category']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Customer metrics
        st.markdown('<h2 class="sub-header">Customer Metrics</h2>', unsafe_allow_html=True)
        
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{customer.get('transaction_count', 0):.0f}</div>
                <div class="metric-label">Total Transactions</div>
            </div>
            """, unsafe_allow_html=True)
        
        with metric_col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">₹{customer.get('total_spend', 0):.2f}</div>
                <div class="metric-label">Total Spend</div>
            </div>
            """, unsafe_allow_html=True)
        
        with metric_col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">₹{customer.get('average_transaction_value', 0):.2f}</div>
                <div class="metric-label">Avg. Transaction Value</div>
            </div>
            """, unsafe_allow_html=True)
        
        with metric_col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{customer.get('purchase_frequency', 0):.2f}</div>
                <div class="metric-label">Purchases per Month</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Create tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["Purchase History", "Category Preferences", "Recommendations", "Geographic Distribution"])
        
        with tab1:
            st.markdown('<div class="tab-section-header"><h3>Purchase History</h3></div>', unsafe_allow_html=True)
            
            if len(customer_transactions) > 0:
                # Display transaction table
                display_cols = ['invoice_no', 'invoice_date', 'product_name', 'category', 'quantity', 'price', 'total_amount', 'payment_method', 'shopping_mall']
                display_cols = [col for col in display_cols if col in customer_transactions.columns]
                
                # Format date column
                if 'invoice_date' in display_cols:
                    customer_transactions['invoice_date'] = customer_transactions['invoice_date'].dt.strftime('%Y-%m-%d')
                
                # Format numeric columns
                for col in ['price', 'total_amount']:
                    if col in display_cols:
                        customer_transactions[col] = customer_transactions[col].map('₹{:.2f}'.format)
                
                # Display transactions
                st.dataframe(customer_transactions[display_cols], use_container_width=True)
                
                # Transaction trends over time
                if 'invoice_date' in customer_transactions.columns and len(customer_transactions) > 1:
                    st.markdown('<div class="tab-section-header"><h3>Spending Trends</h3></div>', unsafe_allow_html=True)
                    
                    # Convert back to datetime for plotting
                    try:
                        # Handle zero values
                        customer_transactions['invoice_date'] = customer_transactions['invoice_date'].replace(0, np.nan)
                        customer_transactions['invoice_date'] = customer_transactions['invoice_date'].replace('0', np.nan)
                        
                        # Try to convert with error handling
                        customer_transactions['invoice_date'] = pd.to_datetime(customer_transactions['invoice_date'], errors='coerce')
                        
                        # Drop rows with invalid dates for this analysis
                        valid_dates = customer_transactions.dropna(subset=['invoice_date'])
                        
                        if not valid_dates.empty:
                            # Group by month and calculate total spend
                            monthly_spend = valid_dates.groupby(valid_dates['invoice_date'].dt.to_period('M'))['total_amount'].sum().reset_index()
                            monthly_spend['invoice_date'] = monthly_spend['invoice_date'].astype(str)
                            
                            # Convert total_amount to numeric, handling errors
                            try:
                                # If total_amount is already numeric, use it directly
                                if pd.api.types.is_numeric_dtype(monthly_spend['total_amount']):
                                    pass
                                # If it's a string with dollar signs, try to convert
                                elif isinstance(monthly_spend['total_amount'].iloc[0], str):
                                    # More robust cleaning for malformed values
                                    def clean_amount(val):
                                        if not isinstance(val, str):
                                            return val
                                        
                                        # Remove dollar signs and commas
                                        val = val.replace('$', '').replace(',', '')
                                        
                                        # Handle malformed values like '206818.484692.66'
                                        if val.count('.') > 1:
                                            # Take only the first decimal part
                                            parts = val.split('.')
                                            val = parts[0] + '.' + parts[1]
                                        
                                        try:
                                            return float(val)
                                        except:
                                            return 0.0
                                    
                                    # Apply the cleaning function
                                    monthly_spend['total_amount'] = monthly_spend['total_amount'].apply(clean_amount)
                            except Exception as e:
                                st.error(f"Error converting total_amount to numeric: {e}")
                                # Fallback to simple numeric values
                                monthly_spend['total_amount'] = 1.0
                                st.write("Using placeholder values for visualization due to data conversion errors.")
                            
                            # Create line chart
                            fig = px.line(
                                monthly_spend,
                                x='invoice_date',
                                y='total_amount',
                                title='Monthly Spending Trends',
                                markers=True
                            )
                            
                            fig.update_layout(
                                xaxis_title='Month',
                                yaxis_title='Total Spend (₹)',
                                xaxis=dict(tickangle=45)
                            )
                            
                            st.plotly_chart(fig, use_container_width=True, key="monthly_spending_trends")
                        else:
                            st.info("Cannot create spending trends chart: no valid dates available.")
                    except Exception as e:
                        st.error(f"Error processing date data for trends: {e}")
                        st.info("Unable to create spending trends chart due to data issues.")
            else:
                st.info("No transaction history available for this customer.")
        
        with tab2:
            st.markdown('<div class="tab-section-header"><h3>Category Preferences</h3></div>', unsafe_allow_html=True)
            
            if len(customer_transactions) > 0 and 'category' in customer_transactions.columns:
                # Calculate category spending directly from transactions
                st.info("Showing category preferences based on actual transaction history")
                
                # Group by category and calculate total spend
                category_spend = customer_transactions.groupby('category')['total_amount'].sum()
                
                # Convert string amounts to numeric if needed
                if not pd.api.types.is_numeric_dtype(category_spend):
                    try:
                        # First make a copy to avoid modifying the original
                        category_spend_clean = category_spend.copy()
                        
                        # More robust cleaning for malformed values
                        def clean_amount(val):
                            if not isinstance(val, str):
                                return val
                            
                            # Remove dollar signs and commas
                            val = val.replace('$', '').replace(',', '')
                            
                            # Handle malformed values like '206818.484692.66'
                            if val.count('.') > 1:
                                # Take only the first decimal part
                                parts = val.split('.')
                                val = parts[0] + '.' + parts[1]
                            
                            try:
                                return float(val)
                            except:
                                return 0.0
                        
                        # Apply the cleaning function
                        category_spend_clean = category_spend.apply(clean_amount)
                        
                        category_spend = category_spend_clean
                    except Exception as e:
                        st.error(f"Error converting amounts to numeric: {e}")
                        # Fallback to simple numeric values
                        category_spend = pd.Series([1] * len(category_spend), index=category_spend.index)
                        st.write("Using placeholder values for visualization due to data conversion errors.")
                
                # Calculate percentages
                total_spend = category_spend.sum()
                if total_spend > 0:
                    category_pct = (category_spend / total_spend * 100).round(1)
                else:
                    category_pct = pd.Series([0] * len(category_spend), index=category_spend.index)
                
                # Create data for pie chart
                categories = category_spend.index.tolist()
                percentages = category_pct.values.tolist()
                
                # Create pie chart
                fig = px.pie(
                    values=percentages,
                    names=categories,
                    title='Category Spending Distribution (Based on Transaction History)',
                    hole=0.4
                )
                
                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label'
                )
                
                # Add transparent legend background
                fig.update_layout(
                    legend=dict(bgcolor='rgba(0,0,0,0)')
                )
                
                st.plotly_chart(fig, use_container_width=True, key="category_pie_chart")
                
                # Display category preferences as a table
                category_data = []
                
                for category, spend, pct in zip(categories, category_spend.values, category_pct.values):
                    # Format the spend value based on its type
                    if isinstance(spend, (int, float)):
                        spend_formatted = f"₹{spend:.2f}"
                    else:
                        spend_formatted = str(spend)
                    
                    category_data.append({
                        'Category': category,
                        'Spend': spend_formatted,
                        'Percentage': f"{pct:.1f}%"
                    })
                
                # Sort by percentage (descending)
                category_data.sort(key=lambda x: float(x['Percentage'].replace('%', '')), reverse=True)
                
                # Display as dataframe
                st.dataframe(pd.DataFrame(category_data), use_container_width=True)
            
            # Fallback to pre-calculated values if no transaction data
            elif [col for col in customer.keys() if col.startswith('pct_')]:
                st.info("Showing pre-calculated category preferences (may not match transaction history)")
                # Get category preference columns
                category_cols = [col for col in customer.keys() if col.startswith('pct_')]
                
                # Create data for pie chart
                categories = [col.replace('pct_', '').title() for col in category_cols]
                percentages = [customer[col] for col in category_cols]
                
                # Create pie chart
                fig = px.pie(
                    values=percentages,
                    names=categories,
                    title='Category Spending Distribution (Pre-calculated)',
                    hole=0.4
                )
                
                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label'
                )
                
                # Add transparent legend background
                fig.update_layout(
                    legend=dict(bgcolor='rgba(0,0,0,0)')
                )
                
                st.plotly_chart(fig, use_container_width=True, key="category_pie_chart_precalc")
                
                # Display category preferences as a table
                category_data = []
                
                for cat_col, spend_col in zip(
                    [col for col in category_cols],
                    [col.replace('pct_', 'spend_') for col in category_cols]
                ):
                    if spend_col in customer:
                        category_data.append({
                            'Category': cat_col.replace('pct_', '').title(),
                            'Spend': f"₹{customer[spend_col]:.2f}",
                            'Percentage': f"{customer[cat_col]:.1f}%"
                        })
                
                # Sort by percentage (descending)
                category_data.sort(key=lambda x: float(x['Percentage'].replace('%', '')), reverse=True)
                
                # Display as dataframe
                st.dataframe(pd.DataFrame(category_data), use_container_width=True)
            else:
                st.info("No category preference data available for this customer.")
            
            # Product preferences
            if len(customer_transactions) > 0:
                st.markdown('<div class="tab-section-header"><h3>Top Purchased Products</h3></div>', unsafe_allow_html=True)
                
                # Get top products
                top_products = customer_transactions['product_name'].value_counts().head(5)
                
                # Create bar chart
                fig = px.bar(
                    x=top_products.index,
                    y=top_products.values,
                    title='Top Purchased Products',
                    labels={'x': 'Product', 'y': 'Purchase Count'}
                )
                
                # Add transparent legend background
                fig.update_layout(
                    legend=dict(bgcolor='rgba(0,0,0,0)')
                )
                
                st.plotly_chart(fig, use_container_width=True, key="top_products_chart")
        
        with tab3:
            # Product recommendations
            st.markdown('<div class="tab-section-header"><h3>Recommended Products</h3></div>', unsafe_allow_html=True)
            
            recommendations = generate_product_recommendations(customer, transactions_df)
            
            rec_col1, rec_col2, rec_col3 = st.columns(3)
            
            for i, (col, rec) in enumerate(zip([rec_col1, rec_col2, rec_col3], recommendations)):
                with col:
                    st.markdown(f"""
                    <div class="recommendation-card">
                        <div class="recommendation-title">{rec['title']}</div>
                        <div class="recommendation-text">{rec['reason']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Special offers
            st.markdown('<div class="tab-section-header"><h3>Special Offers</h3></div>', unsafe_allow_html=True)
            
            offers = generate_special_offers(customer)
            
            offer_col1, offer_col2 = st.columns(2)
            
            for i, (col, offer) in enumerate(zip([offer_col1, offer_col2], offers)):
                with col:
                    st.markdown(f"""
                    <div class="recommendation-card">
                        <div class="recommendation-title">{offer['title']}</div>
                        <div class="recommendation-text">{offer['text']}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        with tab4:
            st.markdown('<div class="tab-section-header"><h3>Customer Geographic Distribution</h3></div>', unsafe_allow_html=True)
            
            # Create a DataFrame for mapping customer locations
            mapping_data = pd.DataFrame(index=customer_data.index)
            
            # Add segment information for coloring
            if 'segment_name' in customer_data.columns:
                mapping_data['segment_name'] = customer_data['segment_name'].values
            else:
                # If we have a selected customer, use their segment
                segment = customer.get('segment_name', '')
                mapping_data['segment_name'] = segment if segment else 'Unknown'
            
            # Clean and prepare city data for mapping
            mapping_data['city'] = 'Unknown'  # Set default value
            
            # Extract city from location if it exists
            if 'location' in customer_data.columns and pd.notna(customer_data['location']).any():
                for idx, row in customer_data.iterrows():
                    if pd.notna(row.get('location')):
                        city = str(row['location']).split(',')[0].strip()
                        if city and city != 'Unknown':
                            mapping_data.at[idx, 'city'] = city
            
            # Handle one-hot encoded city columns
            elif any(col.startswith('city_') for col in customer_data.columns):
                city_columns = [col for col in customer_data.columns if col.startswith('city_')]
                
                for idx, row in customer_data.iterrows():
                    for city_col in city_columns:
                        if pd.notna(row.get(city_col)) and row.get(city_col) == 1:
                            city_name = city_col.replace('city_', '')
                            mapping_data.at[idx, 'city'] = city_name
            
            # Use direct city column if available
            elif 'city' in customer_data.columns:
                for idx, row in customer_data.iterrows():
                    if pd.notna(row.get('city')):
                        mapping_data.at[idx, 'city'] = row['city']
            
            # Create the map using the prepared data
            fig = create_customer_location_map(mapping_data)
            st.plotly_chart(fig, use_container_width=True, key="all_customers_map")
            
            # Display map of customers in the same segment
            if 'segment_name' in customer and customer.get('segment_name'):
                segment_name = customer.get('segment_name', 'Unknown')
                segment_customers = mapping_data.copy()
                
                # Filter for customers in the same segment, if we have multiple customers
                if len(mapping_data) > 1 and 'segment_name' in mapping_data.columns:
                    segment_customers = mapping_data[mapping_data['segment_name'] == segment_name]
                
                # Only display if we have customers in this segment
                if len(segment_customers) > 0:
                    segment_title = f"{segment_name} Customers by Location"
                    st.markdown(f'<div class="tab-section-header"><h3>{segment_title}</h3></div>', unsafe_allow_html=True)
                    fig = create_customer_location_map(segment_customers)
                    st.plotly_chart(fig, use_container_width=True, key="segment_customers_map")
    
    else:
        st.info("Please select a customer from the sidebar to view their profile.")

if __name__ == "__main__":
    main() 