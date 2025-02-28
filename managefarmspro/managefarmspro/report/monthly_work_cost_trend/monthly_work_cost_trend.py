# Copyright (c) 2025, Khalandar Sihan and contributors
# For license information, please see license.txt


import frappe  
import json  
from frappe import _  
from frappe.utils import getdate, add_months, month_diff, nowdate, get_first_day, get_last_day

def execute(filters=None):  
   if not filters:  
       filters = {}

   # Set default filters if not specified  
   if not filters.get("from_date"):  
       filters["from_date"] = add_months(nowdate(), -12)  # Default to last 12 months  
   if not filters.get("to_date"):  
       filters["to_date"] = nowdate()

   # Get the columns and data for the report  
   columns = get_columns()  
   data = get_data(filters)

   # Prepare chart data  
   chart = get_chart(data)

   return columns, data, None, chart

def get_columns():  
   """Return the list of columns for the report"""  
   return [  
       {  
           "fieldname": "month_year",  
           "label": _("Month"),  
           "fieldtype": "Data",  
           "width": 220  
       },  
       {  
           "fieldname": "total_cost",  
           "label": _("Total Cost"),  
           "fieldtype": "Currency",  
           "width": 220  
       },  
       {  
           "fieldname": "labor_cost",  
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
       },  
       {  
           "fieldname": "supervision_cost",  
           "label": _("Supervision Cost"),  
           "fieldtype": "Currency",  
           "width": 220  
       },  
       {  
           "fieldname": "work_count",  
           "label": _("# of Works"),  
           "fieldtype": "Int",  
           "width": 120  
       }  
   ]

def get_data(filters):  
   """Fetch and process data for the report"""  
   # Base query conditions - will be prefixed with table alias later  
   conditions = " AND w.docstatus = 1"  # Only consider submitted works  
    
   # Add date range conditions  
   conditions += f" AND w.work_date >= '{filters.get('from_date')}'"  
   conditions += f" AND w.work_date <= '{filters.get('to_date')}'"  
    
   # Always join with Plot table for supervision charges and other filters
   cluster_join = "LEFT JOIN `tabPlot` p ON w.plot = p.name"
   
   # Add filters sequentially instead of using elif to allow multiple filters to apply
   if filters.get("cluster"):  
       conditions += f" AND p.cluster = '{filters.get('cluster')}'"  
   
   if filters.get("plot"):  
       conditions += f" AND w.plot = '{filters.get('plot')}'"  
   
   if filters.get("customer"):  
       conditions += f" AND w.customer = '{filters.get('customer')}'"  
    
   # Query to get all relevant works with appropriate supervision charges  
   query = f"""  
       SELECT  
           w.name,  
           w.work_date,  
           w.plot,  
           w.total_cost,  
           COALESCE(w.supervision_charges, p.supervision_charges, 0) as supervision_charges  
       FROM  
           `tabWork` w  
       {cluster_join}  
       WHERE  
           1=1 {conditions}  
       ORDER BY  
           w.work_date  
   """  
    
   works = frappe.db.sql(query, as_dict=1)  
    
   # Get additional cost breakdowns per work  
   monthly_data = {}  
   for work in works:  
       # Format the month and year (e.g., "Jan 2025")  
       month_year = getdate(work.work_date).strftime("%b %Y")  
        
       # Debug log for supervision_charges  
       frappe.logger().debug(f"Work {work.name}, Date {work.work_date}, Supervision: {work.supervision_charges}")  
        
       # Initialize the month if not already in dictionary  
       if month_year not in monthly_data:  
           monthly_data[month_year] = {  
               "month_year": month_year,  
               "total_cost": 0,  
               "labor_cost": 0,  
               "material_cost": 0,  
               "equipment_cost": 0,  
               "supervision_cost": 0,  
               "work_count": 0,  
               "sort_key": getdate(work.work_date)  
           }  
        
       # Get cost breakdown for this work  
       labor_cost, material_cost, equipment_cost = get_cost_breakdown(work.name)  
        
       # Calculate supervision cost  
       # Convert supervision_charges to float, ensure it defaults to 0 if None or invalid  
       try:  
           supervision_percentage = float(work.supervision_charges or 0)  
       except (ValueError, TypeError):  
           supervision_percentage = 0  
            
       # Calculate supervision cost based on total_cost  
       supervision_cost = (work.total_cost * supervision_percentage) / 100  
        
       # Round supervision cost to 2 decimal places  
       supervision_cost = round(supervision_cost, 2)  
        
       # Add to monthly totals  
       monthly_data[month_year]["total_cost"] += work.total_cost  
       monthly_data[month_year]["labor_cost"] += labor_cost  
       monthly_data[month_year]["material_cost"] += material_cost  
       monthly_data[month_year]["equipment_cost"] += equipment_cost  
       monthly_data[month_year]["supervision_cost"] += supervision_cost  
       monthly_data[month_year]["work_count"] += 1  
    
   # Convert dictionary to list and sort by date  
   result = list(monthly_data.values())  
   result.sort(key=lambda x: x["sort_key"])  
    
   # Remove the sort key from the final output  
   for entry in result:  
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

def get_chart(data):
    """Generate chart data for the report"""
    if not data:
        return None
    
    labels = []
    total_cost_data = []
    labor_cost_data = []
    material_cost_data = []
    equipment_cost_data = []
    supervision_cost_data = []
    
    for entry in data:
        labels.append(entry["month_year"])
        total_cost_data.append(entry["total_cost"])
        labor_cost_data.append(entry["labor_cost"])
        material_cost_data.append(entry["material_cost"])
        equipment_cost_data.append(entry["equipment_cost"])
        supervision_cost_data.append(entry["supervision_cost"])
    
    # Simplified chart structure that is compatible with Frappe v15
    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Total Cost", "values": total_cost_data, "chartType": "line", "color": "#FF5858"},  # Red
                {"name": "Labor", "values": labor_cost_data, "chartType": "line", "color": "#5EC962"},       # Green
                {"name": "Material", "values": material_cost_data, "chartType": "line", "color": "#7B6CFF"},  # Purple
                {"name": "Equipment", "values": equipment_cost_data, "chartType": "line", "color": "#FFA00A"}, # Orange
                {"name": "Supervision", "values": supervision_cost_data, "chartType": "line", "color": "#00BCD4"} # Cyan
            ]
        },
        "type": "line"
    }
    
    return chart

@frappe.whitelist()
def get_customer_for_plot(doctype, txt, searchfield, start, page_len, filters):
    """
    Get the customer for a specific plot.
    This function will be called by the customer filter when a plot is selected.
    """
    # Handle filters which may be passed as a string
    if isinstance(filters, str):
        filters = json.loads(filters)
    
    # Check if plot filter exists
    plot = None
    if isinstance(filters, dict):
        plot = filters.get('plot')
    elif hasattr(filters, 'plot'):
        plot = filters.plot
    
    if not plot:
        return []
    
    # Get the customer for the selected plot using the correct field name "customer_name"
    plot_info = frappe.db.get_value('Plot', plot, 'customer_name', as_dict=1)
    
    if not plot_info or not plot_info.customer_name:
        return []
    
    # Return the customer in the format expected by Frappe's link field
    return [(plot_info.customer_name,)]

@frappe.whitelist()
def get_customers_for_cluster(doctype, txt, searchfield, start, page_len, filters):
   """
   Get all customers associated with plots in a specific cluster.
   This function will be called by the customer filter when a cluster is selected but no plot is selected.
   """
   # Handle filters which may be passed as a string
   if isinstance(filters, str):
       filters = json.loads(filters)
    
   # Check if cluster filter exists
   cluster = None
   if isinstance(filters, dict):
       cluster = filters.get('cluster')
   elif hasattr(filters, 'cluster'):
       cluster = filters.cluster
    
   if not cluster:
       return []
    
   # Get all plots in the cluster
   plots = frappe.db.sql("""
       SELECT name, customer_name 
       FROM `tabPlot` 
       WHERE cluster = %s AND customer_name IS NOT NULL
   """, cluster, as_dict=1)
    
   # Extract unique customers
   customers = []
   customer_set = set()
   
   for plot in plots:
       if plot.customer_name and plot.customer_name not in customer_set:
           customer_set.add(plot.customer_name)
           customers.append((plot.customer_name,))
    
   return customers