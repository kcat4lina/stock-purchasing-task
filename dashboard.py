import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os

from src.data.loader import load_item_data, load_supplier_data, load_pricing_data
from src.utils.preprocessing import prepare_data_for_optimization
from src.models.optimizer import create_optimization_model, solve_model

st.set_page_config(
    page_title="Stock Purchasing Optimizer",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        border: none;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #45a049;
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }
    .optimization-result {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-top: 20px;
    }
    .metric-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1E88E5;
    }
    .metric-label {
        font-size: 14px;
        color: #616161;
    }
    .table-container {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-top: 10px;
    }
    .section-title {
        font-size: 20px;
        font-weight: bold;
        color: #333;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📦 Stock Purchasing Optimizer")
st.markdown("""
This dashboard helps you optimize your stock purchasing decisions. 
View your current inventory, supplier information, and pricing data, then run the optimization to get the most cost-effective purchasing plan.
""")

@st.cache_data
def load_all_data():
    try:
        items_df = load_item_data()
        suppliers_df = load_supplier_data()
        pricing_df = load_pricing_data()
        return items_df, suppliers_df, pricing_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None

items_df, suppliers_df, pricing_df = load_all_data()

st.header("Source Data")

tab1, tab2, tab3 = st.tabs(["Items", "Suppliers", "Pricing"])

with tab1:
    st.markdown('<div class="section-title">Item Inventory Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="table-container">', unsafe_allow_html=True)
    st.dataframe(items_df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">Current Stock vs Min/Max Stock Levels</div>', unsafe_allow_html=True)
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=items_df['Name'],
        y=items_df['CurrentStock'],
        name='Current Stock',
        marker_color='#4CAF50'
    ))
    
    fig.add_trace(go.Scatter(
        x=items_df['Name'],
        y=items_df['MinStock'],
        mode='lines',
        name='Min Stock',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=items_df['Name'],
        y=items_df['MaxStock'],
        mode='lines',
        name='Max Stock',
        line=dict(color='blue', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title='',
        xaxis_title='Item',
        yaxis_title='Stock Level',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown('<div class="section-title">Supplier Information</div>', unsafe_allow_html=True)
    st.markdown('<div class="table-container">', unsafe_allow_html=True)
    st.dataframe(suppliers_df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">Supplier Capacity (Min/Max Pallets)</div>', unsafe_allow_html=True)
    fig = go.Figure()
    
    for i, supplier in suppliers_df.iterrows():
        fig.add_trace(go.Bar(
            x=[supplier['Name']],
            y=[supplier['MaxPallets']],
            name=f"{supplier['Name']} Max",
            marker_color='#1E88E5',
            width=0.4,
            offset=-0.2
        ))
        
        fig.add_trace(go.Bar(
            x=[supplier['Name']],
            y=[supplier['MinPallets']],
            name=f"{supplier['Name']} Min",
            marker_color='#FFC107',
            width=0.4,
            offset=0.2
        ))
    
    fig.update_layout(
        barmode='group',
        title='',
        xaxis_title='Supplier',
        yaxis_title='Pallets',
        template='plotly_white',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('<div class="section-title">Supplier Lead Time (Days)</div>', unsafe_allow_html=True)
    fig = px.bar(
        suppliers_df, 
        x='Name', 
        y='LeadTime (days)',
        color='LeadTime (days)',
        color_continuous_scale='Viridis',
        labels={'Name': 'Supplier', 'LeadTime (days)': 'Lead Time (Days)'}
    )
    
    fig.update_layout(
        title='',
        template='plotly_white',
        coloraxis_showscale=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown('<div class="section-title">Pricing Information</div>', unsafe_allow_html=True)
    st.markdown('<div class="table-container">', unsafe_allow_html=True)
    st.dataframe(pricing_df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    pricing_with_names = pricing_df.merge(
        items_df[['ItemID', 'Name']], 
        on='ItemID'
    ).merge(
        suppliers_df[['SupplierID', 'Name']], 
        on='SupplierID',
        suffixes=('_Item', '_Supplier')
    )
    
    st.markdown('<div class="section-title">Cost Per Pallet by Supplier and Item</div>', unsafe_allow_html=True)
    
    pivot_df = pricing_with_names.pivot(
        index='Name_Supplier', 
        columns='Name_Item', 
        values='CostPerPallet'
    )
    
    fig = px.imshow(
        pivot_df,
        labels=dict(x="Item", y="Supplier", color="Cost Per Pallet"),
        x=pivot_df.columns,
        y=pivot_df.index,
        color_continuous_scale='Viridis',
        aspect="auto"
    )
    
    fig.update_layout(
        title='',
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.header("Optimization")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{len(items_df)}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Total Items</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    below_min = len(items_df[items_df['CurrentStock'] < items_df['MinStock']])
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{below_min}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Items Below Min Stock</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    total_current_stock = items_df['CurrentStock'].sum()
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{total_current_stock}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Total Current Stock</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    total_min_stock = items_df['MinStock'].sum()
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{total_min_stock}</div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Total Min Stock Required</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
optimize_button = st.button("🚀 Run Optimization", use_container_width=True)

results_container = st.container()

if optimize_button:
    with st.spinner('Optimizing your stock purchasing plan...'):
        data = prepare_data_for_optimization(items_df, suppliers_df, pricing_df)
        
        progress_bar = st.progress(0)
        
        for i in range(101):
            progress_bar.progress(i)
            time.sleep(0.02)
        
        model, x = create_optimization_model(data)
        results_df, total_cost = solve_model(model, x, data)
        
        progress_bar.empty()
        
        with results_container:
            if results_df is not None and not results_df.empty:
                st.markdown('<div class="optimization-result">', unsafe_allow_html=True)
                st.subheader("✅ Optimization Complete!")
                
                results_with_names = results_df.copy()
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">${total_cost:,.2f}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Total Cost</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    total_pallets = results_df['PalletsOrdered'].sum()
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{total_pallets}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Total Pallets</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    total_units = results_df['UnitsOrdered'].sum()
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{total_units}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Total Units</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col4:
                    suppliers_used = len(results_df['SupplierID'].unique())
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-value">{suppliers_used}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="metric-label">Suppliers Used</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                viz_tab1, viz_tab2, viz_tab3 = st.tabs(["Order Summary", "By Supplier", "By Item"])
                
                with viz_tab1:
                    st.markdown('<div class="section-title">Optimal Purchasing Plan</div>', unsafe_allow_html=True)
                    st.markdown('<div class="table-container">', unsafe_allow_html=True)
                    st.dataframe(results_df, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="section-title">Cost Distribution</div>', unsafe_allow_html=True)
                    fig = px.pie(
                        results_df, 
                        values='TotalCost', 
                        names='ItemName',
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    
                    fig.update_layout(
                        title='',
                        template='plotly_white'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                with viz_tab2:
                    st.markdown('<div class="section-title">Orders by Supplier</div>', unsafe_allow_html=True)
                    
                    supplier_summary = results_df.groupby('SupplierName').agg({
                        'PalletsOrdered': 'sum',
                        'UnitsOrdered': 'sum',
                        'TotalCost': 'sum'
                    }).reset_index()
                    
                    st.markdown('<div class="table-container">', unsafe_allow_html=True)
                    st.dataframe(supplier_summary, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown('<div class="section-title">Pallets by Supplier</div>', unsafe_allow_html=True)
                        fig = px.bar(
                            supplier_summary,
                            x='SupplierName',
                            y='PalletsOrdered',
                            color='PalletsOrdered',
                            color_continuous_scale='Viridis',
                            labels={'SupplierName': 'Supplier', 'PalletsOrdered': 'Pallets Ordered'}
                        )
                        
                        fig.update_layout(
                            title='',
                            template='plotly_white',
                            coloraxis_showscale=False
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.markdown('<div class="section-title">Cost by Supplier</div>', unsafe_allow_html=True)
                        fig = px.bar(
                            supplier_summary,
                            x='SupplierName',
                            y='TotalCost',
                            color='TotalCost',
                            color_continuous_scale='Viridis',
                            labels={'SupplierName': 'Supplier', 'TotalCost': 'Total Cost ($)'}
                        )
                        
                        fig.update_layout(
                            title='',
                            template='plotly_white',
                            coloraxis_showscale=False
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                with viz_tab3:
                    st.markdown('<div class="section-title">Orders by Item</div>', unsafe_allow_html=True)
                    
                    item_summary = results_df.groupby('ItemName').agg({
                        'PalletsOrdered': 'sum',
                        'UnitsOrdered': 'sum',
                        'TotalCost': 'sum'
                    }).reset_index()
                    
                    st.markdown('<div class="table-container">', unsafe_allow_html=True)
                    st.dataframe(item_summary, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown('<div class="section-title">Units by Item</div>', unsafe_allow_html=True)
                        fig = px.bar(
                            item_summary,
                            x='ItemName',
                            y='UnitsOrdered',
                            color='UnitsOrdered',
                            color_continuous_scale='Viridis',
                            labels={'ItemName': 'Item', 'UnitsOrdered': 'Units Ordered'}
                        )
                        
                        fig.update_layout(
                            title='',
                            template='plotly_white',
                            coloraxis_showscale=False
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.markdown('<div class="section-title">Cost by Item</div>', unsafe_allow_html=True)
                        fig = px.bar(
                            item_summary,
                            x='ItemName',
                            y='TotalCost',
                            color='TotalCost',
                            color_continuous_scale='Viridis',
                            labels={'ItemName': 'Item', 'TotalCost': 'Total Cost ($)'}
                        )
                        
                        fig.update_layout(
                            title='',
                            template='plotly_white',
                            coloraxis_showscale=False
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                # Stock level comparison (before and after optimization)
                st.markdown('<div class="section-title">Stock Level Comparison (Before vs After Optimization)</div>', unsafe_allow_html=True)
                
                # Create a dataframe with before and after stock levels
                stock_comparison = pd.DataFrame()
                stock_comparison['ItemID'] = items_df['ItemID']
                stock_comparison['ItemName'] = items_df['Name']
                stock_comparison['BeforeStock'] = items_df['CurrentStock']
                
                # Calculate after stock by adding ordered units to current stock
                after_stock = items_df['CurrentStock'].copy()
                for _, row in results_df.iterrows():
                    item_id = row['ItemID']
                    units_ordered = row['UnitsOrdered']
                    idx = stock_comparison[stock_comparison['ItemID'] == item_id].index
                    if len(idx) > 0:
                        after_stock.iloc[idx[0]] += units_ordered
                
                stock_comparison['AfterStock'] = after_stock
                stock_comparison['MinStock'] = items_df['MinStock']
                stock_comparison['MaxStock'] = items_df['MaxStock']
                
                # Create a bar chart comparing before and after stock levels
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=stock_comparison['ItemName'],
                    y=stock_comparison['BeforeStock'],
                    name='Before Optimization',
                    marker_color='#FFC107'
                ))
                
                fig.add_trace(go.Bar(
                    x=stock_comparison['ItemName'],
                    y=stock_comparison['AfterStock'],
                    name='After Optimization',
                    marker_color='#4CAF50'
                ))
                
                fig.add_trace(go.Scatter(
                    x=stock_comparison['ItemName'],
                    y=stock_comparison['MinStock'],
                    mode='lines',
                    name='Min Stock',
                    line=dict(color='red', width=2, dash='dash')
                ))
                
                fig.add_trace(go.Scatter(
                    x=stock_comparison['ItemName'],
                    y=stock_comparison['MaxStock'],
                    mode='lines',
                    name='Max Stock',
                    line=dict(color='blue', width=2, dash='dash')
                ))
                
                fig.update_layout(
                    barmode='group',
                    title='',
                    xaxis_title='Item',
                    yaxis_title='Stock Level',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    template='plotly_white'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Download button for the results
                csv = results_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Optimization Results",
                    data=csv,
                    file_name="optimal_purchasing_plan.csv",
                    mime="text/csv",
                    key="download-csv"
                )
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error("Failed to find an optimal solution. Please check the constraints and try again.")

