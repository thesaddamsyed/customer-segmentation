"""
Segment Analysis Page

This page provides detailed analysis of customer segments with interactive visualizations.
"""
import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Import custom modules
from src.data_processing.data_loader import load_and_process
from src.segmentation.segmentation import CustomerSegmentation
from src.visualization.dashboard import (
    create_rfm_heatmap,
    create_category_preference_chart,
    create_spending_trend_chart,
    create_payment_method_chart,
    create_mall_distribution_chart,
    create_age_distribution_chart,
    create_city_distribution_chart,
    create_customer_location_map
)

# Set page configuration
st.set_page_config(
    page_title="Segment Analysis - Mall Customer Segmentation",
    page_icon="📊",
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
            margin-bottom: 1.5rem;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #5E35B1;
            margin-bottom: 1.5rem;
        }
        .filter-container {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
        }
        .insight-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
        }
        .insight-title {
            font-size: 1.2rem;
            font-weight: bold;
            color: #4527A0;
            margin-bottom: 0.5rem;
        }
        .insight-text {
            font-size: 1rem;
            color: #6c757d;
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

# Function to generate segment insights
def generate_segment_insights(segment_profiles, segment_name):
    insights = []
    
    # Get the profile for the selected segment
    profile = segment_profiles[segment_profiles['segment_name'] == segment_name].iloc[0]
    
    # Calculate average values across all segments
    avg_recency = segment_profiles['recency'].mean()
    avg_frequency = segment_profiles['transaction_count'].mean()
    avg_spend = segment_profiles['total_spend'].mean()
    avg_transaction = segment_profiles['average_transaction_value'].mean()
    
    # Generate insights based on segment characteristics
    if segment_name == 'VIP':
        insights.append({
            'title': 'High Value Customers',
            'text': f"VIP customers spend ₹{profile['total_spend']:.2f} on average, which is {(profile['total_spend']/avg_spend - 1)*100:.1f}% higher than the average customer."
        })
        insights.append({
            'title': 'Frequent Shoppers',
            'text': f"VIP customers make {profile['transaction_count']:.1f} transactions on average, compared to the overall average of {avg_frequency:.1f} transactions."
        })
        insights.append({
            'title': 'Retention Strategy',
            'text': "Focus on exclusive offers, personalized recommendations, and loyalty rewards to retain these valuable customers."
        })
    
    elif segment_name == 'At Risk':
        insights.append({
            'title': 'Churn Risk',
            'text': f"At Risk customers haven't made a purchase in {profile['recency']:.0f} days, which is {(profile['recency']/avg_recency - 1)*100:.1f}% longer than the average customer."
        })
        insights.append({
            'title': 'Historical Value',
            'text': f"Despite their inactivity, these customers have historically spent ₹{profile['total_spend']:.2f} on average, making them valuable to retain."
        })
        insights.append({
            'title': 'Win-back Strategy',
            'text': "Implement win-back campaigns with special discounts and personalized offers based on their past purchase history."
        })
    
    elif segment_name == 'New':
        insights.append({
            'title': 'Recent Acquisition',
            'text': f"New customers have a shorter customer lifetime of {profile['customer_lifetime']:.0f} days, indicating they've been recently acquired."
        })
        insights.append({
            'title': 'Growth Potential',
            'text': f"These customers have made {profile['transaction_count']:.1f} transactions so far, with potential for increased engagement."
        })
        insights.append({
            'title': 'Onboarding Strategy',
            'text': "Focus on welcome offers, educational content, and excellent customer service to encourage repeat purchases."
        })
    
    elif segment_name == 'Regular':
        insights.append({
            'title': 'Consistent Shoppers',
            'text': f"Regular customers shop with a frequency of {profile['purchase_frequency']:.2f} transactions per month, showing consistent engagement."
        })
        insights.append({
            'title': 'Moderate Spending',
            'text': f"These customers spend ₹{profile['average_transaction_value']:.2f} per transaction, close to the overall average of ₹{avg_transaction:.2f}."
        })
        insights.append({
            'title': 'Engagement Strategy',
            'text': "Encourage category exploration and increase purchase frequency through loyalty rewards and cross-selling."
        })
    
    elif segment_name == 'Occasional':
        insights.append({
            'title': 'Infrequent Shoppers',
            'text': f"Occasional customers make only {profile['transaction_count']:.1f} transactions on average, {(1 - profile['transaction_count']/avg_frequency)*100:.1f}% less than the average customer."
        })
        insights.append({
            'title': 'Lower Spending',
            'text': f"These customers spend ₹{profile['total_spend']:.2f} on average, below the overall average of ₹{avg_spend:.2f}."
        })
        insights.append({
            'title': 'Activation Strategy',
            'text': "Use seasonal promotions and category-specific offers to increase engagement and purchase frequency."
        })
    
    else:
        insights.append({
            'title': 'Segment Overview',
            'text': f"This segment contains {profile['customer_count']:.0f} customers, representing {profile['customer_percentage']:.1f}% of the total customer base."
        })
        insights.append({
            'title': 'Spending Behavior',
            'text': f"Customers in this segment spend ₹{profile['total_spend']:.2f} on average across {profile['transaction_count']:.1f} transactions."
        })
        insights.append({
            'title': 'Engagement Strategy',
            'text': "Analyze this segment's unique characteristics to develop targeted marketing strategies."
        })
    
    return insights

# Main function
def main():
    # Load CSS
    load_css()
    
    # Display header
    st.markdown('<h1 class="main-header">Segment Analysis</h1>', unsafe_allow_html=True)
    
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
    
    # Add segment information to transactions
    transactions_with_segments = transactions_df.merge(
        customer_segments[['segment', 'segment_name']], 
        left_on='customer_id', 
        right_index=True,
        how='left'
    )
    
    # Create filters
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    
    # Segment filter - Fix for duplicate segments by using unique values
    unique_segment_names = ['All Segments'] + sorted(segment_profiles['segment_name'].unique().tolist())
    selected_segment = st.selectbox('Select Segment', unique_segment_names)
    
    # Date range filter
    transactions_df['invoice_date'] = pd.to_datetime(transactions_df['invoice_date'])
    min_date = transactions_df['invoice_date'].min().date()
    max_date = transactions_df['invoice_date'].max().date()
    
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input('Start Date', min_date)
    with date_col2:
        end_date = st.date_input('End Date', max_date)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Filter data based on selections
    if selected_segment != 'All Segments':
        filtered_customers = customer_segments[customer_segments['segment_name'] == selected_segment]
        filtered_transactions = transactions_with_segments[
            (transactions_with_segments['segment_name'] == selected_segment) &
            (transactions_with_segments['invoice_date'].dt.date >= start_date) &
            (transactions_with_segments['invoice_date'].dt.date <= end_date)
        ]
    else:
        filtered_customers = customer_segments
        filtered_transactions = transactions_with_segments[
            (transactions_with_segments['invoice_date'].dt.date >= start_date) &
            (transactions_with_segments['invoice_date'].dt.date <= end_date)
        ]
    
    # Display segment insights if a specific segment is selected
    if selected_segment != 'All Segments':
        st.markdown('<h2 class="sub-header">Segment Insights</h2>', unsafe_allow_html=True)
        
        insights = generate_segment_insights(segment_profiles, selected_segment)
        
        insight_cols = st.columns(len(insights))
        
        for i, (col, insight) in enumerate(zip(insight_cols, insights)):
            with col:
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">{insight['title']}</div>
                    <div class="insight-text">{insight['text']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Create visualizations
    st.markdown('<h2 class="sub-header">Segment Analysis</h2>', unsafe_allow_html=True)
    
    # Create two columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        # RFM Heatmap
        st.markdown('<h3>RFM Analysis</h3>', unsafe_allow_html=True)
        fig = create_rfm_heatmap(filtered_customers)
        st.plotly_chart(fig, use_container_width=True, key="rfm_heatmap")
        
        # Category Preferences
        st.markdown('<h3>Category Preferences</h3>', unsafe_allow_html=True)
        fig = create_category_preference_chart(filtered_customers)
        st.plotly_chart(fig, use_container_width=True, key="category_preferences")
        
        # Age Distribution
        st.markdown('<h3>Age Distribution</h3>', unsafe_allow_html=True)
        fig = create_age_distribution_chart(filtered_customers)
        st.plotly_chart(fig, use_container_width=True, key="age_distribution")
    
    with col2:
        # Spending Trends
        st.markdown('<h3>Spending Trends</h3>', unsafe_allow_html=True)
        fig = create_spending_trend_chart(filtered_transactions)
        st.plotly_chart(fig, use_container_width=True, key="spending_trends")
        
        # Payment Method Preferences
        st.markdown('<h3>Payment Method Preferences</h3>', unsafe_allow_html=True)
        fig = create_payment_method_chart(filtered_transactions)
        st.plotly_chart(fig, use_container_width=True, key="payment_methods")
        
        # Mall Distribution
        st.markdown('<h3>Shopping Mall Distribution</h3>', unsafe_allow_html=True)
        fig = create_mall_distribution_chart(filtered_transactions)
        st.plotly_chart(fig, use_container_width=True, key="mall_distribution")
    
    # City Distribution (full width)
    st.markdown('<h3>Customer Distribution by City</h3>', unsafe_allow_html=True)
    fig = create_city_distribution_chart(filtered_customers)
    st.plotly_chart(fig, use_container_width=True, key="city_distribution")
    
    # Geographic Distribution Map (full width)
    st.markdown('<h3>Geographic Distribution</h3>', unsafe_allow_html=True)
    
    # Prepare data for the location map
    map_data = pd.DataFrame(index=filtered_customers.index)
    map_data['segment_name'] = filtered_customers['segment_name'].values if 'segment_name' in filtered_customers.columns else 'All Customers'
    
    # Set default city value
    map_data['city'] = 'Unknown'
    
    # Handle one-hot encoded city columns
    city_columns = [col for col in filtered_customers.columns if col.startswith('city_')]
    if len(city_columns) > 0:
        for idx, row in filtered_customers.iterrows():
            for city_col in city_columns:
                if pd.notna(row.get(city_col)) and row.get(city_col) == 1:
                    city_name = city_col.replace('city_', '')
                    map_data.at[idx, 'city'] = city_name
    # Direct city column if available
    elif 'city' in filtered_customers.columns:
        for idx, row in filtered_customers.iterrows():
            if pd.notna(row.get('city')):
                map_data.at[idx, 'city'] = row['city']
    
    fig = create_customer_location_map(map_data)
    st.plotly_chart(fig, use_container_width=True, key="geographic_distribution")
    
    # Display segment recommendations
    if selected_segment != 'All Segments':
        st.markdown('<h2 class="sub-header">Marketing Recommendations</h2>', unsafe_allow_html=True)
        
        recommendations = model.get_segment_recommendations()
        
        if selected_segment in recommendations:
            rec = recommendations[selected_segment]
            
            rec_col1, rec_col2 = st.columns(2)
            
            with rec_col1:
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">Email Frequency</div>
                    <div class="insight-text">{rec['email_frequency']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">Message Tone</div>
                    <div class="insight-text">{rec['message_tone']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with rec_col2:
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">Offer Type</div>
                    <div class="insight-text">{rec['offer_type']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">Strategy</div>
                    <div class="insight-text">{rec['strategy']}</div>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 