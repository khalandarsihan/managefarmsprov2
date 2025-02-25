# Copyright (c) 2025, Khalandar Sihan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	if filters is None:
		filters = {}

	threshold = filters.get("maintenance_balance_threshold")
	if threshold is None:
		threshold = 500.0
	else:
		threshold = round(float(threshold), 2)

	columns = get_columns()
	data = get_data(threshold)
	return columns, data


def get_columns():
	return [
		{"fieldname": "plot_name", "label": _("Plot Name"), "fieldtype": "Data", "width": 150},
		{
			"fieldname": "customer_name",
			"label": _("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150,
		},
		{
			"fieldname": "cluster",
			"label": _("Cluster"),
			"fieldtype": "Link",
			"options": "Cluster",
			"width": 120,
		},
		{"fieldname": "plot_status", "label": _("Status"), "fieldtype": "Select", "width": 100},
		{
			"fieldname": "monthly_maintenance_budget",
			"label": _("Monthly Budget"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"fieldname": "total_amount_spent",
			"label": _("Amount Spent"),
			"fieldtype": "Currency",
			"width": 120,
		},
		{"fieldname": "maintenance_balance", "label": _("Balance"), "fieldtype": "Currency", "width": 120},
	]


def get_data(threshold):
	# Updated query to calculate balance correctly
	query = """
        SELECT
            plot_name,
            customer_name,
            cluster,
            plot_status,
            monthly_maintenance_budget,
            total_amount_spent,
            (monthly_maintenance_budget - IFNULL(total_amount_spent, 0)) as maintenance_balance
        FROM `tabPlot`
        WHERE monthly_maintenance_budget > 0
        AND (monthly_maintenance_budget - IFNULL(total_amount_spent, 0)) <= %s
        ORDER BY maintenance_balance ASC, plot_name ASC
    """

	result = frappe.db.sql(query, (threshold,), as_dict=1)

	# Ensure proper number formatting
	for row in result:
		row.monthly_maintenance_budget = flt(row.monthly_maintenance_budget, 2)
		row.total_amount_spent = flt(row.total_amount_spent, 2)
		row.maintenance_balance = flt(row.maintenance_balance, 2)

	return result
