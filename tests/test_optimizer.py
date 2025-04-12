import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.loader import load_item_data, load_supplier_data, load_pricing_data
from src.utils.preprocessing import prepare_data_for_optimization, convert_units_to_pallets, convert_pallets_to_units
from src.models.optimizer import create_optimization_model, solve_model

# Test data loading
def test_data_loading():
    items_df = load_item_data()
    suppliers_df = load_supplier_data()
    pricing_df = load_pricing_data()
    
    assert items_df is not None and not items_df.empty
    assert suppliers_df is not None and not suppliers_df.empty
    assert pricing_df is not None and not pricing_df.empty
    
    assert 'ItemID' in items_df.columns
    assert 'SupplierID' in suppliers_df.columns
    assert 'CostPerPallet' in pricing_df.columns

# Test unit conversion functions
def test_unit_conversion():
    assert convert_units_to_pallets(24) == 1.0
    assert convert_units_to_pallets(48) == 2.0
    assert convert_units_to_pallets(12) == 0.5
    
    assert convert_pallets_to_units(1) == 24
    assert convert_pallets_to_units(2.5) == 60
    assert convert_pallets_to_units(0.5) == 12

# Test data preprocessing
def test_data_preprocessing():
    items_df = load_item_data()
    suppliers_df = load_supplier_data()
    pricing_df = load_pricing_data()
    
    data = prepare_data_for_optimization(items_df, suppliers_df, pricing_df)
    
    assert 'items' in data
    assert 'suppliers' in data
    assert 'available_suppliers' in data
    assert 'costs' in data
    
    # Check that all items are included
    assert len(data['items']) == len(items_df)
    
    # Check that all suppliers are included
    assert len(data['suppliers']) == len(suppliers_df)
    
    # Check that costs are properly mapped
    for _, row in pricing_df.iterrows():
        item_id = row['ItemID']
        supplier_id = row['SupplierID']
        cost = row['CostPerPallet']
        assert supplier_id in data['costs'].get(item_id, {})
        assert data['costs'][item_id][supplier_id] == cost

# Test optimization model creation
def test_model_creation():
    items_df = load_item_data()
    suppliers_df = load_supplier_data()
    pricing_df = load_pricing_data()
    
    data = prepare_data_for_optimization(items_df, suppliers_df, pricing_df)
    model, x = create_optimization_model(data)
    
    assert model is not None
    assert x is not None
    
    # Check that decision variables are created for each item-supplier combination
    for item_id in data['items']:
        for supplier_id in data['available_suppliers'].get(item_id, []):
            assert (item_id, supplier_id) in x

# Test a simple optimization scenario
def test_simple_optimization():
    # Create mock data
    items_data = {
        'ItemID': [1, 2],
        'Name': ['Item A', 'Item B'],
        'MinStock': [10, 20],
        'MaxStock': [100, 200],
        'Expiry (days)': [60, 40],
        'CurrentStock': [5, 15],
        'AverageDailySale': [1, 2]
    }
    
    suppliers_data = {
        'SupplierID': [1, 2],
        'Name': ['Supplier A', 'Supplier B'],
        'MinPallets': [1, 2],
        'MaxPallets': [50, 100],
        'LeadTime (days)': [3, 5]
    }
    
    pricing_data = {
        'SupplierID': [1, 1, 2, 2],
        'ItemID': [1, 2, 1, 2],
        'CostPerPallet': [100, 120, 110, 105]
    }
    
    items_df = pd.DataFrame(items_data)
    suppliers_df = pd.DataFrame(suppliers_data)
    pricing_df = pd.DataFrame(pricing_data)
    
    data = prepare_data_for_optimization(items_df, suppliers_df, pricing_df)
    model, x = create_optimization_model(data)
    results_df, total_cost = solve_model(model, x, data)
    
    assert results_df is not None and not results_df.empty
    assert total_cost > 0
    
    # Check that minimum stock constraints are satisfied
    for item_id in data['items']:
        item_orders = results_df[results_df['ItemID'] == item_id]
        total_ordered = item_orders['UnitsOrdered'].sum() if not item_orders.empty else 0
        current_stock = data['items'][item_id]['current_stock']
        min_stock = data['items'][item_id]['min_stock']
        
        assert current_stock + total_ordered >= min_stock

# Test that the optimization respects supplier constraints
def test_supplier_constraints():
    items_df = load_item_data()
    suppliers_df = load_supplier_data()
    pricing_df = load_pricing_data()
    
    data = prepare_data_for_optimization(items_df, suppliers_df, pricing_df)
    model, x = create_optimization_model(data)
    results_df, total_cost = solve_model(model, x, data)
    
    if results_df is not None and not results_df.empty:
        # Check that supplier minimum and maximum constraints are respected
        for supplier_id in data['suppliers']:
            supplier_orders = results_df[results_df['SupplierID'] == supplier_id]
            total_pallets = supplier_orders['PalletsOrdered'].sum() if not supplier_orders.empty else 0
            
            if total_pallets > 0:  # Only check if we're using this supplier
                min_pallets = data['suppliers'][supplier_id]['min_pallets']
                max_pallets = data['suppliers'][supplier_id]['max_pallets']
                
                assert total_pallets >= min_pallets
                assert total_pallets <= max_pallets

# Test that the optimization respects stock level constraints
def test_stock_level_constraints():
    items_df = load_item_data()
    suppliers_df = load_supplier_data()
    pricing_df = load_pricing_data()
    
    data = prepare_data_for_optimization(items_df, suppliers_df, pricing_df)
    model, x = create_optimization_model(data)
    results_df, total_cost = solve_model(model, x, data)
    
    if results_df is not None and not results_df.empty:
        # Check that stock level constraints are respected
        for item_id in data['items']:
            item_orders = results_df[results_df['ItemID'] == item_id]
            total_ordered = item_orders['UnitsOrdered'].sum() if not item_orders.empty else 0
            current_stock = data['items'][item_id]['current_stock']
            min_stock = data['items'][item_id]['min_stock']
            max_stock = data['items'][item_id]['max_stock']
            
            assert current_stock + total_ordered >= min_stock
            assert current_stock + total_ordered <= max_stock

if __name__ == "__main__":
    # Run the tests
    pytest.main(["-v", __file__])
