import pandas as pd
import os
import uuid
import sys

# Create required directories
os.makedirs("test_data", exist_ok=True)

def create_test_customer(email):
    """
    Create a test customer dataset with a single customer record.
    
    Args:
        email: Your email address for testing
    """
    # Generate a unique customer ID
    customer_id = str(uuid.uuid4())
    
    # Create customer data
    customer_data = {
        'customer_id': [customer_id],
        'id': [customer_id],  # Duplicate as both id and customer_id for compatibility
        'email': [email],
        'first_name': ['Test'],
        'last_name': ['User'],
        'age': [35],
        'gender': ['Male'],
        'city': ['Test City'],
        'spending_score': [80],
        'annual_income': [75000],
        'segment_name': ['High Value'],
        'primary_category': ['Electronics'],
        'category': ['Electronics'],
        'recency': [5],
        'frequency': [8],
        'monetary': [1200]
    }
    
    # Create DataFrame
    df = pd.DataFrame(customer_data)
    
    # Save to CSV
    output_path = "test_data/test_customer.csv"
    df.to_csv(output_path, index=False)
    print(f"Test customer dataset created at: {output_path}")
    print(f"Customer ID: {customer_id}")
    print(f"Email: {email}")
    
    return df

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Use email from command line argument
        your_email = sys.argv[1]
    else:
        # Ask for email interactively
        your_email = input("Enter your email address for testing: ")
    
    if not your_email or '@' not in your_email:
        print("Error: Please provide a valid email address")
        sys.exit(1)
        
    create_test_customer(your_email) 