"""
Mall Customer Segmentation System - Main Application

This is the main entry point for the Mall Customer Segmentation System.
It provides a dashboard with key insights and navigation to other pages.
"""
import os
import streamlit as st
import pandas as pd
import numpy as np
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
import json
import requests

# Import custom modules
from src.data_processing.data_loader import load_and_process
from src.segmentation.segmentation import CustomerSegmentation
from src.visualization.dashboard import (
    create_segment_distribution_chart,
    create_segment_metrics_chart,
    create_segment_pca_chart,
    create_dashboard_metrics,
    create_customer_location_map
)

# Set page configuration
st.set_page_config(
    page_title="Mall Customer Segmentation",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
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
        .stButton button {
            background-color: #4527A0;
            color: white;
            border-radius: 5px;
            padding: 0.5rem 1rem;
            border: none;
        }
        .stButton button:hover {
            background-color: #5E35B1;
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
    </style>
    """, unsafe_allow_html=True)

# Load Lottie animation
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

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

# Function to load or train segmentation model
@st.cache_resource
def load_or_train_model(customer_features):
    if os.path.exists(os.path.join(MODEL_PATH, 'kmeans.pkl')):
        # Load model if it exists
        model = CustomerSegmentation.load_model(MODEL_PATH)
    else:
        # Train model if it doesn't exist
        os.makedirs(MODEL_PATH, exist_ok=True)
        model = CustomerSegmentation(n_segments=5)
        model.fit(customer_features)
        model.save_model(MODEL_PATH)
    
    return model

# Main function
def main():
    # Load CSS
    load_css()
    
    # Display header
    st.markdown('<h1 class="main-header">Mall Customer Segmentation System</h1>', unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading data..."):
        transactions_df, customer_features = load_cached_data()
    
    # Load or train model
    with st.spinner("Loading segmentation model..."):
        model = load_or_train_model(customer_features)
    
    # Get customer segments
    customer_segments = model.get_customer_segments(customer_features)
    
    # Get segment profiles
    segment_profiles = model.get_segment_profiles()
    
    # Get PCA components for visualization
    pca_df = model.get_pca_components(customer_features)
    
    # Calculate dashboard metrics
    metrics = create_dashboard_metrics(customer_segments, transactions_df)
    
    # Create dashboard layout with more space for the sidebar
    col1, col2 = st.columns([1.2, 3])
    
    with col1:
        # Display Lottie animation
        lottie_url = "https://assets5.lottiefiles.com/packages/lf20_jcikwtux.json"
        lottie_json = load_lottie_url(lottie_url)
        if lottie_json:
            st_lottie(lottie_json, height=250, key="shopping")
        
        # Display key metrics
        st.markdown('<h2 class="sub-header">Key Metrics</h2>', unsafe_allow_html=True)
        
        # Format metrics
        total_customers = f"{metrics.get('total_customers', 0):,.0f}"
        total_revenue = f"${metrics.get('total_revenue', 0):,.2f}"
        avg_clv = f"${metrics.get('avg_customer_lifetime_value', 0):,.2f}"
        avg_transaction = f"${metrics.get('avg_transaction_value', 0):,.2f}"
        
        # Display metrics one by one instead of a grid for better mobile responsiveness
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_customers}</div>
            <div class="metric-label">Total Customers</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_revenue}</div>
            <div class="metric-label">Total Revenue</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg_clv}</div>
            <div class="metric-label">Avg. Customer Value</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg_transaction}</div>
            <div class="metric-label">Avg. Transaction</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Display segment distribution chart
        st.markdown('<h2 class="sub-header">Customer Segments</h2>', unsafe_allow_html=True)
        fig = create_segment_distribution_chart(segment_profiles)
        # Adjust legend position and size
        fig.update_layout(
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            margin=dict(l=20, r=20, t=40, b=20),
            height=350
        )
        st.plotly_chart(fig, use_container_width=True, key="segment_distribution")
        
        # Display segment metrics chart
        st.markdown('<h2 class="sub-header">Segment Comparison</h2>', unsafe_allow_html=True)
        fig = create_segment_metrics_chart(segment_profiles)
        # Adjust legend position and size
        fig.update_layout(
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            margin=dict(l=20, r=20, t=40, b=20),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True, key="segment_metrics")
    
    # Create container for PCA visualization
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="sub-header">Customer Segmentation Visualization (PCA)</h2>', unsafe_allow_html=True)
    fig = create_segment_pca_chart(pca_df)
    # Adjust layout
    fig.update_layout(
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5),
        margin=dict(l=20, r=20, t=40, b=80),  # More bottom margin for legend
        height=450
    )
    st.plotly_chart(fig, use_container_width=True, key="pca_visualization")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display segment profiles in a container
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="sub-header">Segment Profiles</h2>', unsafe_allow_html=True)
    
    # Format segment profiles for display
    display_profiles = segment_profiles[['segment_name', 'customer_count', 'customer_percentage', 
                                         'recency', 'transaction_count', 'total_spend', 
                                         'average_transaction_value', 'purchase_frequency']].copy()
    
    # Rename columns for better display
    display_profiles.columns = ['Segment Name', 'Customer Count', 'Customer %', 
                               'Recency (Days)', 'Transaction Count', 'Total Spend ($)', 
                               'Avg. Transaction ($)', 'Purchase Frequency']
    
    # Format numeric columns
    display_profiles['Customer %'] = display_profiles['Customer %'].round(1)
    display_profiles['Recency (Days)'] = display_profiles['Recency (Days)'].round(0).astype(int)
    display_profiles['Transaction Count'] = display_profiles['Transaction Count'].round(1)
    display_profiles['Total Spend ($)'] = display_profiles['Total Spend ($)'].round(2)
    display_profiles['Avg. Transaction ($)'] = display_profiles['Avg. Transaction ($)'].round(2)
    display_profiles['Purchase Frequency'] = display_profiles['Purchase Frequency'].round(2)
    
    # Display profiles with scrolling enabled
    st.dataframe(display_profiles, use_container_width=True, height=300)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display geographic distribution in a container
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="sub-header">Customer Geographic Distribution</h2>', unsafe_allow_html=True)
    
    # Prepare data for the location map
    map_data = pd.DataFrame(index=customer_segments.index)
    map_data['segment_name'] = customer_segments['segment_name'].values
    
    # Set default city value
    map_data['city'] = 'Unknown'
    
    # Handle one-hot encoded city columns
    city_columns = [col for col in customer_segments.columns if col.startswith('city_')]
    if len(city_columns) > 0:
        for idx, row in customer_segments.iterrows():
            for city_col in city_columns:
                if pd.notna(row.get(city_col)) and row.get(city_col) == 1:
                    city_name = city_col.replace('city_', '')
                    map_data.at[idx, 'city'] = city_name
    # Direct city column if available
    elif 'city' in customer_segments.columns:
        for idx, row in customer_segments.iterrows():
            if pd.notna(row.get('city')):
                map_data.at[idx, 'city'] = row['city']
    
    fig = create_customer_location_map(map_data)
    # Adjust layout
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        height=450
    )
    st.plotly_chart(fig, use_container_width=True, key="geographic_distribution")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add a note about navigation
    st.info("""
    **Navigate to other pages using the sidebar to:**
    - Explore detailed segment analysis
    - Set up automated email campaigns
    - View customer profiles and purchase history
    - Manage marketing recommendations
    """)

if __name__ == "__main__":
    main() 