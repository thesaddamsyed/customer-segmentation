"""
Data loader module for loading and preprocessing customer data.
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, Optional


def load_data(file_path: str) -> pd.DataFrame:
    """
    Load data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        DataFrame containing the data
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    return pd.read_csv(file_path)


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess raw transaction data.
    
    Args:
        df: Raw customer data
        
    Returns:
        Preprocessed customer data
    """
    # Create a copy to avoid modifying the original dataframe
    processed_df = df.copy()
    
    # Convert invoice_date to datetime - handle multiple possible date formats
    if 'invoice_date' in processed_df.columns:
        # Replace any zeros with NaT
        processed_df['invoice_date'] = processed_df['invoice_date'].replace(0, np.nan)
        processed_df['invoice_date'] = processed_df['invoice_date'].replace('0', np.nan)
        
        # Try multiple formats with error handling
        try:
            # Try default format (original dataset format)
            processed_df['invoice_date'] = pd.to_datetime(processed_df['invoice_date'], errors='coerce')
        except:
            try:
                # Try dd/mm/yyyy format (our new dataset format)
                processed_df['invoice_date'] = pd.to_datetime(processed_df['invoice_date'], format='%d/%m/%Y', errors='coerce')
            except:
                # If all else fails, use a more flexible approach
                processed_df['invoice_date'] = pd.to_datetime(processed_df['invoice_date'], format='mixed', errors='coerce')
    
        # Handle any remaining NaT values by setting them to a default date
        default_date = processed_df['invoice_date'].dropna().max() if not processed_df['invoice_date'].dropna().empty else pd.Timestamp('today')
        processed_df = processed_df.assign(invoice_date=processed_df['invoice_date'].fillna(default_date))
        
        # Extract year and month from invoice_date
        processed_df['year'] = processed_df['invoice_date'].dt.year
        processed_df['month'] = processed_df['invoice_date'].dt.month
        
        # Calculate days since last purchase (using the max date in the dataset as reference)
        max_date = processed_df['invoice_date'].max()
        processed_df['days_since_last_purchase'] = (max_date - processed_df['invoice_date']).dt.days
    
    # Handle missing values
    processed_df.fillna({
        'discount': 0,
        'quantity': 0,
        'price': 0,
        'total_amount': 0
    }, inplace=True)
    
    # Ensure email addresses are lowercase for consistency
    if 'email' in processed_df.columns:
        processed_df['email'] = processed_df['email'].str.lower()
    
    return processed_df


def create_customer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create customer-level features for segmentation.
    
    Args:
        df: Preprocessed transaction data
        
    Returns:
        DataFrame with customer-level features
    """
    # Group by customer_id and calculate aggregated features
    customer_features = df.groupby('customer_id').agg({
        'invoice_no': 'count',
        'total_amount': ['sum', 'mean', 'max'],
        'quantity': ['sum', 'mean'],
        'discount': ['mean'],
        'days_since_last_purchase': 'min',
        'invoice_date': ['min', 'max']
    })
    
    # Flatten the column hierarchy
    customer_features.columns = ['_'.join(col).strip() for col in customer_features.columns.values]
    
    # Rename columns for clarity
    customer_features.rename(columns={
        'invoice_no_count': 'transaction_count',
        'total_amount_sum': 'total_spend',
        'total_amount_mean': 'average_transaction_value',
        'total_amount_max': 'max_transaction_value',
        'quantity_sum': 'total_items_purchased',
        'quantity_mean': 'average_basket_size',
        'discount_mean': 'average_discount',
        'days_since_last_purchase_min': 'recency',
        'invoice_date_min': 'first_purchase_date',
        'invoice_date_max': 'last_purchase_date'
    }, inplace=True)
    
    # Calculate customer lifetime (days between first and last purchase)
    customer_features['customer_lifetime'] = (
        customer_features['last_purchase_date'] - customer_features['first_purchase_date']
    ).dt.days
    
    # Calculate purchase frequency (transactions per month)
    customer_features['purchase_frequency'] = customer_features['transaction_count'] / (
        customer_features['customer_lifetime'] / 30 + 1  # Add 1 to avoid division by zero
    )
    
    # Add category preferences
    category_preferences = get_category_preferences(df)
    customer_features = customer_features.join(category_preferences)
    
    # Add customer profile information
    customer_profile = get_customer_profile(df)
    customer_features = customer_features.join(customer_profile)
    
    return customer_features


def get_category_preferences(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate category preferences for each customer.
    
    Args:
        df: Preprocessed transaction data
        
    Returns:
        DataFrame with category preference features
    """
    # Get total spend by customer and category
    category_spend = df.groupby(['customer_id', 'category'])['total_amount'].sum().unstack(fill_value=0)
    
    # Rename columns to indicate they are category spends
    category_spend.columns = [f'spend_{col.lower().replace(" & ", "_")}' for col in category_spend.columns]
    
    # Calculate percentage of spend in each category
    total_spend = category_spend.sum(axis=1)
    category_pct = category_spend.div(total_spend, axis=0) * 100
    
    # Rename columns to indicate they are percentages
    category_pct.columns = [f'pct_{col.split("_", 1)[1]}' for col in category_pct.columns]
    
    # Combine spend and percentage features
    category_features = pd.concat([category_spend, category_pct], axis=1)
    
    # Determine primary category (category with highest spend)
    primary_category = category_spend.idxmax(axis=1)
    primary_category = primary_category.str.replace('spend_', '')
    primary_category = pd.DataFrame(primary_category, columns=['primary_category'])
    
    return pd.concat([category_features, primary_category], axis=1)


def get_customer_profile(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract customer profile information.
    
    Args:
        df: Preprocessed transaction data
        
    Returns:
        DataFrame with customer profile features
    """
    # Get the most recent profile information for each customer
    latest_transactions = df.sort_values('invoice_date').groupby('customer_id').last()
    
    # Extract relevant profile columns
    profile_columns = ['email', 'gender', 'age', 'city']
    customer_profile = latest_transactions[profile_columns]
    
    # Create dummy variables for categorical features
    city_dummies = pd.get_dummies(customer_profile['city'], prefix='city')
    gender_dummies = pd.get_dummies(customer_profile['gender'], prefix='gender')
    
    # Combine all profile features
    profile_features = pd.concat([
        customer_profile[['email', 'age']],
        city_dummies,
        gender_dummies
    ], axis=1)
    
    return profile_features


def split_data(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into training and testing sets.
    
    Args:
        df: DataFrame to split
        test_size: Proportion of data to use for testing
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (train_df, test_df)
    """
    from sklearn.model_selection import train_test_split
    
    # Get unique customer IDs
    customer_ids = df['customer_id'].unique()
    
    # Split customer IDs into train and test sets
    train_ids, test_ids = train_test_split(
        customer_ids, test_size=test_size, random_state=random_state
    )
    
    # Filter dataframe based on customer IDs
    train_df = df[df['customer_id'].isin(train_ids)]
    test_df = df[df['customer_id'].isin(test_ids)]
    
    return train_df, test_df


def save_processed_data(df: pd.DataFrame, file_path: str) -> None:
    """
    Save processed data to a CSV file.
    
    Args:
        df: DataFrame to save
        file_path: Path to save the CSV file
    """
    df.to_csv(file_path, index=True)
    print(f"Data saved to {file_path}")


def load_and_process(file_path: str, output_path: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load, preprocess, and create customer features from raw data.
    
    Args:
        file_path: Path to the raw data CSV file
        output_path: Path to save the processed customer features (optional)
        
    Returns:
        Tuple of (processed_transactions, customer_features)
    """
    # Load raw data
    raw_data = load_data(file_path)
    
    # Preprocess transaction data
    processed_transactions = preprocess_data(raw_data)
    
    # Create customer features
    customer_features = create_customer_features(processed_transactions)
    
    # Save processed data if output path is provided
    if output_path:
        save_processed_data(customer_features, output_path)
    
    return processed_transactions, customer_features 