import pulp
import pandas as pd
import numpy as np
from pathlib import Path

def create_optimization_model(data):
    # Create the model - we want to minimize cost
    model = pulp.LpProblem(name="Stock_Purchasing_Optimization", sense=pulp.LpMinimize)
    
    # xij represents the number of pallets of item i ordered from supplier j
    x = {}
    for item_id, item_data in data['items'].items():
        for supplier_id in data['available_suppliers'][item_id]:
            x[(item_id, supplier_id)] = pulp.LpVariable(
                name=f"x_{item_id}_{supplier_id}",
                lowBound=0,
                cat='Integer'  # Pallets must be whole numbers
            )
    
    # Minimize total cost
    model += pulp.lpSum(
        x[(item_id, supplier_id)] * data['costs'][item_id][supplier_id]
        for item_id in data['items']
        for supplier_id in data['available_suppliers'][item_id]
    ), "Total_Cost"
        
    # 1. Stock Constraints
    for item_id, item_data in data['items'].items():
        # Minimum stock constraint: ensure we order enough to meet minimum stock requirements
        model += (
            pulp.lpSum(
                x[(item_id, supplier_id)] * item_data['units_per_pallet']
                for supplier_id in data['available_suppliers'][item_id]
            ) + item_data['current_stock'] >= item_data['min_stock']
        ), f"Min_Stock_{item_id}"
        
        # Maximum stock constraint: ensure we don't order more than maximum stock
        model += (
            pulp.lpSum(
                x[(item_id, supplier_id)] * item_data['units_per_pallet']
                for supplier_id in data['available_suppliers'][item_id]
            ) + item_data['current_stock'] <= item_data['max_stock']
        ), f"Max_Stock_{item_id}"
    
    # 2. Supplier Constraints
    for supplier_id, supplier_data in data['suppliers'].items():
        # Get all items that can be supplied by this supplier
        items_for_supplier = [
            item_id for item_id in data['items']
            if supplier_id in data['available_suppliers'][item_id]
        ]
        
        if items_for_supplier:  
            # Minimum pallets constraint: ensure we order at least the minimum required by the supplier
            model += (
                pulp.lpSum(
                    x[(item_id, supplier_id)]
                    for item_id in items_for_supplier
                ) >= supplier_data['min_pallets']
            ), f"Min_Pallets_{supplier_id}"
            
            # Maximum pallets constraint: ensure we don't order more than the maximum allowed by the supplier
            model += (
                pulp.lpSum(
                    x[(item_id, supplier_id)]
                    for item_id in items_for_supplier
                ) <= supplier_data['max_pallets']
            ), f"Max_Pallets_{supplier_id}"
    
    # 3. Lead Time and Expiry Constraint
    for item_id, item_data in data['items'].items():
        for supplier_id in data['available_suppliers'][item_id]:
            supplier_data = data['suppliers'][supplier_id]
            lead_time = supplier_data['lead_time']
            
            # Calculate expected demand during lead time
            expected_demand_during_lead_time = item_data['average_daily_sale'] * lead_time
            
            # Current stock + ordered stock should not exceed expected demand before expiry
            model += (
                x[(item_id, supplier_id)] * item_data['units_per_pallet'] + item_data['current_stock'] 
                <= item_data['expected_demand'] + expected_demand_during_lead_time
            ), f"Lead_Time_Expiry_{item_id}_{supplier_id}"
    
    return model, x

def solve_model(model, x, data):
    # Solve the model
    solver = pulp.PULP_CBC_CMD(msg=False)
    model.solve(solver)
    
    # Check if the model was solved successfully
    if model.status != pulp.LpStatusOptimal:
        print(f"Model status: {pulp.LpStatus[model.status]}")
        if model.status == pulp.LpStatusInfeasible:
            print("The model is infeasible. Please check the constraints.")
        return None, None
    
    # Extract results
    results = []
    for item_id in data['items']:
        for supplier_id in data['available_suppliers'][item_id]:
            if (item_id, supplier_id) in x:
                pallets_ordered = x[(item_id, supplier_id)].value()
                if pallets_ordered and pallets_ordered > 0:
                    units_ordered = pallets_ordered * data['items'][item_id]['units_per_pallet']
                    cost = pallets_ordered * data['costs'][item_id][supplier_id]
                    results.append({
                        'ItemID': item_id,
                        'ItemName': data['items'][item_id]['name'],
                        'SupplierID': supplier_id,
                        'SupplierName': data['suppliers'][supplier_id]['name'],
                        'PalletsOrdered': int(pallets_ordered),
                        'UnitsOrdered': int(units_ordered),
                        'CostPerPallet': data['costs'][item_id][supplier_id],
                        'TotalCost': cost
                    })
    
    # Create a DataFrame from the results
    results_df = pd.DataFrame(results)
    
    # Calculate total cost
    total_cost = model.objective.value()
    
    return results_df, total_cost

def save_results(results_df, total_cost, output_file=None):
    if output_file is None:
        output_file = Path("optimal_purchasing_plan.csv")
    
    # Save results to CSV
    results_df.to_csv(output_file, index=False)
    print(f"Optimal purchasing plan saved to {output_file}")
    print(f"Total cost: ${total_cost:.2f}")
    
    # Display summary
    print("\nSummary of Optimal Purchasing Plan:")
    print(f"Total items to order: {len(results_df)}")
    print(f"Total pallets to order: {results_df['PalletsOrdered'].sum()}")
    print(f"Total units to order: {results_df['UnitsOrdered'].sum()}")
    
    # Group by supplier and show summary
    supplier_summary = results_df.groupby('SupplierID').agg({
        'PalletsOrdered': 'sum',
        'TotalCost': 'sum'
    }).reset_index()
    
    print("\nOrders by Supplier:")
    for _, row in supplier_summary.iterrows():
        print(f"Supplier {row['SupplierID']}: {row['PalletsOrdered']} pallets, ${row['TotalCost']:.2f}")
    
    return str(output_file)
