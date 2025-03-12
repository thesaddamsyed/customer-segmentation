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
        legend_title='Segments',
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5)
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
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        title='Segment Comparison (Normalized Metrics)',
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5)
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
        xaxis_title='Principal Component 1',
        yaxis_title='Principal Component 2',
        legend_title='Segments'
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
                legend_title='Primary Category'
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
        legend_title='Category'
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
        transactions_df['invoice_date'] = pd.to_datetime(transactions_df['invoice_date'])
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
        xaxis=dict(tickangle=45)
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
            legend_title='Payment Method'
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
            legend_title='Shopping Mall'
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
        legend_title='Segment'
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
    if 'city' not in customer_features.columns:
        return go.Figure()  # Return empty figure if no city column
    
    # Count customers by city and segment
    city_counts = customer_features.groupby([segment_column, 'city']).size().reset_index(name='count')
    
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
        legend_title='Segment'
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
        transactions_df['invoice_date'] = pd.to_datetime(transactions_df['invoice_date'])
        
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
    Creates a visualization showing customer distribution by country or city.
    
    Args:
        customer_data: DataFrame with customer data including location information
        
    Returns:
        Plotly figure object
    """
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Dictionary of Indian cities with their coordinates
    city_coordinates = {
        'Hyderabad': {'lat': 17.3850, 'lon': 78.4867},
        'Vijayawada': {'lat': 16.5062, 'lon': 80.6480},
        'Visakhapatnam': {'lat': 17.6868, 'lon': 83.2185},
        'Bangalore': {'lat': 12.9716, 'lon': 77.5946},
        'Mumbai': {'lat': 19.0760, 'lon': 72.8777},
        'Delhi': {'lat': 28.6139, 'lon': 77.2090},
        'Chennai': {'lat': 13.0827, 'lon': 80.2707},
        'Kolkata': {'lat': 22.5726, 'lon': 88.3639},
        'Pune': {'lat': 18.5204, 'lon': 73.8567},
        'Ahmedabad': {'lat': 23.0225, 'lon': 72.5714},
        'Jaipur': {'lat': 26.9124, 'lon': 75.7873},
        'Lucknow': {'lat': 26.8467, 'lon': 80.9462},
        'Kochi': {'lat': 9.9312, 'lon': 76.2673},
        'Guwahati': {'lat': 26.1445, 'lon': 91.7362},
        'Bhubaneswar': {'lat': 20.2961, 'lon': 85.8245},
        'Chandigarh': {'lat': 30.7333, 'lon': 76.7794},
        'Coimbatore': {'lat': 11.0168, 'lon': 76.9558},
        'Indore': {'lat': 22.7196, 'lon': 75.8577},
        'Nagpur': {'lat': 21.1458, 'lon': 79.0882},
        'Patna': {'lat': 25.5941, 'lon': 85.1376},
        'Surat': {'lat': 21.1702, 'lon': 72.8311},
        'Thiruvananthapuram': {'lat': 8.5241, 'lon': 76.9366},
        'Vadodara': {'lat': 22.3072, 'lon': 73.1812}
    }
    
    # Clean and prepare city data
    customer_data = customer_data.copy()
    
    # Check for one-hot encoded city columns and create city column if needed
    city_columns = [col for col in customer_data.columns if col.startswith('city_')]
    if city_columns and 'city' not in customer_data.columns:
        # Create a new city column
        customer_data['city'] = 'Unknown'
        
        # For each city column, set the city name for rows where the column value is 1
        for city_col in city_columns:
            city_name = city_col.replace('city_', '')
            customer_data.loc[customer_data[city_col] == 1, 'city'] = city_name
    
    # If we have city data
    if 'city' in customer_data.columns:
        # Convert city column to string and handle NaN values
        customer_data['city'] = customer_data['city'].fillna('Unknown')
        customer_data['city'] = customer_data['city'].astype(str)
        
        # Filter out empty city values
        customer_data = customer_data[customer_data['city'].str.strip() != '']
        customer_data = customer_data[customer_data['city'] != 'Unknown']
        
        # Check if we have any valid city data
        if len(customer_data) == 0 or customer_data['city'].nunique() == 0:
            # Create an empty figure with a message
            fig = go.Figure()
            fig.add_annotation(
                text="No valid city data available for mapping",
                showarrow=False,
                font=dict(size=14)
            )
            fig.update_layout(
                title="No City Data Available",
                height=400
            )
            return fig
            
        # Count customers by city
        city_counts = customer_data['city'].value_counts().reset_index()
        city_counts.columns = ['city', 'customer_count']
        
        # Sort by customer count in descending order
        city_counts = city_counts.sort_values('customer_count', ascending=False)
        
        # Add latitude and longitude to city counts
        city_counts['lat'] = city_counts['city'].apply(lambda x: city_coordinates.get(x, {}).get('lat', None))
        city_counts['lon'] = city_counts['city'].apply(lambda x: city_coordinates.get(x, {}).get('lon', None))
        
        # Filter out cities without coordinates
        map_data = city_counts.dropna(subset=['lat', 'lon'])
        
        # If we have segment data, create a more comprehensive visualization with map
        if 'segment_name' in customer_data.columns:
            # Create a figure with subplots: map and bar chart
            fig = make_subplots(
                rows=2, cols=1,
                specs=[[{"type": "scattergeo"}], [{"type": "bar"}]],
                row_heights=[0.7, 0.3],
                subplot_titles=["Geographic Distribution in India", "City Distribution"]
            )
            
            # Add scatter geo map for geographic distribution
            if not map_data.empty:
                # Get segment data for each city
                segment_city_data = []
                for city in map_data['city']:
                    city_customers = customer_data[customer_data['city'] == city]
                    segment_counts = city_customers['segment_name'].value_counts().to_dict()
                    city_info = map_data[map_data['city'] == city].iloc[0].to_dict()
                    city_info.update(segment_counts)
                    segment_city_data.append(city_info)
                
                # Create hover text with segment information
                hover_texts = []
                for city_info in segment_city_data:
                    city_name = city_info['city']
                    total_customers = city_info['customer_count']
                    hover_text = f"<b>{city_name}</b><br>Total Customers: {total_customers}<br>"
                    
                    # Add segment breakdown
                    for key, value in city_info.items():
                        if key not in ['city', 'customer_count', 'lat', 'lon'] and isinstance(value, (int, float)):
                            hover_text += f"{key}: {value} customers<br>"
                    
                    hover_texts.append(hover_text)
                
                # Add scatter geo trace
                fig.add_trace(
                    go.Scattergeo(
                        lon=map_data['lon'],
                        lat=map_data['lat'],
                        text=hover_texts,
                        mode='markers',
                        marker=dict(
                            size=map_data['customer_count'],
                            sizemode='area',
                            sizeref=2.*max(map_data['customer_count'])/(40.**2),
                            sizemin=4,
                            color=map_data['customer_count'],
                            colorscale='Viridis',
                            showscale=True,
                            colorbar=dict(
                                title="Customers",
                                x=0.95
                            )
                        ),
                        hoverinfo='text',
                        name='Customer Distribution'
                    ),
                    row=1, col=1
                )
                
                # Add text labels for cities with customers
                fig.add_trace(
                    go.Scattergeo(
                        lon=map_data['lon'],
                        lat=map_data['lat'],
                        text=map_data['city'],
                        mode='text',
                        textfont=dict(
                            color='black',
                            size=10,
                            family='Arial, bold'
                        ),
                        textposition='top center',
                        hoverinfo='none',
                        name='City Labels'
                    ),
                    row=1, col=1
                )
                
                # Add all major Indian cities as reference points (even those without customers)
                major_cities = []
                for city, coords in city_coordinates.items():
                    # Skip cities that are already in map_data to avoid duplication
                    if city not in map_data['city'].values:
                        major_cities.append({
                            'city': city,
                            'lat': coords['lat'],
                            'lon': coords['lon']
                        })
                
                if major_cities:
                    major_cities_df = pd.DataFrame(major_cities)
                    fig.add_trace(
                        go.Scattergeo(
                            lon=major_cities_df['lon'],
                            lat=major_cities_df['lat'],
                            text=major_cities_df['city'],
                            mode='markers+text',
                            marker=dict(
                                size=5,
                                color='gray',
                                symbol='circle'
                            ),
                            textfont=dict(
                                color='gray',
                                size=8,
                                family='Arial'
                            ),
                            textposition='top center',
                            hovertemplate='<b>%{text}</b><br>No customers<extra></extra>',
                            name='Other Major Cities'
                        ),
                        row=1, col=1
                    )
                
                # Update geo layout - Focus specifically on India
                fig.update_geos(
                    visible=True,
                    resolution=50,
                    scope="asia",
                    showcountries=True,
                    countrycolor="Black",
                    showsubunits=True,
                    subunitcolor="Blue",
                    subunitwidth=1,
                    showcoastlines=True,
                    coastlinecolor="Black",
                    coastlinewidth=1,
                    showland=True,
                    landcolor="LightGreen",
                    showocean=True,
                    oceancolor="LightBlue",
                    showrivers=True,
                    rivercolor="Blue",
                    riverwidth=1,
                    lakecolor="Blue",
                    showlakes=True,
                    showframe=True,
                    framecolor="Gray",
                    framewidth=1,
                    bgcolor='rgba(255, 255, 255, 0.8)',
                    center=dict(lon=78.9629, lat=20.5937),  # Center on India
                    projection_scale=5,  # Zoom level
                    lonaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(0, 0, 0, 0.2)',
                        gridwidth=0.5
                    ),
                    lataxis=dict(
                        showgrid=True,
                        gridcolor='rgba(0, 0, 0, 0.2)',
                        gridwidth=0.5
                    )
                )
            
            # Add bar chart for city distribution
            segment_city_counts = customer_data.groupby(['city', 'segment_name']).size().reset_index(name='customer_count')
            
            # Get unique segments for consistent colors
            segments = customer_data['segment_name'].unique()
            
            # Add traces for each segment
            for segment in segments:
                segment_data = segment_city_counts[segment_city_counts['segment_name'] == segment]
                fig.add_trace(
                    go.Bar(
                        x=segment_data['city'],
                        y=segment_data['customer_count'],
                        name=segment,
                        hovertemplate='<b>%{x}</b><br>Segment: ' + segment + '<br>Customers: %{y}<extra></extra>'
                    ),
                    row=2, col=1
                )
            
            # Update layout
            fig.update_layout(
                title_text=f'Customer Geographic Distribution in India (Total: {len(customer_data)} customers)',
                barmode='stack',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.1,
                    xanchor="center",
                    x=0.5
                ),
                height=700,
                margin=dict(l=0, r=0, t=50, b=0)
            )
            
            fig.update_xaxes(title_text="City", tickangle=45, row=2, col=1)
            fig.update_yaxes(title_text="Number of Customers", row=2, col=1)
            
            return fig
        else:
            # Create a figure with map and bar chart
            fig = make_subplots(
                rows=2, cols=1,
                specs=[[{"type": "scattergeo"}], [{"type": "bar"}]],
                row_heights=[0.7, 0.3],
                subplot_titles=["Geographic Distribution in India", "City Distribution"]
            )
            
            # Add scatter geo map for geographic distribution
            if not map_data.empty:
                # Create hover text
                hover_texts = [f"<b>{city}</b><br>Customers: {count}" 
                              for city, count in zip(map_data['city'], map_data['customer_count'])]
                
                # Add scatter geo trace
                fig.add_trace(
                    go.Scattergeo(
                        lon=map_data['lon'],
                        lat=map_data['lat'],
                        text=hover_texts,
                        mode='markers',
                        marker=dict(
                            size=map_data['customer_count'],
                            sizemode='area',
                            sizeref=2.*max(map_data['customer_count'])/(40.**2),
                            sizemin=4,
                            color=map_data['customer_count'],
                            colorscale='Viridis',
                            showscale=True,
                            colorbar=dict(
                                title="Customers",
                                x=0.95
                            )
                        ),
                        hoverinfo='text'
                    ),
                    row=1, col=1
                )
                
                # Add text labels for cities with customers
                fig.add_trace(
                    go.Scattergeo(
                        lon=map_data['lon'],
                        lat=map_data['lat'],
                        text=map_data['city'],
                        mode='text',
                        textfont=dict(
                            color='black',
                            size=10,
                            family='Arial, bold'
                        ),
                        textposition='top center',
                        hoverinfo='none',
                        name='City Labels'
                    ),
                    row=1, col=1
                )
                
                # Add all major Indian cities as reference points (even those without customers)
                major_cities = []
                for city, coords in city_coordinates.items():
                    # Skip cities that are already in map_data to avoid duplication
                    if city not in map_data['city'].values:
                        major_cities.append({
                            'city': city,
                            'lat': coords['lat'],
                            'lon': coords['lon']
                        })
                
                if major_cities:
                    major_cities_df = pd.DataFrame(major_cities)
                    fig.add_trace(
                        go.Scattergeo(
                            lon=major_cities_df['lon'],
                            lat=major_cities_df['lat'],
                            text=major_cities_df['city'],
                            mode='markers+text',
                            marker=dict(
                                size=5,
                                color='gray',
                                symbol='circle'
                            ),
                            textfont=dict(
                                color='gray',
                                size=8,
                                family='Arial'
                            ),
                            textposition='top center',
                            hovertemplate='<b>%{text}</b><br>No customers<extra></extra>',
                            name='Other Major Cities'
                        ),
                        row=1, col=1
                    )
                
                # Update geo layout - Focus specifically on India
                fig.update_geos(
                    visible=True,
                    resolution=50,
                    scope="asia",
                    showcountries=True,
                    countrycolor="Black",
                    showsubunits=True,
                    subunitcolor="Blue",
                    subunitwidth=1,
                    showcoastlines=True,
                    coastlinecolor="Black",
                    coastlinewidth=1,
                    showland=True,
                    landcolor="LightGreen",
                    showocean=True,
                    oceancolor="LightBlue",
                    showrivers=True,
                    rivercolor="Blue",
                    riverwidth=1,
                    lakecolor="Blue",
                    showlakes=True,
                    showframe=True,
                    framecolor="Gray",
                    framewidth=1,
                    bgcolor='rgba(255, 255, 255, 0.8)',
                    center=dict(lon=78.9629, lat=20.5937),  # Center on India
                    projection_scale=5,  # Zoom level
                    lonaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(0, 0, 0, 0.2)',
                        gridwidth=0.5
                    ),
                    lataxis=dict(
                        showgrid=True,
                        gridcolor='rgba(0, 0, 0, 0.2)',
                        gridwidth=0.5
                    )
                )
            
            # Add bar chart for city distribution
            fig.add_trace(
                go.Bar(
                    x=city_counts['city'],
                    y=city_counts['customer_count'],
                    marker_color='purple',
                    hovertemplate='<b>%{x}</b><br>Customers: %{y}<extra></extra>'
                ),
                row=2, col=1
            )
            
            # Update layout
            fig.update_layout(
                title_text=f'Customer Geographic Distribution in India (Total: {len(customer_data)} customers)',
                height=700,
                margin=dict(l=0, r=0, t=50, b=0)
            )
            
            fig.update_xaxes(title_text="City", tickangle=45, row=2, col=1)
            fig.update_yaxes(title_text="Number of Customers", row=2, col=1)
            
            return fig
    
    # If we don't have location data
    else:
        # Create an empty figure with a message
        fig = go.Figure()
        fig.add_annotation(
            text="No city data available for mapping. Please ensure city data is properly loaded.",
            showarrow=False,
            font=dict(size=14)
        )
        fig.update_layout(
            title="No Location Data Available",
            height=400
        )
        return fig 