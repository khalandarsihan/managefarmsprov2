# Copyright (c) 2025, Khalandar Sihan and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe

def execute(filters=None):
    if not filters:
        filters = {}
    
    columns = [
        {"label": "Plot", "fieldname": "plot_name", "fieldtype": "Link", "options": "Plot", "width": 280},
        {"label": "Cluster", "fieldname": "cluster", "fieldtype": "Link", "options": "Cluster", "width": 120},
        {"label": "Location", "fieldname": "plot_location", "fieldtype": "Link", "options": "Plot Location", "width": 120},
        {"label": "Budget", "fieldname": "monthly_maintenance_budget", "fieldtype": "Currency", "width": 120},
        {"label": "Spent", "fieldname": "total_amount_spent", "fieldtype": "Currency", "width": 120},
        {"label": "Balance", "fieldname": "balance", "fieldtype": "Currency", "width": 120}
    ]
    
    # Build where conditions based on filters
    conditions = "monthly_maintenance_budget > 0"
    
    if filters.get("cluster"):
        conditions += f" AND cluster = '{filters.get('cluster')}'"
    
    if filters.get("plot_location"):
        conditions += f" AND plot_location = '{filters.get('plot_location')}'"
    
    # Handle sorting
    sort_field = "monthly_maintenance_budget"
    sort_order = "DESC"
    
    if filters.get("sort_by"):
        sort_option = filters.get("sort_by")
        
        if sort_option == "Budget: High to Low":
            sort_field = "monthly_maintenance_budget"
            sort_order = "DESC"
        elif sort_option == "Budget: Low to High":
            sort_field = "monthly_maintenance_budget"
            sort_order = "ASC"
        elif sort_option == "Spent: High to Low":
            sort_field = "total_amount_spent"
            sort_order = "DESC"
        elif sort_option == "Spent: Low to High":
            sort_field = "total_amount_spent"
            sort_order = "ASC"
        elif sort_option == "Balance: High to Low":
            sort_field = "balance"
            sort_order = "DESC"
        elif sort_option == "Balance: Low to High":
            sort_field = "balance"
            sort_order = "ASC"
    
    # Handle limit
    limit = filters.get("limit") or 10
    
    query = f"""
        SELECT 
            plot_name, 
            cluster,
            plot_location,
            monthly_maintenance_budget, 
            total_amount_spent,
            (monthly_maintenance_budget - total_amount_spent) as balance
        FROM 
            `tabPlot` 
        WHERE 
            {conditions}
        ORDER BY 
            {sort_field} {sort_order}
        LIMIT {limit}
    """
    
    data = frappe.db.sql(query, as_dict=1)
    
    chart = {
        "type": "bar",
        "data": {
            "labels": [d.plot_name for d in data],
            "datasets": [
                {"name": "Budget", "values": [d.monthly_maintenance_budget for d in data]},
                {"name": "Spent", "values": [d.total_amount_spent for d in data]}
            ]
        },
        "colors": ["#4CAF50", "#FF5722"]
    }
    
    return columns, data, "Plot Budget Comparison", chart