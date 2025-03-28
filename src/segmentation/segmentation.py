"""
Customer segmentation module for segmenting customers based on their features.
"""
import os
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import joblib


class CustomerSegmentation:
    """
    Class for segmenting customers based on their features.
    """
    
    def __init__(self, n_segments: int = 5, random_state: int = 42):
        """
        Initialize the CustomerSegmentation class.
        
        Args:
            n_segments: Number of segments to create
            random_state: Random seed for reproducibility
        """
        self.n_segments = n_segments
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=n_segments, random_state=random_state, n_init=10)
        self.pca = PCA(n_components=2)
        self.feature_columns = None
        self.segment_profiles = None
        
    def preprocess_features(self, df: pd.DataFrame, feature_columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Preprocess features for segmentation.
        
        Args:
            df: DataFrame with customer features
            feature_columns: List of columns to use for segmentation (optional)
            
        Returns:
            DataFrame with preprocessed features
        """
        # If feature columns are not provided, use default RFM features
        if feature_columns is None:
            feature_columns = [
                'recency',
                'transaction_count',
                'total_spend',
                'average_transaction_value',
                'purchase_frequency',
                'customer_lifetime',
                'average_basket_size'
            ]
        
        self.feature_columns = feature_columns
        
        # Select features and handle missing values
        features_df = df[feature_columns].copy()
        features_df.fillna(features_df.mean(), inplace=True)
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features_df)
        
        return pd.DataFrame(scaled_features, index=df.index, columns=feature_columns)
    
    def fit(self, df: pd.DataFrame, feature_columns: Optional[List[str]] = None) -> 'CustomerSegmentation':
        """
        Fit the segmentation model to the data.
        
        Args:
            df: DataFrame with customer features
            feature_columns: List of columns to use for segmentation (optional)
            
        Returns:
            Self for method chaining
        """
        # Preprocess features
        preprocessed_features = self.preprocess_features(df, feature_columns)
        
        # Fit KMeans model
        self.kmeans.fit(preprocessed_features)
        
        # Create segment profiles
        self.segment_profiles = self._create_segment_profiles(df)
        
        return self
    
    def predict(self, df: pd.DataFrame) -> pd.Series:
        """
        Predict segments for new data.
        
        Args:
            df: DataFrame with customer features
            
        Returns:
            Series with segment labels
        """
        # Preprocess features
        preprocessed_features = self.preprocess_features(df, self.feature_columns)
        
        # Predict segments
        segments = self.kmeans.predict(preprocessed_features)
        
        return pd.Series(segments, index=df.index, name='segment')
    
    def fit_predict(self, df: pd.DataFrame, feature_columns: Optional[List[str]] = None) -> pd.Series:
        """
        Fit the segmentation model and predict segments.
        
        Args:
            df: DataFrame with customer features
            feature_columns: List of columns to use for segmentation (optional)
            
        Returns:
            Series with segment labels
        """
        # Fit the model
        self.fit(df, feature_columns)
        
        # Predict segments
        segments = self.predict(df)
        
        return segments
    
    def get_segment_profiles(self) -> pd.DataFrame:
        """
        Get profiles for each segment.
        
        Returns:
            DataFrame with segment profiles
        """
        if self.segment_profiles is None:
            raise ValueError("Model has not been fit yet. Call fit() first.")
        
        return self.segment_profiles
    
    def _create_segment_profiles(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create profiles for each segment.
        
        Args:
            df: DataFrame with customer features
            
        Returns:
            DataFrame with segment profiles
        """
        # Predict segments
        df = df.copy()
        df['segment'] = self.predict(df)
        
        # Calculate segment profiles
        segment_profiles = df.groupby('segment').agg({
            'recency': 'mean',
            'transaction_count': 'mean',
            'total_spend': 'mean',
            'average_transaction_value': 'mean',
            'purchase_frequency': 'mean',
            'customer_lifetime': 'mean',
            'average_basket_size': 'mean'
        })
        
        # Count customers in each segment
        segment_counts = df['segment'].value_counts().to_frame('customer_count')
        segment_profiles = segment_profiles.join(segment_counts)
        
        # Calculate percentage of customers in each segment
        segment_profiles['customer_percentage'] = segment_profiles['customer_count'] / segment_profiles['customer_count'].sum() * 100
        
        # Add segment names based on profiles
        segment_profiles['segment_name'] = self._assign_segment_names(segment_profiles)
        
        return segment_profiles
    
    def _assign_segment_names(self, segment_profiles: pd.DataFrame) -> pd.Series:
        """
        Assign names to segments based on their profiles.
        
        Args:
            segment_profiles: DataFrame with segment profiles
            
        Returns:
            Series with segment names
        """
        # Create a copy of the profiles for ranking
        profiles = segment_profiles.copy()
        
        # Rank segments by key metrics
        profiles['recency_rank'] = profiles['recency'].rank(ascending=True)  # Lower recency is better
        profiles['frequency_rank'] = profiles['transaction_count'].rank(ascending=False)  # Higher frequency is better
        profiles['monetary_rank'] = profiles['total_spend'].rank(ascending=False)  # Higher spend is better
        
        # Calculate overall RFM score (lower is better)
        profiles['rfm_score'] = profiles['recency_rank'] + profiles['frequency_rank'] + profiles['monetary_rank']
        
        # Assign segment names based on RFM score and other characteristics
        segment_names = {}
        
        # Determine the number of segments
        n_segments = len(profiles)
        
        # Used segment names tracker to avoid duplicates
        used_names = set()
        
        # Assign names based on relative rankings rather than fixed thresholds
        for segment in profiles.index:
            profile = profiles.loc[segment]
            
            # VIP customers: High frequency, high monetary value
            if profile['frequency_rank'] <= n_segments/2 and profile['monetary_rank'] <= n_segments/2 and profile['total_spend'] > profiles['total_spend'].median():
                segment_names[segment] = 'VIP'
                used_names.add('VIP')
            
            # At-risk customers: Low recency (haven't purchased recently), but good history
            elif profile['recency_rank'] >= n_segments/2 and profile['monetary_rank'] <= n_segments/2:
                segment_names[segment] = 'At Risk'
                used_names.add('At Risk')
            
            # New customers: Low customer lifetime, low transaction count
            elif profile['customer_lifetime'] < profiles['customer_lifetime'].median() and profile['recency_rank'] <= n_segments/2:
                segment_names[segment] = 'New'
                used_names.add('New')
            
            # Regular customers: Middle of the pack in most metrics
            elif profile['frequency_rank'] <= n_segments/2 and profile['monetary_rank'] > n_segments/2:
                segment_names[segment] = 'Regular'
                used_names.add('Regular')
            
            # Occasional customers: Low frequency, low monetary value
            elif profile['frequency_rank'] > n_segments/2 and profile['monetary_rank'] > n_segments/2:
                segment_names[segment] = 'Occasional'
                used_names.add('Occasional')
            
            # Default name if none of the above conditions are met
            else:
                # Determine a name based on the most distinctive characteristic
                if profile['recency_rank'] <= n_segments/3 and 'Recent Shoppers' not in used_names:
                    segment_names[segment] = 'Recent Shoppers'
                    used_names.add('Recent Shoppers')
                elif profile['frequency_rank'] <= n_segments/3 and 'Frequent Shoppers' not in used_names:
                    segment_names[segment] = 'Frequent Shoppers'
                    used_names.add('Frequent Shoppers')
                elif profile['monetary_rank'] <= n_segments/3 and 'High Value' not in used_names:
                    segment_names[segment] = 'High Value'
                    used_names.add('High Value')
                else:
                    # If we need to assign a name that's already used, make it more specific
                    base_name = 'Standard'
                    suffix = ''
                    counter = 1
                    
                    # If we need to use a duplicate name, add a numeric suffix
                    if profile['frequency_rank'] > n_segments/2 and profile['monetary_rank'] > n_segments/2:
                        base_name = 'Occasional'
                        # If 'Occasional' is already used, make it Occasional-Plus
                        if base_name in used_names:
                            suffix = '-Plus'
                    
                    segment_names[segment] = f"{base_name}{suffix}"
                    used_names.add(f"{base_name}{suffix}")
        
        return pd.Series(segment_names)
    
    def get_customer_segments(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get segments for all customers with segment names.
        
        Args:
            df: DataFrame with customer features
            
        Returns:
            DataFrame with customer segments and segment names
        """
        # Predict segments
        df = df.copy()
        df['segment'] = self.predict(df)
        
        # Add segment names
        segment_name_map = self.segment_profiles['segment_name'].to_dict()
        df['segment_name'] = df['segment'].map(segment_name_map)
        
        return df
    
    def get_segment_recommendations(self) -> Dict[str, Dict[str, str]]:
        """
        Get marketing recommendations for each segment.
        
        Returns:
            Dictionary with recommendations for each segment
        """
        if self.segment_profiles is None:
            raise ValueError("Model has not been fit yet. Call fit() first.")
        
        recommendations = {}
        
        for segment, profile in self.segment_profiles.iterrows():
            segment_name = profile['segment_name']
            
            if segment_name == 'VIP':
                recommendations[segment_name] = {
                    'email_frequency': 'Monthly',
                    'offer_type': 'Exclusive VIP offers, early access to new products, personalized recommendations',
                    'message_tone': 'Premium, personalized, appreciative',
                    'strategy': 'Retention and loyalty building, encourage referrals'
                }
            
            elif segment_name == 'At Risk':
                recommendations[segment_name] = {
                    'email_frequency': 'Bi-weekly',
                    'offer_type': 'Win-back offers, special discounts, reminders of past purchases',
                    'message_tone': 'We miss you, incentivizing',
                    'strategy': 'Re-engagement, remind of value proposition'
                }
            
            elif segment_name == 'New':
                recommendations[segment_name] = {
                    'email_frequency': 'Weekly for first month, then bi-weekly',
                    'offer_type': 'Welcome offers, educational content about products/services',
                    'message_tone': 'Welcoming, helpful, educational',
                    'strategy': 'Onboarding, build relationship, encourage second purchase'
                }
            
            elif segment_name == 'Regular':
                recommendations[segment_name] = {
                    'email_frequency': 'Bi-weekly',
                    'offer_type': 'Loyalty rewards, cross-sell related products',
                    'message_tone': 'Friendly, appreciative',
                    'strategy': 'Increase purchase frequency, encourage category exploration'
                }
            
            elif segment_name == 'Occasional':
                recommendations[segment_name] = {
                    'email_frequency': 'Monthly',
                    'offer_type': 'Seasonal promotions, category-specific offers',
                    'message_tone': 'Promotional, highlighting value',
                    'strategy': 'Increase purchase frequency, highlight value proposition'
                }
            
            else:
                recommendations[segment_name] = {
                    'email_frequency': 'Monthly',
                    'offer_type': 'General promotions, seasonal offers',
                    'message_tone': 'Promotional',
                    'strategy': 'Segment-specific strategy based on characteristics'
                }
        
        return recommendations
    
    def get_pca_components(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get PCA components for visualization.
        
        Args:
            df: DataFrame with customer features
            
        Returns:
            DataFrame with PCA components and segment labels
        """
        # Preprocess features
        preprocessed_features = self.preprocess_features(df, self.feature_columns)
        
        # Apply PCA
        pca_components = self.pca.fit_transform(preprocessed_features)
        
        # Create DataFrame with PCA components
        pca_df = pd.DataFrame(
            pca_components,
            columns=['PC1', 'PC2'],
            index=df.index
        )
        
        # Add segment labels
        pca_df['segment'] = self.predict(df)
        
        # Add segment names
        segment_name_map = self.segment_profiles['segment_name'].to_dict()
        pca_df['segment_name'] = pca_df['segment'].map(segment_name_map)
        
        return pca_df
    
    def save_model(self, model_dir: str) -> None:
        """
        Save the segmentation model to disk.
        
        Args:
            model_dir: Directory to save the model
        """
        # Create directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
        
        # Save model components
        joblib.dump(self.scaler, os.path.join(model_dir, 'scaler.pkl'))
        joblib.dump(self.kmeans, os.path.join(model_dir, 'kmeans.pkl'))
        joblib.dump(self.pca, os.path.join(model_dir, 'pca.pkl'))
        
        # Save feature columns and segment profiles
        joblib.dump(self.feature_columns, os.path.join(model_dir, 'feature_columns.pkl'))
        
        if self.segment_profiles is not None:
            self.segment_profiles.to_csv(os.path.join(model_dir, 'segment_profiles.csv'))
    
    @classmethod
    def load_model(cls, model_dir: str) -> 'CustomerSegmentation':
        """
        Load a segmentation model from disk.
        
        Args:
            model_dir: Directory containing the saved model
            
        Returns:
            Loaded CustomerSegmentation instance
        """
        # Create a new instance
        segmentation = cls()
        
        # Load model components
        segmentation.scaler = joblib.load(os.path.join(model_dir, 'scaler.pkl'))
        segmentation.kmeans = joblib.load(os.path.join(model_dir, 'kmeans.pkl'))
        segmentation.pca = joblib.load(os.path.join(model_dir, 'pca.pkl'))
        
        # Load feature columns
        segmentation.feature_columns = joblib.load(os.path.join(model_dir, 'feature_columns.pkl'))
        
        # Load segment profiles if they exist
        segment_profiles_path = os.path.join(model_dir, 'segment_profiles.csv')
        if os.path.exists(segment_profiles_path):
            segmentation.segment_profiles = pd.read_csv(segment_profiles_path, index_col=0)
        
        # Set n_segments based on the loaded KMeans model
        segmentation.n_segments = segmentation.kmeans.n_clusters
        
        return segmentation 