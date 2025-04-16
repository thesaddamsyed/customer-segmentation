import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import uuid
import os

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Create directories if they don't exist
os.makedirs('data', exist_ok=True)

# Constants
NUM_CUSTOMERS = 2000
NUM_TRANSACTIONS = 10000

# --------------- Local Data Specific to Proddatur and Andhra Pradesh ---------------

# Local malls/shopping centers in and around Proddatur
shopping_malls = [
    "Sri Lakshmi Shopping Mall", 
    "Proddatur Central Mall", 
    "JC Brothers Shopping Complex",
    "PSR Shopping Mall", 
    "SVR Mall"
]

# Popular nearby cities (all in Andhra Pradesh)
cities = {
    "Proddatur": 0.45,  # Main city (45% of customers)
    "Kadapa": 0.20,     # District headquarters
    "Jammalamadugu": 0.08,
    "Kamalapuram": 0.05,
    "Yerraguntla": 0.05,
    "Mydukur": 0.04,
    "Pulivendla": 0.04,
    "Rajampet": 0.03,
    "Badvel": 0.03,
    "Rayachoti": 0.03
}

# Common South Indian first names 
first_names_male = [
    "Srinivas", "Venkat", "Ramesh", "Suresh", "Krishna", "Ravi", "Vijay", 
    "Siva", "Prasad", "Narayana", "Venu", "Satish", "Harish", "Mahesh", 
    "Rajesh", "Anil", "Sunil", "Pavan", "Mohan", "Vamsi", "Kiran", "Srikanth",
    "Ganesh", "Manoj", "Naveen", "Kalyan", "Surya", "Chandra", "Sekhar", "Praveen",
    "Madhu", "Murali", "Sudhakar", "Naga", "Subba", "Rao", "Naidu", "Babu", "Reddy"
]

first_names_female = [
    "Lakshmi", "Padma", "Sujatha", "Sarita", "Kavita", "Sunita", "Radha", 
    "Vijaya", "Usha", "Anitha", "Rani", "Sudha", "Latha", "Sarala", "Rama", 
    "Jyothi", "Saraswati", "Devi", "Durga", "Sridevi", "Savitri", "Aruna",
    "Sandhya", "Lalitha", "Meena", "Swapna", "Sravani", "Divya", "Priya", "Nirmala",
    "Sneha", "Jaya", "Sujana", "Pavani", "Sirisha", "Madhavi", "Aparna", "Anupama"
]

# Common South Indian last names (particularly common in Andhra Pradesh)
last_names = [
    "Reddy", "Naidu", "Sharma", "Varma", "Rao", "Choudhary", "Nayak", "Devi",
    "Raju", "Goud", "Achary", "Sastry", "Chowdary", "Gupta", "Kumar", "Prasad",
    "Patil", "Murthy", "Kondaiah", "Setty", "Yadav", "Agarwal", "Shastri", "Pandey",
    "Singh", "Subramaniam", "Babu", "Gopal", "Prakash", "Narayan", "Swamy", "Pillai",
    "Gowda", "Iyer", "Hegde", "Srinivasulu", "Venkateswarlu", "Ramakrishna", "Suryanarayana"
]

# Email domains
email_domains = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "rediffmail.com", 
    "proddaturmail.com", "kakinada.edu.in", "apsrtc.gov.in", "andhramail.com", 
    "apcob.org"
]

# Categories more relevant to Indian context
categories = {
    "Clothing": 0.25,
    "Electronics": 0.20,
    "Groceries": 0.18,
    "Home & Kitchen": 0.15,
    "Beauty": 0.10,
    "Jewelry": 0.06,
    "Footwear": 0.04,
    "Sports": 0.02
}

# Products relevant to Indian context with realistic price ranges (in INR)
products = {
    "Clothing": [
        ("Men's Cotton Shirt", 800, 2000),
        ("Women's Saree", 1500, 8000),
        ("Kids' T-Shirt", 300, 800),
        ("Churidar Set", 1200, 3500),
        ("Kurta Pajama", 1000, 2500),
        ("Lehenga", 2000, 10000),
        ("Cotton Dhoti", 400, 900),
        ("Silk Pattu Saree", 5000, 20000),
        ("Designer Blouse", 600, 2000),
        ("Readymade Salwar", 1000, 3000)
    ],
    "Electronics": [
        ("Samsung Galaxy M32", 12000, 16000),
        ("OnePlus Nord CE 2", 24000, 30000),
        ("LG Smart TV", 25000, 50000),
        ("Philips Mixer Grinder", 2500, 5000),
        ("Bajaj Induction Cooker", 3000, 6000),
        ("Crompton Ceiling Fan", 1500, 3000),
        ("Boat Headphones", 1000, 3000),
        ("Mi Power Bank", 800, 2000),
        ("Sony Home Theatre", 15000, 30000),
        ("Havells Water Heater", 4000, 8000)
    ],
    "Groceries": [
        ("Aashirvaad Atta (10kg)", 400, 500),
        ("Sunflower Oil (5L)", 800, 1100),
        ("Toor Dal (2kg)", 250, 350),
        ("Basmati Rice (5kg)", 500, 800),
        ("MTR Masala Pack", 300, 500),
        ("Telugu Pickles (1kg)", 200, 400),
        ("Kellogg's Corn Flakes", 180, 300),
        ("Nandini Ghee (1L)", 500, 700),
        ("Britannia Biscuits Pack", 100, 200),
        ("Horlicks (500g)", 250, 350)
    ],
    "Home & Kitchen": [
        ("Prestige Pressure Cooker", 1500, 3500),
        ("Milton Flask Set", 800, 1500),
        ("Steel Dinner Set", 1200, 3000),
        ("Cotton Bed Sheet", 600, 1500),
        ("Faber Chimney", 8000, 15000),
        ("Clay Cookware Set", 1000, 2500),
        ("Designer Curtains", 1500, 4000),
        ("Copper Water Bottles", 700, 1500),
        ("Plastic Storage Containers", 400, 1000),
        ("Wooden Cutting Board", 300, 800)
    ],
    "Beauty": [
        ("Lakme Lipstick", 300, 800),
        ("Himalaya Face Wash", 150, 300),
        ("Maybelline Mascara", 400, 900),
        ("Forest Essentials Cream", 800, 2000),
        ("Patanjali Hair Oil", 100, 250),
        ("Ayurvedic Face Pack", 250, 600),
        ("L'Oreal Hair Color", 500, 1000),
        ("Biotique Face Scrub", 200, 450),
        ("Nivea Skin Cream", 200, 500),
        ("Dove Soap (Pack of 3)", 120, 200)
    ],
    "Jewelry": [
        ("Gold Plated Bangles", 1000, 3000),
        ("Silver Anklets", 800, 2500),
        ("Temple Jewellery Set", 1500, 5000),
        ("Oxidized Earrings", 300, 800),
        ("Pearl Necklace", 1000, 4000),
        ("Traditional Maang Tikka", 500, 1500),
        ("Stone Studded Rings", 400, 1200),
        ("Brass Antique Jewelry", 600, 2000),
        ("Imitation Bridal Set", 2000, 6000),
        ("Silver Toe Rings", 200, 600)
    ],
    "Footwear": [
        ("Men's Leather Sandals", 800, 2000),
        ("Women's Kolhapuri Chappals", 500, 1500),
        ("Kids' School Shoes", 600, 1200),
        ("Sports Sneakers", 1000, 3000),
        ("Traditional Mojari", 700, 1800),
        ("Ladies Heels", 900, 2500),
        ("Bata Formal Shoes", 1200, 2800),
        ("Paragon Slippers", 300, 600),
        ("Woodland Boots", 2000, 4000),
        ("Rubber Flip Flops", 150, 400)
    ],
    "Sports": [
        ("Yonex Badminton Racket", 1000, 3000),
        ("Cricket Bat (Kashmir Willow)", 800, 2500),
        ("Nivia Football", 500, 1200),
        ("Yoga Mat", 600, 1500),
        ("Cosco Basketball", 700, 1800),
        ("Table Tennis Racket", 500, 1300),
        ("Skipping Rope", 200, 500),
        ("Fitness Dumbbells", 1000, 2500),
        ("Nike Running Shoes", 2500, 5000),
        ("Sports Water Bottle", 300, 600)
    ]
}

# Payment methods
payment_methods = {
    "UPI": 0.35,
    "Debit Card": 0.20,
    "Credit Card": 0.15,
    "Cash": 0.20,
    "Paytm": 0.10
}

# ------------------ Generate Customer Data ------------------

def generate_customers(num_customers):
    """Generate customer data with realistic Indian names and details"""
    customers = []
    
    for i in range(1, num_customers + 1):
        customer_id = f"CUST{i:04d}"
        
        # Determine gender
        gender = random.choices(["Male", "Female"], weights=[0.52, 0.48])[0]
        
        # Generate name based on gender
        if gender == "Male":
            first_name = random.choice(first_names_male)
        else:
            first_name = random.choice(first_names_female)
        
        last_name = random.choice(last_names)
        
        # Generate email
        email_domain = random.choice(email_domains)
        email = f"{first_name.lower()}.{last_name.lower()}@{email_domain}"
        
        # Generate age - adult distribution skewed towards younger adults
        age = int(np.random.triangular(18, 30, 75))
        
        # Assign city based on weighted probabilities
        city = random.choices(
            list(cities.keys()),
            weights=list(cities.values())
        )[0]
        
        customers.append({
            "customer_id": customer_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "gender": gender,
            "age": age,
            "city": city
        })
    
    return pd.DataFrame(customers)

# ------------------ Generate Transaction Data ------------------

def generate_transactions(customers_df, num_transactions):
    """Generate transaction data with realistic products, prices and patterns"""
    transactions = []
    
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    for i in range(1, num_transactions + 1):
        invoice_no = f"INV{i:05d}"
        
        # Select a random customer
        customer = customers_df.sample(1).iloc[0]
        customer_id = customer["customer_id"]
        
        # Generate transaction date
        transaction_date = start_date + timedelta(
            days=random.randint(0, (end_date - start_date).days)
        )
        
        # Format date as Indian format (dd/mm/yyyy)
        invoice_date = transaction_date.strftime("%d/%m/%Y")
        
        # Select category based on weighted probabilities
        category = random.choices(
            list(categories.keys()),
            weights=list(categories.values())
        )[0]
        
        # Select product from the category
        product_name, min_price, max_price = random.choice(products[category])
        
        # Generate quantity (skewed towards smaller quantities)
        quantity = min(int(np.random.exponential(3)) + 1, 20)
        
        # Generate unit price
        price = round(random.uniform(min_price, max_price), 2)
        
        # Calculate total amount
        total_amount = round(price * quantity, 2)
        
        # Generate discount (0-50%)
        discount = round(random.uniform(0, 50), 2)
        
        # Apply discount to total
        discounted_total = round(total_amount * (1 - discount/100), 2)
        
        # Select payment method based on weighted probabilities
        payment_method = random.choices(
            list(payment_methods.keys()),
            weights=list(payment_methods.values())
        )[0]
        
        # Select shopping mall
        shopping_mall = random.choice(shopping_malls)
        
        transactions.append({
            "invoice_no": invoice_no,
            "customer_id": customer_id,
            "category": category,
            "product_name": product_name,
            "quantity": quantity,
            "price": price,
            "payment_method": payment_method,
            "invoice_date": invoice_date,
            "shopping_mall": shopping_mall,
            "discount": discount,
            "email": customer["email"],
            "gender": customer["gender"],
            "age": customer["age"],
            "city": customer["city"],
            "total_amount": discounted_total
        })
    
    return pd.DataFrame(transactions)

# ------------------ Process Data for Feature Generation ------------------

def process_transactions_for_features(transactions_df, customers_df):
    """Process transaction data to extract customer features"""
    
    # Convert invoice_date to datetime
    transactions_df['invoice_date'] = pd.to_datetime(transactions_df['invoice_date'], format='%d/%m/%Y')
    
    # Calculate spending by category
    category_spending = transactions_df.groupby(['customer_id', 'category'])['total_amount'].sum().unstack(fill_value=0)
    
    # Initialize features dataframe with customers
    features = customers_df[['customer_id', 'email', 'gender', 'age', 'city']].copy()
    features = features.set_index('customer_id')
    
    # Get transaction counts
    transaction_counts = transactions_df.groupby('customer_id').size()
    features['transaction_count'] = transaction_counts
    
    # Fill missing transaction counts with 0
    features['transaction_count'] = features['transaction_count'].fillna(0).astype(int)
    
    # Calculate total spend
    total_spend = transactions_df.groupby('customer_id')['total_amount'].sum()
    features['total_spend'] = total_spend
    
    # Fill missing total spend with 0
    features['total_spend'] = features['total_spend'].fillna(0)
    
    # Calculate average transaction value
    features['average_transaction_value'] = features['total_spend'] / features['transaction_count'].replace(0, np.nan)
    
    # Calculate maximum transaction value
    max_transaction = transactions_df.groupby('customer_id')['total_amount'].max()
    features['max_transaction_value'] = max_transaction
    
    # Calculate total items purchased
    total_items = transactions_df.groupby('customer_id')['quantity'].sum()
    features['total_items_purchased'] = total_items
    
    # Calculate average basket size
    features['average_basket_size'] = features['total_items_purchased'] / features['transaction_count'].replace(0, np.nan)
    
    # Calculate average discount
    avg_discount = transactions_df.groupby('customer_id')['discount'].mean()
    features['average_discount'] = avg_discount
    
    # Calculate recency (days since last purchase)
    last_purchase_date = transactions_df.groupby('customer_id')['invoice_date'].max()
    reference_date = datetime(2024, 1, 1)  # Reference date for recency calculation
    features['recency'] = (reference_date - last_purchase_date).dt.days
    
    # Calculate first purchase date
    first_purchase_date = transactions_df.groupby('customer_id')['invoice_date'].min()
    features['first_purchase_date'] = first_purchase_date
    
    # Calculate last purchase date
    features['last_purchase_date'] = last_purchase_date
    
    # Calculate customer lifetime (days between first and last purchase)
    features['customer_lifetime'] = (last_purchase_date - first_purchase_date).dt.days
    
    # Calculate purchase frequency (purchases per month if lifetime > 0)
    features['purchase_frequency'] = np.where(
        features['customer_lifetime'] > 0,
        features['transaction_count'] / (features['customer_lifetime'] / 30),
        features['transaction_count']  # If lifetime is 0, frequency is transaction count
    )
    
    # Add spending by category
    for category in categories.keys():
        if category in category_spending.columns:
            features[f'spend_{category.lower().replace(" & ", "_")}'] = category_spending[category]
        else:
            features[f'spend_{category.lower().replace(" & ", "_")}'] = 0
    
    # Calculate percentage of spending by category
    for category in categories.keys():
        cat_col = f'spend_{category.lower().replace(" & ", "_")}'
        pct_col = f'pct_{category.lower().replace(" & ", "_")}'
        features[pct_col] = features[cat_col] / features['total_spend'].replace(0, np.nan) * 100
        features[pct_col] = features[pct_col].fillna(0)
    
    # Determine primary category
    category_columns = [f'spend_{category.lower().replace(" & ", "_")}' for category in categories.keys()]
    features['primary_category'] = features[category_columns].idxmax(axis=1)
    features['primary_category'] = features['primary_category'].str.replace('spend_', '')
    
    # Fill NaN values
    features = features.fillna(0)
    
    # Create one-hot encoded columns for city
    city_dummies = pd.get_dummies(features['city'], prefix='city')
    
    # Add dummy variables to features
    features = pd.concat([features, city_dummies], axis=1)
    
    # Create one-hot encoded columns for gender
    gender_dummies = pd.get_dummies(features['gender'], prefix='gender')
    
    # Add dummy variables to features
    features = pd.concat([features, gender_dummies], axis=1)
    
    return features

# ------------------ Main Execution ------------------

def main():
    # Generate customer data
    print("Generating customer data...")
    customers_df = generate_customers(NUM_CUSTOMERS)
    
    # Generate transaction data
    print("Generating transaction data...")
    transactions_df = generate_transactions(customers_df, NUM_TRANSACTIONS)
    
    # Process data for feature generation
    print("Processing data for feature generation...")
    features_df = process_transactions_for_features(transactions_df, customers_df)
    
    # Save to CSV files
    print("Saving data to CSV files...")
    transactions_df.to_csv("project2.csv", index=False)
    features_df.to_csv("data/processed_customer_features.csv")
    
    print("Done!")
    print(f"Generated {len(customers_df)} customers")
    print(f"Generated {len(transactions_df)} transactions")
    print(f"Features shape: {features_df.shape}")

if __name__ == "__main__":
    main() 