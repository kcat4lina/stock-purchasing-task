# ths module handles loading the CSV files aontaining supplier data, item data & the mapping between suppliers and items

import pandas as pd
from pathlib import Path

def load_data_from_source(filename):
    # Get the project root directory (where main.py is located)
    project_root = Path.cwd()
    
    # Construct the path to the file in the Source directory
    file_path = project_root / "Source" / filename
    
    try:
        df = pd.read_csv(file_path)
        print(f"Successfully loaded {filename} with {len(df)} records")
        return df
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        raise

def load_item_data():
    return load_data_from_source("items_updated.csv")

def load_supplier_data():
    return load_data_from_source("suppliers.csv")

def load_pricing_data():
    return load_data_from_source("pricing.csv")

def get_available_suppliers_for_item(pricing_df, item_id):
    # Based on the actual column names in pricing.csv
    available_suppliers = pricing_df[pricing_df['ItemID'] == item_id]['SupplierID'].unique().tolist()
    return available_suppliers
