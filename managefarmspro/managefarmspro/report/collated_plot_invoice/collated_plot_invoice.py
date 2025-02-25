import json
import os
import random
import time  # to use a timestamp for uniqueness
import uuid

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.utils import add_days
from frappe.utils.pdf import get_pdf


@frappe.whitelist()
def execute(filters=None):
	"""Generate report data and return columns, data for Frappe query report."""
	columns = get_columns()
	data, grand_total, supervision_charges = get_data(filters)
	return columns, data


def get_columns():
	"""Define and return the column structure for the report."""
	return [
		{"fieldname": "plot", "label": _("Plot"), "fieldtype": "Link", "options": "Plot", "width": 150},
		{"fieldname": "work_date", "label": _("Work Date"), "fieldtype": "Date", "width": 120},
		{"fieldname": "work_name", "label": _("Work Name"), "fieldtype": "Data", "width": 180},
		{"fieldname": "work_id", "label": _("Work ID"), "fieldtype": "Data", "width": 150},
		{"fieldname": "description", "label": _("Description"), "fieldtype": "Data", "width": 450},
		{"fieldname": "total_cost", "label": _("Total Cost"), "fieldtype": "Currency", "width": 120},
	]


def get_data(filters):
	"""Fetch and structure data for the report based on the provided filters."""
	Work = DocType("Work")
	Plot = DocType("Plot")

	plot_name = filters.get("plot")
	start_date = filters.get("start_date")
	end_date = filters.get("end_date")

	# Base condition for the query
	conditions = (Work.docstatus == 1) & ((Work.invoice_number.isnull()) | (Work.invoice_number == ""))

	# Additional conditions based on filters
	if plot_name:
		conditions &= Work.plot == plot_name
	if start_date and end_date:
		conditions &= Work.work_date.between(start_date, end_date)

	# Using Query Builder instead of raw SQL
	invoices = (
		frappe.qb.from_(Work)
		.left_join(Plot)
		.on(Work.plot == Plot.name)
		.select(
			Work.name.as_("work_id"),
			Work.plot,
			Plot.plot_name,
			Work.work_date,
			Work.work_name.as_("work_name"),
			Work.description,
			Work.total_cost,
			Work.customer,
		)
		.where(conditions)
		.orderby(Work.work_date)
		.run(as_dict=True)
	)

	grand_total = 0
	supervision_charges = 0
	for invoice in invoices:
		grand_total += invoice.get("total_cost", 0) or 0

		plot_details = frappe.db.get_value(
			"Plot", invoice.get("plot"), ["customer_name", "plot_name", "supervision_charges"], as_dict=True
		)
		invoice["customer"] = invoice.get("customer") or plot_details.get("customer_name", _("N/A"))
		invoice["plot_name"] = plot_details.get("plot_name") if plot_details else _("N/A")

		supervision_percent = plot_details.get("supervision_charges") if plot_details else 0
		invoice_supervision_charge = (supervision_percent / 100) * invoice.get("total_cost", 0)
		supervision_charges += invoice_supervision_charge

		# Fetch item names from Item Doctype and include them
		labor_details = frappe.get_all(
			"Labor Child",
			filters={"parent": invoice.get("work_id")},
			fields=[
				"labor_code as item_code",
				"item_display_name as item_name",
				"number_of_labor_units as qty",
				"labor_unit as unit",
				"unit_price as rate",  # Include rate
				"total_price as amount",
				"'Labor' as item_group",
			],
		)
		equipment_details = frappe.get_all(
			"Equipment Child",
			filters={"parent": invoice.get("work_id")},
			fields=[
				"equipment_code as item_code",
				"item_display_name as item_name",
				"number_of_equipment_units as qty",
				"equipment_unit as unit",
				"unit_price as rate",  # Include rate
				"total_price as amount",
				"'Equipment' as item_group",
			],
		)
		material_details = frappe.get_all(
			"Material Child",
			filters={"parent": invoice.get("work_id")},
			fields=[
				"material_code as item_code",
				"item_display_name as item_name",
				"number_of_material_units as qty",
				"material_unit as unit",
				"unit_price as rate",  # Include rate
				"total_price as amount",
				"'Raw Material' as item_group",
			],
		)

		# Map item codes to item names
		# for item in labor_details + equipment_details + material_details:
		# 	item["item_name"] = (
		# 		frappe.db.get_value("Item", item["item_code"], "item_name") or item["item_code"]
		# 	)

		# Map item codes to item names
		for item in labor_details + equipment_details + material_details:
			if not item.get("item_name") or item["item_name"] == "":
				item["item_name"] = (
					frappe.db.get_value("Item", item["item_code"], "item_name") or item["item_code"]
				)


		# Combine the details into one list of items
		invoice["items"] = labor_details + equipment_details + material_details

		# Ensure items are initialized
		invoice["items"] = invoice["items"] if invoice["items"] else []

	return invoices, grand_total, supervision_charges


@frappe.whitelist()
def download_invoice_pdf(filters):
	"""
	Generate a consolidated Sales Invoice PDF, link the invoice number to each work entry,
	and create a Sales Invoice entry in Frappe.
	"""
	if isinstance(filters, str):
		filters = json.loads(filters)

	invoices, grand_total, supervision_charges = get_data(filters)
	if not invoices:
		frappe.throw(_("No new work entries found for generating the invoice."))

	final_grand_total = grand_total + supervision_charges

	customer = invoices[0].get("customer", None)
	plot_name = invoices[0].get("plot", _("N/A"))

	if not customer or not frappe.db.exists("Customer", customer):
		frappe.throw(_("Customer not found for this plot. Please ensure a valid customer is assigned."))

	company = "Philosan Farm Management"
	income_account = frappe.db.get_value("Company", company, "default_income_account")
	if not income_account:
		frappe.throw(_("Please set a default income account for the company {0}.").format(company))

	supervision_charge_account = "Service - PFM"

	# Create a new Sales Invoice with stock update enabled
	sales_invoice = frappe.get_doc(
		{
			"doctype": "Sales Invoice",
			"customer": customer,
			"company": company,
			"custom_plot": plot_name,
			"posting_date": filters.get("end_date"),
			"due_date": add_days(filters.get("end_date"), 10),
			"update_stock": 1,
			"set_warehouse": "Main Warehouse - PFM",
			"cost_center": "Main - PFM",
			"items": [],
			"set_posting_time": 1,
		}
	)

	for invoice in invoices:
		item_name = invoice.get("work_name")
		invoice_item = {
			"item_name": item_name,
			"description": invoice.get("description"),
			"qty": 1,
			"rate": invoice.get("total_cost"),
			"amount": invoice.get("total_cost"),
			"linked_work_entry": invoice.get("work_id"),
			"income_account": income_account,
			"warehouse": "Main Warehouse - PFM",
			"expense_account": "Cost of Goods Sold - PFM",
			"custom_plot": plot_name,
			"custom_work_id": invoice.get("work_id"),
		}
		sales_invoice.append("items", invoice_item)

	if supervision_charges > 0:
		additional_charge_item = {
			"item_name": _("Supervision Charges"),
			"description": _("Supervision charges for the services provided."),
			"qty": 1,
			"rate": supervision_charges,
			"amount": supervision_charges,
			"income_account": supervision_charge_account,
		}
		sales_invoice.append("items", additional_charge_item)

	sales_invoice.total = grand_total
	sales_invoice.total_taxes_and_charges = 0
	sales_invoice.total_amount = final_grand_total
	sales_invoice.grand_total = final_grand_total
	sales_invoice.rounded_total = final_grand_total
	sales_invoice.outstanding_amount = final_grand_total

	sales_invoice.insert()
	sales_invoice.submit()

	invoice_number = sales_invoice.name

	for invoice in invoices:
		frappe.db.set_value("Work", invoice["work_id"], "invoice_number", invoice_number)

	for invoice in invoices:
		invoice["invoice_items"] = invoice.pop("items", []) if invoice.get("items") is not None else []

	context = {
		"invoices": invoices,
		"grand_total": grand_total,
		"supervision_charges": supervision_charges,
		"final_grand_total": final_grand_total,
		"filters": filters,
		"invoice_number": invoice_number,
		"customer": customer,
		"plot_name": plot_name,
	}

	html = frappe.render_template("managefarmspro/templates/collated_invoice.html", context)
	pdf_file = get_pdf(html)

	# Get the request object to access headers
	request = frappe.request

	# Get the host from the request headers
	host = request.headers.get("Host")

	# Get the scheme (http/https)
	forwarded_proto = request.headers.get("X-Forwarded-Proto", "http")

	# If we're behind a proxy (like nginx), use the original host
	original_host = request.headers.get("X-Forwarded-Host", host)

	# Construct the base URL using the actual host that the client used
	base_url = f"{forwarded_proto}://{original_host}"

	# Retrieve the plot ID from the provided filters
	plot_id = filters.get("plot")

	# Fetch the plot name from the database using the plot ID
	plot_name = frappe.db.get_value("Plot", plot_id, "plot_name") or _("N/A")

	# Generate a unique identifier using timestamp + random number
	timestamp = int(time.time())  # Current timestamp
	random_number = random.randint(1000, 9999)  # A random number between 1000 and 9999
	unique_suffix = f"{timestamp}{random_number}"  # Combine them

	# Construct the file name using the plot name and unique identifier
	file_name = (
		f"Invoice_{plot_name}_{filters.get('start_date')}_{filters.get('end_date')}_{unique_suffix}.pdf"
	)

	file_path = f"private/files/{file_name}"
	full_file_path = frappe.get_site_path(file_path)

	os.makedirs(os.path.dirname(full_file_path), exist_ok=True)

	with open(full_file_path, "wb") as f:
		f.write(pdf_file)

	# Create the File document and link it to the Sales Invoice
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": file_name,
			"file_url": f"/private/files/{file_name}",  # Save without domain
			"attached_to_doctype": "Sales Invoice",
			"attached_to_name": invoice_number,
			"is_private": 1,
		}
	)
	file_doc.insert(ignore_permissions=True)

	# Retrieve the content hash generated by Frappe for the file
	content_hash = file_doc.content_hash
	hash_suffix = content_hash[-6:]  # Extract last 6 characters of content hash

	# Update file paths with content hash
	final_file_path = f"/private/files/Invoice_{plot_name}_{filters.get('start_date')}_{filters.get('end_date')}_{unique_suffix}{hash_suffix}.pdf"

	# Create the final URL with the correct host
	final_url = f"{base_url}{final_file_path}"

	# Update the Sales Invoice with the file path (not full URL)
	frappe.db.set_value("Sales Invoice", invoice_number, "custom_pdf_invoice_link", final_file_path)

	# Update Work Doctype with the file path
	for invoice in invoices:
		frappe.db.set_value("Work", invoice["work_id"], "pdf_invoice_link", final_file_path)

	return final_url
