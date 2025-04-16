"""
Test Data Manager

This page allows users to add and manage test customer data for email marketing campaigns.
"""
import os
import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, timedelta
import random

# Set page configuration
st.set_page_config(
    page_title="Test Data Manager - Mall Customer Segmentation",
    page_icon="📊",
    layout="wide"
)

# Initialize session state variables
if 'random_data' not in st.session_state:
    st.session_state.random_data = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'edit_index' not in st.session_state:
    st.session_state.edit_index = None
if 'edited_data' not in st.session_state:
    st.session_state.edited_data = None

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
        .action-btn {
            background-color: #4527A0;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 0.3rem;
            text-decoration: none;
            font-weight: bold;
        }
        .email-edit-table {
            width: 100%;
            border-collapse: collapse;
        }
        .email-edit-table th, .email-edit-table td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .email-edit-table tr:hover {
            background-color: #f5f5f5;
        }
    </style>
    """, unsafe_allow_html=True)

# Constants
TEST_DATA_PATH = "data/test_customers.csv"
DEFAULT_SEGMENTS = ["VIP", "Regular", "New", "Occasional", "At Risk"]
DEFAULT_CATEGORIES = ["electronics", "clothing", "home_kitchen", "groceries"]

# Function to load test data
def load_test_data():
    """Load test customer data from CSV file"""
    try:
        if os.path.exists(TEST_DATA_PATH):
            return pd.read_csv(TEST_DATA_PATH)
        else:
            # Create empty dataframe with required columns
            return pd.DataFrame(columns=[
                'customer_id', 'email', 'first_name', 'last_name', 
                'segment_name', 'primary_category', 'age', 'gender', 'city',
                'last_purchase_date', 'total_spent'
            ])
    except Exception as e:
        st.error(f"Error loading test data: {e}")
        return pd.DataFrame()

# Function to save test data
def save_test_data(df):
    """Save test customer data to CSV file"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(TEST_DATA_PATH), exist_ok=True)
        df.to_csv(TEST_DATA_PATH, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving test data: {e}")
        return False

# Function to generate random customer data
def generate_random_data(num_customers=5):
    """Generate random customer data for testing"""
    random_data = []
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
    
    for _ in range(num_customers):
        customer_id = str(uuid.uuid4())[:8]
        email_domain = random.choice(["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"])
        first_name = random.choice(["John", "Mary", "James", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth"])
        last_name = random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"])
        email = f"{first_name.lower()}.{last_name.lower()}@{email_domain}"
        
        segment_name = random.choice(DEFAULT_SEGMENTS)
        primary_category = random.choice(DEFAULT_CATEGORIES)
        age = random.randint(18, 65)
        gender = random.choice(["Male", "Female"])
        city = random.choice(cities)
        
        # Random last purchase date within last 60 days
        days_ago = random.randint(1, 60)
        last_purchase_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        
        total_spent = round(random.uniform(50.0, 1000.0), 2)
        
        random_data.append({
            'customer_id': customer_id,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'segment_name': segment_name,
            'primary_category': primary_category,
            'age': age,
            'gender': gender,
            'city': city,
            'last_purchase_date': last_purchase_date,
            'total_spent': total_spent
        })
    
    return pd.DataFrame(random_data)

# Function to edit customer data
def edit_customer(test_data, index, new_data):
    """Edit customer data at the given index"""
    try:
        updated_data = test_data.copy()
        for key, value in new_data.items():
            updated_data.at[index, key] = value
        return updated_data
    except Exception as e:
        st.error(f"Error updating customer data: {e}")
        return test_data

# Function to start editing a customer
def start_edit_mode(index):
    st.session_state.edit_mode = True
    st.session_state.edit_index = index

# Function to cancel editing
def cancel_edit_mode():
    st.session_state.edit_mode = False
    st.session_state.edit_index = None
    st.session_state.edited_data = None

# Main function
def main():
    # Load CSS
    load_css()
    
    # Display header
    st.markdown('<h1 class="main-header">Test Data Manager</h1>', unsafe_allow_html=True)
    
    # Load test data
    test_data = load_test_data()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Add Test Customers", "View/Edit Test Data", "Generate Random Data"])
    
    with tab1:
        st.markdown('<h2 class="sub-header">Add Test Customer</h2>', unsafe_allow_html=True)
        
        # Form for adding a new test customer
        with st.form("add_customer_form"):
            # Basic information
            col1, col2 = st.columns(2)
            
            with col1:
                email = st.text_input("Email Address", placeholder="customer@example.com")
                first_name = st.text_input("First Name", placeholder="John")
                last_name = st.text_input("Last Name", placeholder="Doe")
            
            with col2:
                segment = st.selectbox("Customer Segment", DEFAULT_SEGMENTS)
                category = st.selectbox("Primary Product Category", DEFAULT_CATEGORIES)
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            
            # Additional information
            col3, col4 = st.columns(2)
            
            with col3:
                age = st.number_input("Age", min_value=18, max_value=100, value=30)
                city = st.text_input("City", placeholder="New York")
            
            with col4:
                last_purchase_date = st.date_input("Last Purchase Date", value=datetime.now())
                total_spent = st.number_input("Total Spent", min_value=0.0, value=100.0, format="%.2f")
            
            # Submit button
            submit_button = st.form_submit_button("Add Customer")
        
        # Handle form submission
        if submit_button:
            if not email:
                st.error("Email address is required.")
            elif not first_name:
                st.error("First name is required.")
            else:
                # Create customer ID
                customer_id = str(uuid.uuid4())[:8]
                
                # Create new customer record
                new_customer = {
                    'customer_id': customer_id,
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name if last_name else "",
                    'segment_name': segment,
                    'primary_category': category,
                    'age': age,
                    'gender': gender,
                    'city': city if city else "",
                    'last_purchase_date': last_purchase_date.strftime("%Y-%m-%d"),
                    'total_spent': total_spent
                }
                
                # Add new customer to dataframe
                test_data = pd.concat([test_data, pd.DataFrame([new_customer])], ignore_index=True)
                
                # Save updated data
                if save_test_data(test_data):
                    st.success(f"Customer {first_name} {last_name} added successfully!")
    
    with tab2:
        st.markdown('<h2 class="sub-header">Test Customer Data</h2>', unsafe_allow_html=True)
        
        if test_data.empty:
            st.info("No test customers found. Add some customers in the 'Add Test Customers' tab.")
        else:
            # Display test data
            st.write(f"Total Customers: {len(test_data)}")
            
            # Add search and filter options
            search_term = st.text_input("Search by email or name", "")
            
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                filter_segment = st.multiselect("Filter by Segment", options=sorted(test_data['segment_name'].unique()))
            
            with filter_col2:
                filter_category = st.multiselect("Filter by Category", options=sorted(test_data['primary_category'].unique()))
            
            # Apply filters
            filtered_data = test_data.copy()
            
            if search_term:
                filtered_data = filtered_data[
                    filtered_data['email'].str.contains(search_term, case=False) |
                    filtered_data['first_name'].str.contains(search_term, case=False) |
                    filtered_data['last_name'].str.contains(search_term, case=False)
                ]
            
            if filter_segment:
                filtered_data = filtered_data[filtered_data['segment_name'].isin(filter_segment)]
            
            if filter_category:
                filtered_data = filtered_data[filtered_data['primary_category'].isin(filter_category)]
            
            # Check if we're in edit mode
            if st.session_state.edit_mode and st.session_state.edit_index is not None:
                # Get the index in the original dataframe
                orig_index = st.session_state.edit_index
                
                # Get the customer data
                if orig_index < len(test_data):
                    customer = test_data.iloc[orig_index].to_dict()
                    
                    # Create an edit form
                    st.markdown("### Edit Customer")
                    with st.form("edit_customer_form"):
                        # Basic information
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            email = st.text_input("Email Address", value=customer['email'])
                            first_name = st.text_input("First Name", value=customer['first_name'])
                            last_name = st.text_input("Last Name", value=customer['last_name'])
                        
                        with col2:
                            segment = st.selectbox("Customer Segment", DEFAULT_SEGMENTS, index=DEFAULT_SEGMENTS.index(customer['segment_name']) if customer['segment_name'] in DEFAULT_SEGMENTS else 0)
                            category = st.selectbox("Primary Product Category", DEFAULT_CATEGORIES, index=DEFAULT_CATEGORIES.index(customer['primary_category']) if customer['primary_category'] in DEFAULT_CATEGORIES else 0)
                            gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(customer['gender']) if customer['gender'] in ["Male", "Female", "Other"] else 0)
                        
                        # Additional information
                        col3, col4 = st.columns(2)
                        
                        with col3:
                            age = st.number_input("Age", min_value=18, max_value=100, value=int(customer['age']))
                            city = st.text_input("City", value=customer['city'])
                        
                        with col4:
                            last_purchase_date = st.date_input("Last Purchase Date", value=datetime.strptime(customer['last_purchase_date'], "%Y-%m-%d") if isinstance(customer['last_purchase_date'], str) else datetime.now())
                            total_spent = st.number_input("Total Spent", min_value=0.0, value=float(customer['total_spent']), format="%.2f")
                        
                        # Submit buttons
                        col5, col6 = st.columns(2)
                        
                        with col5:
                            submit_button = st.form_submit_button("Save Changes")
                        
                        with col6:
                            cancel_button = st.form_submit_button("Cancel")
                    
                    if submit_button:
                        # Create updated customer record
                        updated_customer = {
                            'email': email,
                            'first_name': first_name,
                            'last_name': last_name if last_name else "",
                            'segment_name': segment,
                            'primary_category': category,
                            'age': age,
                            'gender': gender,
                            'city': city if city else "",
                            'last_purchase_date': last_purchase_date.strftime("%Y-%m-%d"),
                            'total_spent': total_spent
                        }
                        
                        # Update customer in dataframe
                        test_data = edit_customer(test_data, orig_index, updated_customer)
                        
                        # Save updated data
                        if save_test_data(test_data):
                            st.success(f"Customer {first_name} {last_name} updated successfully!")
                            
                            # Exit edit mode
                            cancel_edit_mode()
                            st.rerun()
                    
                    if cancel_button:
                        # Exit edit mode
                        cancel_edit_mode()
                        st.rerun()
            else:
                # Display filtered data as a table with edit buttons
                if not filtered_data.empty:
                    st.markdown("### Customer List")
                    
                    # Create a container for the table
                    table_container = st.container()
                    
                    with table_container:
                        # Display each customer with edit options
                        for i, (index, row) in enumerate(filtered_data.iterrows()):
                            # Find the index in the original dataframe
                            orig_index = test_data.index[test_data['customer_id'] == row['customer_id']].tolist()[0] if 'customer_id' in test_data.columns else index
                            
                            # Create a row for each customer
                            cols = st.columns([3, 2, 2, 2, 1.5, 1.5])
                            
                            with cols[0]:
                                st.write(f"**{row['email']}**")
                            
                            with cols[1]:
                                st.write(f"{row['first_name']} {row['last_name']}")
                            
                            with cols[2]:
                                st.write(f"Segment: {row['segment_name']}")
                            
                            with cols[3]:
                                st.write(f"Category: {row['primary_category']}")
                            
                            with cols[4]:
                                st.write(f"${row['total_spent']:.2f}")
                            
                            with cols[5]:
                                if st.button(f"Edit", key=f"edit_{i}"):
                                    start_edit_mode(orig_index)
                                    st.rerun()
                            
                            # Add a separator
                            st.markdown("---")
                else:
                    st.warning("No customers match the search criteria.")
            
            # Delete selected customers
            if st.button("Delete All Test Data"):
                if st.checkbox("I understand this will delete ALL test customer data"):
                    # Create empty dataframe with required columns
                    empty_df = pd.DataFrame(columns=[
                        'customer_id', 'email', 'first_name', 'last_name', 
                        'segment_name', 'primary_category', 'age', 'gender', 'city',
                        'last_purchase_date', 'total_spent'
                    ])
                    
                    # Save empty dataframe
                    if save_test_data(empty_df):
                        st.success("All test customer data deleted successfully!")
                        st.info("Refresh the page to see the updated data.")
            
            # Export data button
            if st.download_button(
                "Export Test Data",
                test_data.to_csv(index=False).encode('utf-8'),
                "test_customers.csv",
                "text/csv",
                key='download-csv'
            ):
                st.success("Test data exported successfully!")
    
    with tab3:
        st.markdown('<h2 class="sub-header">Generate Random Test Data</h2>', unsafe_allow_html=True)
        
        # Options for generating random data
        num_customers = st.number_input("Number of customers to generate", min_value=1, max_value=100, value=10)
        
        # Generate button - on click, store the generated data in session state
        if st.button("Generate Random Data"):
            st.session_state.random_data = generate_random_data(num_customers)
            st.success(f"Generated {num_customers} random customers!")
        
        # Display generated data if available
        if st.session_state.random_data is not None:
            st.markdown("### Preview of Generated Data")
            
            # Display editable email data
            st.markdown("#### Edit Email Addresses (if needed)")
            st.warning("Edit email addresses before adding to test customers")
            
            # Create a copy of the generated data for editing
            if st.session_state.edited_data is None:
                st.session_state.edited_data = st.session_state.random_data.copy()
            
            # Create a form for editing emails
            with st.form("edit_emails_form"):
                # Create a container for the email editing interface
                for i, row in enumerate(st.session_state.edited_data.iterrows()):
                    idx, data = row
                    cols = st.columns([3, 2, 2, 3])
                    
                    with cols[0]:
                        st.write(f"{data['first_name']} {data['last_name']}")
                    
                    with cols[1]:
                        st.write(f"Segment: {data['segment_name']}")
                    
                    with cols[2]:
                        st.write(f"Category: {data['primary_category']}")
                    
                    with cols[3]:
                        new_email = st.text_input(f"Email {i+1}", value=data['email'], key=f"email_{i}")
                        st.session_state.edited_data.at[idx, 'email'] = new_email
                
                # Submit button
                submit_emails_button = st.form_submit_button("Update Emails")
            
            if submit_emails_button:
                st.success("Emails updated successfully!")
            
            # Display the updated data
            st.dataframe(st.session_state.edited_data, use_container_width=True)
            
            # Add button - separate from generate button
            if st.button("Add to Test Customers"):
                # Combine existing and generated data
                combined_data = pd.concat([test_data, st.session_state.edited_data], ignore_index=True)
                
                # Save combined data
                if save_test_data(combined_data):
                    st.success(f"{len(st.session_state.edited_data)} random customers added successfully!")
                    # Clear the session state
                    st.session_state.random_data = None
                    st.session_state.edited_data = None
                    st.info("Refresh the page to see the updated data in the 'View/Edit Test Data' tab.")

# Run the app
if __name__ == "__main__":
    main() 