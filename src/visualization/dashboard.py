"""
Dashboard module for visualizing customer segmentation data.
"""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple, Optional


def create_segment_distribution_chart(segment_profiles: pd.DataFrame) -> go.Figure:
    """
    Create a pie chart showing the distribution of customers across segments.
    
    Args:
        segment_profiles: DataFrame with segment profiles
        
    Returns:
        Plotly figure object
    """
    fig = px.pie(
        segment_profiles,
        values='customer_count',
        names='segment_name',
        title='Customer Segment Distribution',
        color_discrete_sequence=px.colors.qualitative.Bold,
        hole=0.4
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Customers: %{value}<br>Percentage: %{percent}'
    )
    
    fig.update_layout(
        title_x=0.5,
        title_font_size=18,
        autosize=True,
        legend_title='Segments',
        legend=dict(
            orientation='h', 
            yanchor='bottom', 
            y=-0.1, 
            xanchor='center', 
            x=0.5,
            font=dict(size=11),
            bgcolor='rgba(0,0,0,0)'  # Transparent background
        ),
        margin=dict(l=20, r=20, t=50, b=50)
    )
    
    return fig


def create_segment_metrics_chart(segment_profiles: pd.DataFrame) -> go.Figure:
    """
    Create a radar chart comparing key metrics across segments.
    
    Args:
        segment_profiles: DataFrame with segment profiles
        
    Returns:
        Plotly figure object
    """
    # Select metrics to display
    metrics = [
        'recency',
        'transaction_count',
        'total_spend',
        'average_transaction_value',
        'purchase_frequency',
        'customer_lifetime',
        'average_basket_size'
    ]
    
    # Normalize metrics for radar chart
    normalized_profiles = segment_profiles.copy()
    for metric in metrics:
        if metric in normalized_profiles.columns:
            max_val = normalized_profiles[metric].max()
            if max_val > 0:  # Avoid division by zero
                normalized_profiles[metric] = normalized_profiles[metric] / max_val
    
    # Create radar chart
    fig = go.Figure()
    
    for segment, profile in normalized_profiles.iterrows():
        segment_name = profile['segment_name']
        
        fig.add_trace(go.Scatterpolar(
            r=[profile[metric] for metric in metrics if metric in profile.index],
            theta=[metric.replace('_', ' ').title() for metric in metrics if metric in profile.index],
            fill='toself',
            name=segment_name
        ))
    
    fig.update_layout(
        title='Segment Comparison (Normalized Metrics)',
        title_x=0.5,
        title_font_size=18,
        autosize=True,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True,
        legend=dict(
            orientation='h', 
            yanchor='bottom', 
            y=-0.1, 
            xanchor='center', 
            x=0.5,
            font=dict(size=11),
            bgcolor='rgba(0,0,0,0)'  # Transparent background
        ),
        margin=dict(l=40, r=40, t=50, b=70)
    )
    
    return fig


def create_segment_pca_chart(pca_df: pd.DataFrame) -> go.Figure:
    """
    Create a scatter plot of PCA components colored by segment.
    
    Args:
        pca_df: DataFrame with PCA components and segment labels
        
    Returns:
        Plotly figure object
    """
    fig = px.scatter(
        pca_df,
        x='PC1',
        y='PC2',
        color='segment_name',
        title='Customer Segments (PCA)',
        color_discrete_sequence=px.colors.qualitative.Bold,
        hover_data=['segment_name']
    )
    
    fig.update_layout(
        title_x=0.5,
        title_font_size=18,
        xaxis_title='Principal Component 1',
        yaxis_title='Principal Component 2',
        legend_title='Segments',
        legend=dict(
            orientation='h', 
            yanchor='bottom', 
            y=-0.25, 
            xanchor='center', 
            x=0.5,
            font=dict(size=11),
            bgcolor='rgba(0,0,0,0)'  # Transparent background
        ),
        margin=dict(l=40, r=40, t=50, b=80),
        autosize=True
    )
    
    return fig


def create_rfm_heatmap(customer_features: pd.DataFrame, segment_column: str = 'segment_name') -> go.Figure:
    """
    Create a heatmap showing the relationship between recency, frequency, and monetary value.
    
    Args:
        customer_features: DataFrame with customer features
        segment_column: Column name containing segment labels
        
    Returns:
        Plotly figure object
    """
    # Create recency and frequency bins
    customer_features = customer_features.copy()
    customer_features['recency_bin'] = pd.qcut(customer_features['recency'], 5, labels=False)
    customer_features['frequency_bin'] = pd.qcut(
        customer_features['transaction_count'], 5, labels=False, duplicates='drop'
    )
    
    # Calculate average monetary value for each recency-frequency combination
    heatmap_data = customer_features.groupby(['recency_bin', 'frequency_bin']).agg({
        'total_spend': 'mean',
        segment_column: 'count'
    }).reset_index()
    
    # Create pivot table for heatmap
    pivot_data = heatmap_data.pivot_table(
        index='recency_bin',
        columns='frequency_bin',
        values='total_spend'
    )
    
    # Create heatmap
    fig = px.imshow(
        pivot_data,
        labels=dict(x='Frequency (Higher is Better)', y='Recency (Lower is Better)', color='Avg. Spend'),
        x=[f'F{i+1}' for i in range(pivot_data.shape[1])],
        y=[f'R{i+1}' for i in range(pivot_data.shape[0])],
        color_continuous_scale='Viridis',
        title='RFM Analysis Heatmap'
    )
    
    fig.update_layout(
        coloraxis_colorbar=dict(title='Avg. Spend')
    )
    
    return fig


def create_category_preference_chart(customer_features: pd.DataFrame, segment_column: str = 'segment_name') -> go.Figure:
    """
    Create a bar chart showing category preferences by segment.
    
    Args:
        customer_features: DataFrame with customer features
        segment_column: Column name containing segment labels
        
    Returns:
        Plotly figure object
    """
    # Get category columns (those starting with 'pct_')
    category_columns = [col for col in customer_features.columns if col.startswith('pct_')]
    
    if not category_columns:
        # If no category percentage columns, try to use primary_category
        if 'primary_category' in customer_features.columns:
            # Count customers by segment and primary category
            category_counts = customer_features.groupby([segment_column, 'primary_category']).size().reset_index(name='count')
            
            # Create bar chart
            fig = px.bar(
                category_counts,
                x=segment_column,
                y='count',
                color='primary_category',
                title='Primary Category Preference by Segment',
                barmode='group'
            )
            
            fig.update_layout(
                xaxis_title='Segment',
                yaxis_title='Number of Customers',
                legend_title='Primary Category',
                legend=dict(bgcolor='rgba(0,0,0,0)')  # Add transparent legend background
            )
            
            return fig
    
    # Calculate average category preferences by segment
    segment_categories = customer_features.groupby(segment_column)[category_columns].mean().reset_index()
    
    # Melt the dataframe for easier plotting
    melted_df = pd.melt(
        segment_categories,
        id_vars=[segment_column],
        value_vars=category_columns,
        var_name='Category',
        value_name='Percentage'
    )
    
    # Clean category names
    melted_df['Category'] = melted_df['Category'].str.replace('pct_', '').str.title()
    
    # Create bar chart
    fig = px.bar(
        melted_df,
        x=segment_column,
        y='Percentage',
        color='Category',
        title='Category Preferences by Segment',
        barmode='group'
    )
    
    fig.update_layout(
        xaxis_title='Segment',
        yaxis_title='Percentage of Spend',
        legend_title='Category',
        legend=dict(bgcolor='rgba(0,0,0,0)')  # Add transparent legend background
    )
    
    return fig


def create_spending_trend_chart(transactions_df: pd.DataFrame, segment_column: Optional[str] = None) -> go.Figure:
    """
    Create a line chart showing spending trends over time.
    
    Args:
        transactions_df: DataFrame with transaction data
        segment_column: Column name containing segment labels (optional)
        
    Returns:
        Plotly figure object
    """
    # Ensure invoice_date is datetime
    transactions_df = transactions_df.copy()
    if 'invoice_date' in transactions_df.columns:
        # Handle zero values
        transactions_df['invoice_date'] = transactions_df['invoice_date'].replace(0, np.nan)
        transactions_df['invoice_date'] = transactions_df['invoice_date'].replace('0', np.nan)
        
        # Try to parse with error handling
        try:
            transactions_df['invoice_date'] = pd.to_datetime(transactions_df['invoice_date'], errors='coerce')
        except:
            try:
                # Try with specific format
                transactions_df['invoice_date'] = pd.to_datetime(transactions_df['invoice_date'], format='%d/%m/%Y', errors='coerce')
            except:
                # If all else fails, use mixed format
                transactions_df['invoice_date'] = pd.to_datetime(transactions_df['invoice_date'], format='mixed', errors='coerce')
        
        # Fill NaT values with a default date
        if transactions_df['invoice_date'].isna().any():
            valid_dates = transactions_df['invoice_date'].dropna()
            if not valid_dates.empty:
                default_date = valid_dates.max()
            else:
                default_date = pd.Timestamp('today')
            transactions_df = transactions_df.assign(invoice_date=transactions_df['invoice_date'].fillna(default_date))
            
        transactions_df['month_year'] = transactions_df['invoice_date'].dt.to_period('M')
    else:
        return go.Figure()  # Return empty figure if no date column
    
    # Group by month and calculate total spend
    if segment_column and segment_column in transactions_df.columns:
        # Group by month and segment
        monthly_spend = transactions_df.groupby(['month_year', segment_column])['total_amount'].sum().reset_index()
        monthly_spend['month_year'] = monthly_spend['month_year'].astype(str)
        
        # Create line chart
        fig = px.line(
            monthly_spend,
            x='month_year',
            y='total_amount',
            color=segment_column,
            title='Monthly Spending Trends by Segment',
            markers=True
        )
    else:
        # Group by month only
        monthly_spend = transactions_df.groupby('month_year')['total_amount'].sum().reset_index()
        monthly_spend['month_year'] = monthly_spend['month_year'].astype(str)
        
        # Create line chart
        fig = px.line(
            monthly_spend,
            x='month_year',
            y='total_amount',
            title='Monthly Spending Trends',
            markers=True
        )
    
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Total Spend',
        xaxis=dict(tickangle=45),
        legend=dict(bgcolor='rgba(0,0,0,0)')  # Add transparent legend background
    )
    
    return fig


def create_payment_method_chart(transactions_df: pd.DataFrame, segment_column: Optional[str] = None) -> go.Figure:
    """
    Create a chart showing payment method preferences.
    
    Args:
        transactions_df: DataFrame with transaction data
        segment_column: Column name containing segment labels (optional)
        
    Returns:
        Plotly figure object
    """
    if 'payment_method' not in transactions_df.columns:
        return go.Figure()  # Return empty figure if no payment method column
    
    transactions_df = transactions_df.copy()
    
    if segment_column and segment_column in transactions_df.columns:
        # Count transactions by payment method and segment
        payment_counts = transactions_df.groupby([segment_column, 'payment_method']).size().reset_index(name='count')
        
        # Create bar chart
        fig = px.bar(
            payment_counts,
            x=segment_column,
            y='count',
            color='payment_method',
            title='Payment Method Preferences by Segment',
            barmode='group'
        )
        
        fig.update_layout(
            xaxis_title='Segment',
            yaxis_title='Number of Transactions',
            legend_title='Payment Method',
            legend=dict(bgcolor='rgba(0,0,0,0)')  # Add transparent legend background
        )
    else:
        # Count transactions by payment method
        payment_counts = transactions_df['payment_method'].value_counts().reset_index()
        payment_counts.columns = ['payment_method', 'count']
        
        # Create pie chart
        fig = px.pie(
            payment_counts,
            values='count',
            names='payment_method',
            title='Payment Method Distribution',
            hole=0.4
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label'
        )
    
    return fig


def create_mall_distribution_chart(transactions_df: pd.DataFrame, segment_column: Optional[str] = None) -> go.Figure:
    """
    Create a chart showing distribution of transactions across shopping malls.
    
    Args:
        transactions_df: DataFrame with transaction data
        segment_column: Column name containing segment labels (optional)
        
    Returns:
        Plotly figure object
    """
    if 'shopping_mall' not in transactions_df.columns:
        return go.Figure()  # Return empty figure if no shopping mall column
    
    transactions_df = transactions_df.copy()
    
    if segment_column and segment_column in transactions_df.columns:
        # Count transactions by mall and segment
        mall_counts = transactions_df.groupby([segment_column, 'shopping_mall']).size().reset_index(name='count')
        
        # Create bar chart
        fig = px.bar(
            mall_counts,
            x=segment_column,
            y='count',
            color='shopping_mall',
            title='Shopping Mall Preferences by Segment',
            barmode='group'
        )
        
        fig.update_layout(
            xaxis_title='Segment',
            yaxis_title='Number of Transactions',
            legend_title='Shopping Mall',
            legend=dict(bgcolor='rgba(0,0,0,0)')  # Add transparent legend background
        )
    else:
        # Count transactions by mall
        mall_counts = transactions_df['shopping_mall'].value_counts().reset_index()
        mall_counts.columns = ['shopping_mall', 'count']
        
        # Create bar chart
        fig = px.bar(
            mall_counts,
            x='shopping_mall',
            y='count',
            title='Transaction Distribution by Shopping Mall',
            color='shopping_mall'
        )
        
        fig.update_layout(
            xaxis_title='Shopping Mall',
            yaxis_title='Number of Transactions',
            showlegend=False
        )
    
    return fig


def create_age_distribution_chart(customer_features: pd.DataFrame, segment_column: str = 'segment_name') -> go.Figure:
    """
    Create a histogram showing age distribution by segment.
    
    Args:
        customer_features: DataFrame with customer features
        segment_column: Column name containing segment labels
        
    Returns:
        Plotly figure object
    """
    if 'age' not in customer_features.columns:
        return go.Figure()  # Return empty figure if no age column
    
    # Create histogram
    fig = px.histogram(
        customer_features,
        x='age',
        color=segment_column,
        title='Age Distribution by Segment',
        barmode='overlay',
        opacity=0.7,
        nbins=20
    )
    
    fig.update_layout(
        xaxis_title='Age',
        yaxis_title='Number of Customers',
        legend_title='Segment',
        legend=dict(bgcolor='rgba(0,0,0,0)')  # Add transparent legend background
    )
    
    return fig


def create_city_distribution_chart(customer_features: pd.DataFrame, segment_column: str = 'segment_name') -> go.Figure:
    """
    Create a chart showing distribution of customers across cities.
    
    Args:
        customer_features: DataFrame with customer features
        segment_column: Column name containing segment labels
        
    Returns:
        Plotly figure object
    """
    # Check if city data is available
    city_columns = [col for col in customer_features.columns if col.startswith('city_')]
    
    # Create a new DataFrame for city data to avoid modifying the original
    city_df = pd.DataFrame(index=customer_features.index)
    
    # Add segment information
    if segment_column in customer_features.columns:
        city_df[segment_column] = customer_features[segment_column].values
    else:
        city_df[segment_column] = 'Unknown'
    
    # If we have the one-hot encoded city columns
    if len(city_columns) > 0:
        # Set default city value
        city_df['city'] = 'Unknown'
        
        # Process each customer row and assign city based on one-hot encoded columns
        for idx, row in customer_features.iterrows():
            for city_col in city_columns:
                if row.get(city_col) == 1:
                    city_name = city_col.replace('city_', '')
                    city_df.at[idx, 'city'] = city_name
    
    # If we have a direct city column
    elif 'city' in customer_features.columns:
        city_df['city'] = customer_features['city'].fillna('Unknown').values
    
    # If no city data is available, create a message
    else:
        # Create an empty figure
        fig = go.Figure()
        fig.add_annotation(
            text="No city data available",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        fig.update_layout(
            title='Customer Distribution by City and Segment',
            xaxis_title='City',
            yaxis_title='Number of Customers'
        )
        return fig
    
    # Count customers by city and segment
    city_counts = city_df.groupby([segment_column, 'city']).size().reset_index(name='count')
    
    # Remove 'Unknown' city if it exists and there are other cities
    if 'Unknown' in city_counts['city'].values and len(city_counts['city'].unique()) > 1:
        city_counts = city_counts[city_counts['city'] != 'Unknown']
    
    # Sort by count for better visualization
    city_counts = city_counts.sort_values(['city', 'count'], ascending=[True, False])
    
    # Create bar chart
    fig = px.bar(
        city_counts,
        x='city',
        y='count',
        color=segment_column,
        title='Customer Distribution by City and Segment',
        barmode='group'
    )
    
    fig.update_layout(
        xaxis_title='City',
        yaxis_title='Number of Customers',
        legend_title='Segment',
        legend=dict(bgcolor='rgba(0,0,0,0)')  # Add transparent legend background
    )
    
    return fig


def create_dashboard_metrics(customer_features: pd.DataFrame, transactions_df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate key metrics for the dashboard.
    
    Args:
        customer_features: DataFrame with customer features
        transactions_df: DataFrame with transaction data
        
    Returns:
        Dictionary with key metrics
    """
    metrics = {}
    
    # Customer metrics
    metrics['total_customers'] = len(customer_features)
    
    if 'transaction_count' in customer_features.columns:
        metrics['avg_transactions_per_customer'] = customer_features['transaction_count'].mean()
    
    if 'total_spend' in customer_features.columns:
        metrics['avg_customer_lifetime_value'] = customer_features['total_spend'].mean()
    
    if 'average_transaction_value' in customer_features.columns:
        metrics['avg_transaction_value'] = customer_features['average_transaction_value'].mean()
    
    # Transaction metrics
    metrics['total_transactions'] = len(transactions_df)
    
    if 'total_amount' in transactions_df.columns:
        metrics['total_revenue'] = transactions_df['total_amount'].sum()
    
    if 'quantity' in transactions_df.columns:
        metrics['total_items_sold'] = transactions_df['quantity'].sum()
    
    # Calculate retention rate (if date information is available)
    if 'invoice_date' in transactions_df.columns:
        transactions_df = transactions_df.copy()
        
        # Handle zero values
        transactions_df['invoice_date'] = transactions_df['invoice_date'].replace(0, np.nan)
        transactions_df['invoice_date'] = transactions_df['invoice_date'].replace('0', np.nan)
        
        # Try to parse with error handling
        try:
            transactions_df['invoice_date'] = pd.to_datetime(transactions_df['invoice_date'], errors='coerce')
        except:
            try:
                # Try with specific format
                transactions_df['invoice_date'] = pd.to_datetime(transactions_df['invoice_date'], format='%d/%m/%Y', errors='coerce')
            except:
                # If all else fails, use mixed format
                transactions_df['invoice_date'] = pd.to_datetime(transactions_df['invoice_date'], format='mixed', errors='coerce')
        
        # Drop rows with invalid dates for this calculation
        transactions_df = transactions_df.dropna(subset=['invoice_date'])
        
        if not transactions_df.empty:
            # Get the date range
            min_date = transactions_df['invoice_date'].min()
            max_date = transactions_df['invoice_date'].max()
            
            # Calculate months between min and max date
            months_diff = (max_date.year - min_date.year) * 12 + max_date.month - min_date.month
            
            if months_diff > 0:
                # Count customers who made purchases in the first and last month
                first_month_customers = transactions_df[
                    (transactions_df['invoice_date'].dt.year == min_date.year) &
                    (transactions_df['invoice_date'].dt.month == min_date.month)
                ]['customer_id'].nunique()
                
                last_month_customers = transactions_df[
                    (transactions_df['invoice_date'].dt.year == max_date.year) &
                    (transactions_df['invoice_date'].dt.month == max_date.month)
                ]['customer_id'].nunique()
                
                # Calculate retention rate
                if first_month_customers > 0:
                    metrics['customer_retention_rate'] = last_month_customers / first_month_customers
    
    return metrics


def create_customer_location_map(customer_data):
    """
    Create a map showing the geographic distribution of customers.
    
    Args:
        customer_data: DataFrame with customer data including locations
        
    Returns:
        Plotly figure object
    """
    # Create a copy to avoid modifying the original dataframe
    map_data = pd.DataFrame()
    
    # Check if latitude and longitude columns exist
    has_coords = ('latitude' in customer_data.columns and 'longitude' in customer_data.columns)
    
    # Check if we have city columns that can be used for geocoding
    city_columns = [col for col in customer_data.columns if col.startswith('city_')]
    has_city_data = len(city_columns) > 0 or 'city' in customer_data.columns
    
    # If real coordinates are not available, create a representation based on cities
    if not has_coords:
        # Create customer IDs
        if 'customer_id' in customer_data.columns:
            map_data['customer_id'] = customer_data.index
        else:
            map_data['customer_id'] = [f"CUST{i}" for i in range(len(customer_data))]
        
        # Add segment information if available
        if 'segment_name' in customer_data.columns:
            map_data['segment_name'] = customer_data['segment_name'].values
        else:
            map_data['segment_name'] = 'All Customers'
        
        # Create city data based on available information
        map_data['city'] = 'Unknown'  # Default value
        
        if len(city_columns) > 0:
            # Process each customer row and assign city based on one-hot encoded columns
            for idx, row in customer_data.iterrows():
                for city_col in city_columns:
                    if row.get(city_col) == 1:
                        city_name = city_col.replace('city_', '')
                        # Use iloc to set the value for the corresponding row in map_data
                        map_data.loc[map_data['customer_id'] == idx, 'city'] = city_name
        elif 'city' in customer_data.columns:
            map_data['city'] = customer_data['city'].values
            
        # Create predefined coordinates for each city in Andhra Pradesh
        city_coords = {
            # Kadapa District Cities (Andhra Pradesh)
            'Proddatur': {'lat': 14.7502, 'lon': 78.5482},
            'Kadapa': {'lat': 14.4673, 'lon': 78.8242},
            'Jammalamadugu': {'lat': 14.8498, 'lon': 78.3871},
            'Kamalapuram': {'lat': 14.5979, 'lon': 78.6702},
            'Yerraguntla': {'lat': 14.6327, 'lon': 78.5456},
            'Mydukur': {'lat': 14.5216, 'lon': 78.7961},
            'Pulivendla': {'lat': 14.4263, 'lon': 78.2258},
            'Rajampet': {'lat': 14.1896, 'lon': 79.1634},
            'Badvel': {'lat': 14.7430, 'lon': 79.0650},
            'Rayachoti': {'lat': 14.0522, 'lon': 78.7506},
            
            # Other major cities in Andhra Pradesh (as fallbacks)
            'Hyderabad': {'lat': 17.3850, 'lon': 78.4867},
            'Vijayawada': {'lat': 16.5062, 'lon': 80.6480},
            'Visakhapatnam': {'lat': 17.6868, 'lon': 83.2185},
            'Unknown': {'lat': 14.4673, 'lon': 78.8242}  # Default to Kadapa (district center)
        }
        
        # Add small random variation to prevent perfect overlapping of points
        np.random.seed(42)  # For reproducibility
        
        # Create lat/lon columns based on city
        map_data['latitude'] = map_data['city'].apply(
            lambda c: city_coords.get(c, city_coords['Unknown'])['lat'] + np.random.normal(0, 0.01)
        )
        map_data['longitude'] = map_data['city'].apply(
            lambda c: city_coords.get(c, city_coords['Unknown'])['lon'] + np.random.normal(0, 0.01)
        )
    else:
        # Use real coordinates
        map_data = pd.DataFrame({
            'customer_id': customer_data.index,
            'latitude': customer_data['latitude'].values,
            'longitude': customer_data['longitude'].values
        })
        
        if 'segment_name' in customer_data.columns:
            map_data['segment_name'] = customer_data['segment_name'].values
        else:
            map_data['segment_name'] = 'All Customers'
    
    # Create the map
    fig = px.scatter_mapbox(
        map_data,
        lat='latitude',
        lon='longitude',
        color='segment_name',
        hover_name='customer_id',
        zoom=9,  # Adjusted zoom level for better visibility of Kadapa district
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    
    fig.update_layout(
        title='Customer Geographic Distribution',
        title_x=0.5,
        title_font_size=18,
        mapbox_style='open-street-map',
        legend_title='Segments',
        legend=dict(
            orientation='h', 
            yanchor='bottom', 
            y=0.01, 
            xanchor='center', 
            x=0.5,
            font=dict(size=11),
            bgcolor='rgba(0,0,0,0)'  # Transparent background
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        autosize=True
    )
    
    return fig 