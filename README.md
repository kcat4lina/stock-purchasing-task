⸻

📈 Stock Purchasing Optimization

🧠 Problem Overview

This project implements a mixed-integer linear programming (MILP) solution to optimize stock purchases. The goal is to minimize total cost while ensuring:
	•	Minimum/maximum stock levels are respected
	•	Supplier constraints are satisfied
	•	Perishability and lead times are considered

⸻

🔍 My Approach

1. 🗂️ Data Processing and Preparation

Data is loaded from the following CSV files:
	•	items_updated.csv — Info about each item:
ID, Name, Min/Max Stock, Expiry Days, Current Stock, Avg Daily Sales
	•	suppliers.csv — Info about suppliers:
ID, Name, Min/Max Pallets, Lead Time
	•	pricing.csv — Cost per pallet for each item-supplier pair

🛠 Preprocessing includes:
	•	Calculating expected demand
	•	Structuring data for optimization
	•	Mapping supplier-item relationships
	•	Storing cost data efficiently

⸻

2. 📐 Mathematical Optimization Model

Formulated using PuLP, a Python linear programming library.

🧩 Decision Variables

x[(item_id, supplier_id)]  # Number of pallets of item from supplier

🎯 Objective Function

Minimize total cost:

$$
\min Z = \sum_{i \in I} \sum_{j \in S(i)} c(i, j) \cdot x(i, j)
$$

Where:
	•	I = set of items
	•	S(i) = suppliers for item i
	•	c(i, j) = cost per pallet of item i from supplier j
	•	x(i, j) = pallets ordered of item i from supplier j

⸻

✅ Constraints

📦 Stock Level:
	•	Minimum stock:
$$
\sum_{j \in S(i)} x(i,j) \cdot u + \text{current_stock}(i) \geq \text{min_stock}(i)
$$
	•	Maximum stock:
$$
\sum_{j \in S(i)} x(i,j) \cdot u + \text{current_stock}(i) \leq \text{max_stock}(i)
$$

Where u = units per pallet.

⸻

🚚 Supplier Capacity:
	•	Minimum order:
$$
\sum_{i \in I(j)} x(i,j) \geq \text{min_pallets}(j)
$$
	•	Maximum order:
$$
\sum_{i \in I(j)} x(i,j) \leq \text{max_pallets}(j)
$$

⸻

⏳ Lead Time + Expiry:

Avoid over-ordering perishable items:

$$
x(i,j) \cdot u + \text{current_stock}(i) \leq \text{expected_demand}(i) + \text{expected_demand_during_lead_time}(i, j)
$$

⸻

🔒 Variable Type:

x(i,j) >= 0 and Integer



⸻

🔎 Logic Behind the Math

Constraint Type	Why It’s Needed
Cost Objective	Minimizes total cost over all supplier-item pairs
Stock Bounds	Avoids understocking or overstocking
Supplier Rules	Respects supplier order minimums and capacity limits
Expiry Handling	Prevents ordering more than what can be sold before expiry + lead time window
Unit Conversion	Handles pallets vs individual unit constraints (e.g., 1 pallet = 24 units)



⸻

3. 🧮 Solution & Output

Once solved, the model:
	•	Extracts optimal order quantities
	•	Calculates total cost
	•	Saves results to a CSV report

🧾 Output Includes:

Field	Description
ItemID, ItemName	The item being ordered
SupplierID, Name	Supplier details
PalletsOrdered	Optimal quantity to order
UnitsOrdered	Converted from pallets
CostPerPallet	Unit cost
TotalCost	Total cost for the order



⸻

4. 🧱 Code Structure

project_root/
├── src/                     
│   ├── data/                # Data loading modules
│   ├── utils/               # Utility functions
│   └── models/              # Optimization model
├── Source/                  # Input data directory
├── main.py                  # Main script
└── optimal_purchasing_plan.csv  # Output file

Designed with:
	•	Modularity
	•	Error Handling
	•	Descriptive Docstrings
	•	Consistent Naming

⸻

⚠️ Key Challenges & Solutions

Challenge	Solution
Data Integration	Careful ID mapping and schema validation
Constraint Translation	Unit conversion and perishable constraints handled with precision
Solver Performance	Efficient problem formulation using MILP for real-world scale problems



⸻

🚀 How to Run
	1.	Install required packages (requirements.txt):

pip install pandas numpy pulp

	2.	Additional required packages (dashboard data visualization):

pip install streamlit plotly

	3.	Run the tests:

python run_tests.py
python3 run_tests.py

Before running the app, you can engage run_tests.py for testing that everything works as expected (loading data correctly, and generating the report for example). See /tests/test_optimizer.py

	4.	Run the main script:

python main.py
python3 main.py

	5.	Or run dashboard.py for dashboard visualization:

streamlit run dashboard.py

	6.	Results saved to:

optimal_purchasing_plan.csv



⸻
