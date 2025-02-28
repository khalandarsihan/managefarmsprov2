# Copyright (c) 2025, Khalandar Sihan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.utils import getdate, add_months, nowdate, flt, get_first_day, get_last_day, formatdate
from datetime import datetime

def execute(filters=None):
    if not filters:
        filters = {}
        
    # Set default filters if not specified
    if not filters.get("from_date"):
        filters["from_date"] = add_months(nowdate(), -12)  # Default to last 12 months
    if not filters.get("to_date"):
        filters["to_date"] = nowdate()
        
    columns = get_columns(filters)
    data = get_data(filters)
    
    # Prepare chart data
    chart = get_chart(data, filters)
    
    return columns, data, None, chart

def get_columns(filters):
    group_by = filters.get("group_by", "Month")
    
    columns = [
        {
            "fieldname": group_by.lower(),
            "label": _(group_by),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "total_cost",
            "label": _("Total Cost"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "labor_cost",
            "label": _("Labor Cost"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "labor_percentage",
            "label": _("Labor %"),
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "fieldname": "material_cost",
            "label": _("Material Cost"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "material_percentage",
            "label": _("Material %"),
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "fieldname": "equipment_cost",
            "label": _("Equipment Cost"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "equipment_percentage",
            "label": _("Equipment %"),
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "fieldname": "supervision_cost",
            "label": _("Supervision Cost"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "supervision_percentage",
            "label": _("Supervision %"),
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "fieldname": "work_count",
            "label": _("# of Works"),
            "fieldtype": "Int",
            "width": 120
        }
    ]
    
    return columns

def get_data(filters):
    conditions = get_conditions(filters)
    group_by = filters.get("group_by", "Month")
    
    # First, get all works that match the conditions
    works = frappe.db.sql("""
        SELECT 
            name,
            work_name,
            plot,
            total_cost,
            work_date,
            COALESCE(
                supervision_charges, 
                (SELECT supervision_charges FROM `tabPlot` WHERE name = `tabWork`.plot), 
                0
            ) as supervision_charges
        FROM 
            `tabWork`
        WHERE
            docstatus = 1
            {conditions}
        ORDER BY 
            work_date
    """.format(conditions=conditions), filters, as_dict=1)
    
    # Define the grouping function based on the selected group_by option
    def get_group_key(work):
        if group_by == "Month":
            # Format: "Jan 2025"
            return getdate(work.work_date).strftime("%b %Y")
        elif group_by == "Quarter":
            # Format: "Q1 2025"
            date = getdate(work.work_date)
            quarter = ((date.month - 1) // 3) + 1
            return f"Q{quarter} {date.year}"
        elif group_by == "Year":
            # Format: "2025"
            return str(getdate(work.work_date).year)
        elif group_by == "Work Type":
            # Return the work type
            return work.work_name
        elif group_by == "Plot":
            # Return the plot
            return work.plot
        elif group_by == "Cluster":
            # Get the cluster for the plot
            plot_info = frappe.db.get_value("Plot", work.plot, "cluster", as_dict=1)
            return plot_info.cluster if plot_info else "Unknown"
        else:
            # Default to Month
            return getdate(work.work_date).strftime("%b %Y")
    
    # Group works based on the selected criteria
    grouped_data = {}
    
    for work in works:
        group_key = get_group_key(work)
        
        if group_key not in grouped_data:
            grouped_data[group_key] = {
                group_by.lower(): group_key,
                "total_cost": 0,
                "labor_cost": 0,
                "material_cost": 0,
                "equipment_cost": 0,
                "supervision_cost": 0,
                "work_count": 0,
                "sort_key": work.work_date if group_by in ["Month", "Quarter", "Year"] else group_key
            }
        
        # Get cost breakdown for this work
        labor_cost, material_cost, equipment_cost = get_cost_breakdown(work.name)
        
        # Calculate supervision cost
        try:
            supervision_percentage = float(work.supervision_charges or 0)
        except (ValueError, TypeError):
            supervision_percentage = 0
            
        supervision_cost = (work.total_cost * supervision_percentage) / 100
        supervision_cost = round(supervision_cost, 2)
        
        # Add to group totals
        grouped_data[group_key]["total_cost"] += work.total_cost
        grouped_data[group_key]["labor_cost"] += labor_cost
        grouped_data[group_key]["material_cost"] += material_cost
        grouped_data[group_key]["equipment_cost"] += equipment_cost
        grouped_data[group_key]["supervision_cost"] += supervision_cost
        grouped_data[group_key]["work_count"] += 1
    
    # Convert to list and calculate percentages
    result = []
    for key, data in grouped_data.items():
        # Calculate percentages for resource distribution
        total = data["total_cost"]
        if total > 0:
            data["labor_percentage"] = round((data["labor_cost"] / total) * 100, 2)
            data["material_percentage"] = round((data["material_cost"] / total) * 100, 2)
            data["equipment_percentage"] = round((data["equipment_cost"] / total) * 100, 2)
            data["supervision_percentage"] = round((data["supervision_cost"] / total) * 100, 2)
        else:
            data["labor_percentage"] = 0
            data["material_percentage"] = 0
            data["equipment_percentage"] = 0
            data["supervision_percentage"] = 0
        
        result.append(data)
    
    # Sort the result based on group_by
    if group_by in ["Month", "Quarter", "Year"]:
        # For time-based grouping, sort by date
        result.sort(key=lambda x: x["sort_key"])
    else:
        # For other groupings, sort by total_cost (descending)
        result.sort(key=lambda x: x["total_cost"], reverse=True)
    
    # Remove the sort key from the final output
    for entry in result:
        if "sort_key" in entry:
            del entry["sort_key"]
    
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
    
    chart_type = filters.get("chart_type", "Stacked").lower()
    if chart_type == "percentage":
        chart_type = "pie"
    
    # Get the group_by field
    group_by = filters.get("group_by", "Month").lower()
    
    labels = []
    labor_values = []
    material_values = []
    equipment_values = []
    supervision_values = []
    
    for entry in data:
        labels.append(entry[group_by])
        labor_values.append(entry["labor_cost"])
        material_values.append(entry["material_cost"])
        equipment_values.append(entry["equipment_cost"])
        supervision_values.append(entry["supervision_cost"])
    
    # If it's a pie chart, we want to show the overall distribution rather than per group
    if chart_type == "pie":
        # Calculate totals
        total_labor = sum(labor_values)
        total_material = sum(material_values)
        total_equipment = sum(equipment_values)
        total_supervision = sum(supervision_values)
        
        # Create a simple pie chart of overall resource distribution
        chart = {
            "data": {
                "labels": ["Labor", "Material", "Equipment", "Supervision"],
                "datasets": [{
                    "values": [total_labor, total_material, total_equipment, total_supervision]
                }]
            },
            "type": "pie",
            "colors": ["#5EC962", "#7B6CFF", "#FFA00A", "#00BCD4"],
            "height": 300
        }
    else:
        # For bar, line, or stacked chart
        datasets = []
        chart_colors = ["#5EC962", "#7B6CFF", "#FFA00A", "#00BCD4"]
        
        # Determine if we should use stacked bar
        is_stacked = (chart_type == "stacked")
        
        # Use the appropriate chart type
        actual_chart_type = "bar" if chart_type in ["bar", "stacked"] else chart_type
        
        # Create datasets based on chart type
        datasets = [
            {"name": "Labor", "values": labor_values},
            {"name": "Material", "values": material_values},
            {"name": "Equipment", "values": equipment_values},
            {"name": "Supervision", "values": supervision_values}
        ]
        
        chart = {
            "data": {
                "labels": labels,
                "datasets": datasets
            },
            "type": actual_chart_type,
            "colors": chart_colors,
            "height": 300
        }
        
        # Add stacked property if needed
        if is_stacked:
            chart["stacked"] = 1
    
    return chart

def get_conditions(filters):
    """Build the WHERE clause conditions based on filters"""
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
        
    if filters.get("work_name"):
        conditions.append(" AND work_name = %(work_name)s")
    
    return " ".join(conditions)

@frappe.whitelist()
def get_resource_summary(filters):
    """API endpoint to get resource summary data for dashboards"""
    if isinstance(filters, str):
        filters = json.loads(filters)
    
    data = get_data(filters)
    
    # Calculate totals across all groups
    total_cost = sum(d["total_cost"] for d in data)
    labor_cost = sum(d["labor_cost"] for d in data)
    material_cost = sum(d["material_cost"] for d in data)
    equipment_cost = sum(d["equipment_cost"] for d in data)
    supervision_cost = sum(d["supervision_cost"] for d in data)
    
    # Calculate percentages
    labor_percentage = round((labor_cost / total_cost * 100), 2) if total_cost else 0
    material_percentage = round((material_cost / total_cost * 100), 2) if total_cost else 0
    equipment_percentage = round((equipment_cost / total_cost * 100), 2) if total_cost else 0
    supervision_percentage = round((supervision_cost / total_cost * 100), 2) if total_cost else 0
    
    return {
        "total_cost": total_cost,
        "labor": {"cost": labor_cost, "percentage": labor_percentage},
        "material": {"cost": material_cost, "percentage": material_percentage},
        "equipment": {"cost": equipment_cost, "percentage": equipment_percentage},
        "supervision": {"cost": supervision_cost, "percentage": supervision_percentage}
    }