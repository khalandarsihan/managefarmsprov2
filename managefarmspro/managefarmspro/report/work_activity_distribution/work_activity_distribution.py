# Copyright (c) 2025, Khalandar Sihan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.utils import getdate, add_months, nowdate, get_first_day, get_last_day

def execute(filters=None):
    if not filters:
        filters = {}
        
    # Set default filters if not specified
    if not filters.get("from_date"):
        filters["from_date"] = add_months(nowdate(), -12)  # Default to last 12 months
    if not filters.get("to_date"):
        filters["to_date"] = nowdate()
        
    columns = get_columns()
    data = get_data(filters)
    
    # Prepare chart data
    chart = get_chart(data, filters)
    
    return columns, data, None, chart

def get_columns():
    return [
        {
            "fieldname": "work_name",
            "label": _("Work Type"),
            "fieldtype": "Link",
            "options": "Work Item",
            "width": 280
        },
        {
            "fieldname": "work_count",
            "label": _("Count"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "percentage",
            "label": _("Percentage"),
            "fieldtype": "Percent",
            "width": 100
        },
        {
            "fieldname": "total_cost",
            "label": _("Total Cost"),
            "fieldtype": "Currency",
            "width": 220
        },
        {
            "fieldname": "avg_cost",
            "label": _("Average Cost"),
            "fieldtype": "Currency",
            "width": 220
        },
        {
            "fieldname": "labour_cost",
            "label": _("Labor Cost"),
            "fieldtype": "Currency",
            "width": 220
        },
        {
            "fieldname": "material_cost",
            "label": _("Material Cost"),
            "fieldtype": "Currency",
            "width": 220
        },
        {
            "fieldname": "equipment_cost",
            "label": _("Equipment Cost"),
            "fieldtype": "Currency",
            "width": 220
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    # Get a list of all work entries that match the conditions
    works = frappe.db.sql("""
        SELECT 
            name,
            work_name,
            plot,
            total_cost,
            work_date
        FROM 
            `tabWork`
        WHERE
            docstatus = 1
            {conditions}
        ORDER BY 
            work_date
    """.format(conditions=conditions), filters, as_dict=1)
    
    # Group works by work_name
    work_groups = {}
    
    for work in works:
        work_name = work.work_name
        if work_name not in work_groups:
            work_groups[work_name] = {
                "work_name": work_name,
                "work_count": 0,
                "total_cost": 0,
                "labour_cost": 0,
                "material_cost": 0,
                "equipment_cost": 0,
                "works": []
            }
        
        # Add to the group
        work_groups[work_name]["work_count"] += 1
        work_groups[work_name]["total_cost"] += work.total_cost
        work_groups[work_name]["works"].append(work.name)
    
    # Get cost breakdown for each work
    for work_name, group in work_groups.items():
        for work_id in group["works"]:
            labour, material, equipment = get_cost_breakdown(work_id)
            group["labour_cost"] += labour
            group["material_cost"] += material
            group["equipment_cost"] += equipment
    
    # Convert to list
    result = list(work_groups.values())
    
    # Calculate totals for percentage
    total_works = sum([d["work_count"] for d in result])
    
    # Calculate percentages and averages, remove the works list
    for d in result:
        d["percentage"] = (d["work_count"] / total_works * 100) if total_works else 0
        d["avg_cost"] = d["total_cost"] / d["work_count"] if d["work_count"] else 0
        
        # Round to 2 decimal places
        d["percentage"] = round(d["percentage"], 2)
        d["avg_cost"] = round(d["avg_cost"], 2)
        
        # Remove the works list 
        d.pop("works", None)
    
    # Sort by work count (descending)
    result.sort(key=lambda x: x["work_count"], reverse=True)
    
    # Apply minimum count filter if present
    if filters.get("min_count"):
        min_count = filters.get("min_count")
        result = [d for d in result if d["work_count"] >= min_count]
    
    return result

def get_cost_breakdown(work_name):
    """Get the cost breakdown for a specific work"""
    labor_cost = frappe.db.sql("""
        SELECT COALESCE(SUM(total_price), 0) as cost
        FROM `tabLabor Child`
        WHERE parent = %s
    """, work_name, as_dict=1)[0].cost
    
    material_cost = frappe.db.sql("""
        SELECT COALESCE(SUM(total_price), 0) as cost
        FROM `tabMaterial Child`
        WHERE parent = %s
    """, work_name, as_dict=1)[0].cost
    
    equipment_cost = frappe.db.sql("""
        SELECT COALESCE(SUM(total_price), 0) as cost
        FROM `tabEquipment Child`
        WHERE parent = %s
    """, work_name, as_dict=1)[0].cost
    
    return labor_cost, material_cost, equipment_cost

def get_chart(data, filters):
    """Generate chart data for the report"""
    if not data:
        return None
    
    # Get chart type from filters
    chart_type = filters.get("chart_type", "Pie").lower()
    if chart_type == "percentage":
        chart_type = "pie"  # Handle percentage as pie
    
    labels = []
    values = []
    colors = [
        '#FF5733', '#33FF57', '#3357FF', '#F3FF33',
        '#FF33F3', '#33FFF3', '#FF8033', '#8033FF',
        '#5733FF', '#33FFF3', '#FFAF33', '#33FFAF'
    ]
    
    # Sort data by count (descending)
    sorted_data = sorted(data, key=lambda x: x["work_count"], reverse=True)
    
    # Get top 10 if there are more than 10 activities
    chart_data = sorted_data[:10] if len(sorted_data) > 10 else sorted_data
    
    for entry in chart_data:
        labels.append(entry["work_name"])
        values.append(entry["work_count"])
    
    # Basic chart configuration
    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Count", "values": values}
            ]
        },
        "type": chart_type,
        "colors": colors[:len(chart_data)],
        "height": 300
    }
    
    return chart

def get_conditions(filters):
    conditions = []
    
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append(" AND work_date BETWEEN %(from_date)s AND %(to_date)s")
    
    if filters.get("cluster"):
        # This will need a join with Plot to get the cluster
        conditions.append(" AND plot IN (SELECT name FROM `tabPlot` WHERE cluster = %(cluster)s)")
    
    if filters.get("plot"):
        conditions.append(" AND plot = %(plot)s")
        
    if filters.get("customer"):
        conditions.append(" AND customer = %(customer)s")
    
    return " ".join(conditions)

@frappe.whitelist()
def get_chart_data(filters):
    """API endpoint to get chart data for the dashboard"""
    if isinstance(filters, str):
        filters = json.loads(filters)
    
    data = get_data(filters)
    return get_chart(data, filters)