import pandas as pd
import numpy as np

def convert_units_to_pallets(quantity, units_per_pallet=24):
    return quantity / units_per_pallet

def convert_pallets_to_units(pallets, units_per_pallet=24):
    return pallets * units_per_pallet

def calculate_expected_demand(item_row, days_to_consider):
    daily_sale = item_row['AverageDailySale']
    return daily_sale * days_to_consider

def prepare_data_for_optimization(items_df, suppliers_df, pricing_df):
    # Create a dictionary to store all the data needed for optimization
    data = {
        'items': {},
        'suppliers': {},
        'available_suppliers': {},
        'costs': {}
    }
    
    # Process item data
    for _, item in items_df.iterrows():
        item_id = item['ItemID']
        # Calculate expected demand before expiry
        expiry_days = item['Expiry (days)']
        expected_demand = calculate_expected_demand(item, expiry_days)
        
        data['items'][item_id] = {
            'name': item['Name'],
            'current_stock': item['CurrentStock'],
            'min_stock': item['MinStock'],
            'max_stock': item['MaxStock'],
            'expiry_days': expiry_days,
            'average_daily_sale': item['AverageDailySale'],
            'expected_demand': expected_demand,
            'units_per_pallet': 24  # As per the task description
        }
    
    # Process supplier data
    for _, supplier in suppliers_df.iterrows():
        supplier_id = supplier['SupplierID']
        data['suppliers'][supplier_id] = {
            'name': supplier['Name'],
            'min_pallets': supplier['MinPallets'],
            'max_pallets': supplier['MaxPallets'],
            'lead_time': supplier['LeadTime (days)']
        }
    
    # Process pricing data and determine available suppliers for each item
    for item_id in data['items'].keys():
        # Get available suppliers for this item
        item_pricing = pricing_df[pricing_df['ItemID'] == item_id]
        data['available_suppliers'][item_id] = item_pricing['SupplierID'].unique().tolist()
        
        # Store costs for each item-supplier combination
        data['costs'][item_id] = {}
        for _, row in item_pricing.iterrows():
            supplier_id = row['SupplierID']
            data['costs'][item_id][supplier_id] = row['CostPerPallet']
    
    return data
