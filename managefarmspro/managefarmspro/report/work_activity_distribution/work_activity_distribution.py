# Copyright (c) 2025, Khalandar Sihan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, add_months

def execute(filters=None):
    if not filters:
        filters = {}
        
    columns = get_columns()
    data, chart_data = get_data(filters)
    
    return columns, data, None, chart_data

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
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql("""
        SELECT 
            work_name,
            COUNT(*) as work_count,
            SUM(total_cost) as total_cost
        FROM 
            `tabWork`
        WHERE
            docstatus = 1
            {conditions}
        GROUP BY 
            work_name
        ORDER BY 
            work_count DESC
    """.format(conditions=conditions), filters, as_dict=1)
    
    # Calculate totals for percentage
    total_works = sum([d.work_count for d in data])
    
    # Calculate percentages and averages
    for d in data:
        d.percentage = (d.work_count / total_works * 100) if total_works else 0
        d.avg_cost = d.total_cost / d.work_count if d.work_count else 0
    
    # Prepare chart data
    chart = {
        "type": "pie",
        "data": {
            "labels": [d.work_name for d in data],
            "datasets": [
                {"values": [d.work_count for d in data]}
            ]
        },
        "colors": [
            '#FF5733', '#33FF57', '#3357FF', '#F3FF33',
            '#FF33F3', '#33FFF3', '#FF8033', '#8033FF'
        ][:len(data)],
        "height": 300
    }
    
    return data, chart

def get_conditions(filters):
    conditions = []
    
    if filters.get("from_date") and filters.get("to_date"):
        conditions.append(" AND work_date BETWEEN %(from_date)s AND %(to_date)s")
    
    if filters.get("cluster"):
        # This will need a join with Plot to get the cluster
        conditions.append(" AND plot IN (SELECT name FROM `tabPlot` WHERE cluster = %(cluster)s)")
    
    if filters.get("plot"):
        conditions.append(" AND plot = %(plot)s")
    
    return " ".join(conditions)