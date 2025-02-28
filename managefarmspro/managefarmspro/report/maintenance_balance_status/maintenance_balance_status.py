# Copyright (c) 2025, Khalandar Sihan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate, add_days, add_months

def execute(filters=None):
    if not filters:
        filters = {}
    
    # Set default warning threshold if not specified
    if not filters.get("balance_threshold"):
        filters["balance_threshold"] = 20
    
    columns = get_columns()
    data = get_data(filters)
    
    # Prepare chart data
    chart = get_chart(data)
    
    return columns, data, None, chart

def get_columns():
    """Return columns for the report"""
    return [
        {
            "label": _("Plot"),
            "fieldname": "plot_name",
            "fieldtype": "Link",
            "options": "Plot",
            "width": 180
        },
        {
            "label": _("Cluster"),
            "fieldname": "cluster",
            "fieldtype": "Link",
            "options": "Cluster",
            "width": 130
        },
        {
            "label": _("Location"),
            "fieldname": "plot_location",
            "fieldtype": "Link",
            "options": "Plot Location",
            "width": 130
        },
        {
            "label": _("Customer"),
            "fieldname": "customer_name",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 180
        },
        {
            "label": _("Monthly Budget"),
            "fieldname": "monthly_maintenance_budget",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": _("Spent"),
            "fieldname": "total_spent",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": _("Balance"),
            "fieldname": "maintenance_balance",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": _("Balance %"),
            "fieldname": "balance_percentage",
            "fieldtype": "Percent",
            "width": 100
        },
        {
            "label": _("Last Activity"),
            "fieldname": "last_activity",
            "fieldtype": "Date",
            "width": 110
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100
        }
    ]

def get_data(filters):
    """Fetch and process data for the report"""
    # Build conditions based on filters
    conditions = []
    
    if filters.get("cluster"):
        conditions.append(f"p.cluster = '{filters.get('cluster')}'")
    
    if filters.get("plot_location"):
        conditions.append(f"p.plot_location = '{filters.get('plot_location')}'")
    
    if filters.get("customer"):
        conditions.append(f"p.customer_name = '{filters.get('customer')}'")
    
    # Combine all conditions with AND
    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause
    else:
        where_clause = "WHERE 1=1"  # Always true condition if no filters
    
    # Get plot data with maintenance budget info
    plots_query = f"""
        SELECT 
            p.name as plot_name,
            p.cluster,
            p.plot_location,
            p.customer_name,
            p.monthly_maintenance_budget,
            COALESCE(p.total_amount_spent, 0) as total_spent,
            COALESCE(p.maintenance_balance, p.monthly_maintenance_budget) as maintenance_balance,
            (
                SELECT MAX(w.work_date) 
                FROM `tabWork` w 
                WHERE w.plot = p.name AND w.docstatus = 1
            ) as last_activity
        FROM 
            `tabPlot` p
        {where_clause}
        AND p.monthly_maintenance_budget > 0
    """
    
    plots = frappe.db.sql(plots_query, as_dict=1)
    
    # Process data to add balance percentage and status
    result = []
    warning_threshold = flt(filters.get("balance_threshold"))
    
    for plot in plots:
        # Calculate balance percentage
        if plot.monthly_maintenance_budget > 0:
            balance_percentage = (plot.maintenance_balance / plot.monthly_maintenance_budget) * 100
        else:
            balance_percentage = 0
        
        plot.balance_percentage = flt(balance_percentage, 2)
        
        # Set warning threshold for each row for the formatter
        plot.warning_threshold = warning_threshold
        
        # Determine status based on balance
        if plot.balance_percentage < 0:
            plot.status = "Deficit"
        elif plot.balance_percentage < warning_threshold:
            plot.status = "Warning"
        else:
            plot.status = "Good"
        
        result.append(plot)
    
    # Sort data based on the selected option
    sort_option = filters.get("sort_by", "Balance %: Low to High")
    
    if sort_option == "Balance %: Low to High":
        result = sorted(result, key=lambda x: x.balance_percentage)
    elif sort_option == "Balance %: High to Low":
        result = sorted(result, key=lambda x: x.balance_percentage, reverse=True)
    elif sort_option == "Cluster":
        result = sorted(result, key=lambda x: x.cluster or "")
    elif sort_option == "Customer":
        result = sorted(result, key=lambda x: x.customer_name or "")
    elif sort_option == "Location":
        result = sorted(result, key=lambda x: x.plot_location or "")
    
    return result

def get_chart(data):
    """Generate chart data for the report"""
    if not data:
        return None
    
    # Count plots in each status category
    deficit_count = sum(1 for d in data if d.status == "Deficit")
    warning_count = sum(1 for d in data if d.status == "Warning")
    good_count = sum(1 for d in data if d.status == "Good")
    
    # Create a pie chart showing the distribution
    chart = {
        "type": "donut",
        "data": {
            "labels": [_("Deficit"), _("Warning"), _("Good")],
            "datasets": [
                {
                    "values": [deficit_count, warning_count, good_count]
                }
            ]
        },
        "colors": ["#FF5252", "#FFC107", "#4CAF50"],
        "height": 300
    }
    
    return chart

@frappe.whitelist()
def get_maintenance_status_data(cluster=None, location=None, customer=None, threshold=20):
    """API endpoint to get maintenance status data for dashboards"""
    filters = {
        "balance_threshold": threshold
    }
    
    if cluster:
        filters["cluster"] = cluster
    
    if location:
        filters["plot_location"] = location
    
    if customer:
        filters["customer"] = customer
    
    data = get_data(filters)
    
    # Prepare summary statistics
    total_plots = len(data)
    plots_in_deficit = sum(1 for d in data if d.status == "Deficit")
    plots_in_warning = sum(1 for d in data if d.status == "Warning")
    plots_in_good = sum(1 for d in data if d.status == "Good")
    
    total_budget = sum(d.monthly_maintenance_budget for d in data)
    total_spent = sum(d.total_spent for d in data)
    total_balance = sum(d.maintenance_balance for d in data)
    
    # Calculate balance percentage for the entire dataset
    overall_balance_percentage = (total_balance / total_budget * 100) if total_budget > 0 else 0
    
    return {
        "plots": {
            "total": total_plots,
            "deficit": plots_in_deficit,
            "warning": plots_in_warning,
            "good": plots_in_good
        },
        "budget": {
            "total": total_budget,
            "spent": total_spent,
            "balance": total_balance,
            "balance_percentage": overall_balance_percentage
        },
        "data": data
    }