import pandas as pd
import numpy as np
from pathlib import Path
import os

from src.data.loader import load_item_data, load_supplier_data, load_pricing_data
from src.utils.preprocessing import prepare_data_for_optimization
from src.models.optimizer import create_optimization_model, solve_model, save_results

def main():
    # Ensure the Source directory exists and is accessible
    source_dir = Path("Source")
    if not source_dir.exists():
        print(f"Error: Source directory not found at {source_dir.absolute()}")
        return
    
    # Load data
    print("Loading data...")
    try:
        items_df = load_item_data()
        suppliers_df = load_supplier_data()
        pricing_df = load_pricing_data()
    except Exception as e:
        print(f"Error loading data: {e}")
        return
    
    # Print some basic information about the loaded data
    print(f"\nLoaded {len(items_df)} items, {len(suppliers_df)} suppliers, and {len(pricing_df)} pricing records.")
    
    # Prepare data for optimization
    print("\nPreparing data for optimization...")
    data = prepare_data_for_optimization(items_df, suppliers_df, pricing_df)
    
    # Create and solve the optimization model
    print("\nCreating optimization model...")
    model, x = create_optimization_model(data)
    
    print("Solving optimization model...")
    results_df, total_cost = solve_model(model, x, data)
    
    if results_df is not None and not results_df.empty:
        # Save results and display summary
        output_file = Path("optimal_purchasing_plan.csv")
        save_results(results_df, total_cost, output_file)
        
        # Additional analysis
        print("\nAdditional Analysis:")
        
        # Items that need to be ordered
        items_to_order = results_df['ItemID'].unique()
        print(f"Number of different items to order: {len(items_to_order)}")
        
        # Items that don't need to be ordered
        all_items = set(data['items'].keys())
        items_not_ordered = all_items - set(items_to_order)
        if items_not_ordered:
            print(f"\nItems that don't need to be ordered ({len(items_not_ordered)}):")
            for item_id in items_not_ordered:
                item_name = data['items'][item_id]['name']
                current_stock = data['items'][item_id]['current_stock']
                min_stock = data['items'][item_id]['min_stock']
                print(f"  - Item {item_id} ({item_name}): Current stock = {current_stock}, Min stock = {min_stock}")
        
        # Suppliers used
        suppliers_used = results_df['SupplierID'].unique()
        print(f"\nNumber of suppliers used: {len(suppliers_used)} out of {len(data['suppliers'])}")
        
    else:
        print("Failed to find an optimal solution.")

if __name__ == "__main__":
    main()
