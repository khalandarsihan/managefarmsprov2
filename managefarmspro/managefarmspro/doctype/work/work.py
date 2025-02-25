import frappe
from frappe.model.document import Document
from frappe.utils import get_first_day, get_last_day, getdate


class Work(Document):
	def validate(self):
		if self.plot:
			plot_doc = frappe.get_doc("Plot", self.plot)

			# Only proceed with maintenance checks if plot has budget
			if plot_doc.monthly_maintenance_budget:
				# First ensure the plot is up to date with any monthly resets
				plot_doc.check_monthly_reset()
				plot_doc.save()

				# Now get the current values
				self.monthly_maintenance_budget = plot_doc.monthly_maintenance_budget

				# Calculate total cost including supervision charges
				current_date = getdate()
				month_start = get_first_day(current_date)
				month_end = get_last_day(current_date)

				# Get total spent including supervision charges
				total_spent = frappe.db.sql(
					"""
                    SELECT COALESCE(SUM(total_cost + (total_cost * %s / 100)), 0)
                    FROM tabWork
                    WHERE plot = %s
                    AND docstatus = 1
                    AND work_date BETWEEN %s AND %s
                    """,
					(plot_doc.supervision_charges or 0, self.plot, month_start, month_end),
				)[0][0]

				self.maintenance_balance = plot_doc.monthly_maintenance_budget - total_spent

	def on_submit(self):
		self.update_plot_totals()

	def on_cancel(self):
		self.update_plot_totals()

	def update_plot_totals(self):
		if self.plot:
			plot_doc = frappe.get_doc("Plot", self.plot)

			# Skip if no maintenance budget is set
			if not plot_doc.monthly_maintenance_budget:
				return

			current_date = getdate()
			month_start = get_first_day(current_date)
			month_end = get_last_day(current_date)

			# Get total spent including supervision charges
			total_spent = frappe.db.sql(
				"""
                SELECT COALESCE(SUM(total_cost + (total_cost * %s / 100)), 0)
                FROM tabWork
                WHERE plot = %s
                AND docstatus = 1
                AND work_date BETWEEN %s AND %s
                """,
				(plot_doc.supervision_charges or 0, self.plot, month_start, month_end),
			)[0][0]

			# Update Plot document fields
			frappe.db.set_value(
				"Plot",
				self.plot,
				{
					"total_amount_spent": total_spent,
					"maintenance_balance": plot_doc.monthly_maintenance_budget - total_spent,
				},
				update_modified=False,
			)

			# Publish realtime update
			frappe.publish_realtime(
				"plot_updated",
				{
					"plot_name": self.plot,
					"total_amount_spent": total_spent,
					"maintenance_balance": plot_doc.monthly_maintenance_budget - total_spent,
				},
				doctype="Plot",
				docname=self.plot,
				after_commit=True,
			)


@frappe.whitelist()
def get_plot_balances(plot):
	"""Get the current maintenance budget and balance for a plot"""
	plot_doc = frappe.get_doc("Plot", plot)

	# Only check monthly reset if maintenance budget exists
	if plot_doc.monthly_maintenance_budget:
		plot_doc.check_monthly_reset()
		plot_doc.save()

		current_date = getdate()
		month_start = get_first_day(current_date)
		month_end = get_last_day(current_date)

		# Get total spent including supervision charges
		total_spent = frappe.db.sql(
			"""
            SELECT COALESCE(SUM(total_cost + (total_cost * %s / 100)), 0)
            FROM tabWork
            WHERE plot = %s
            AND docstatus = 1
            AND work_date BETWEEN %s AND %s
            """,
			(plot_doc.supervision_charges or 0, plot, month_start, month_end),
		)[0][0]

		return {
			"monthly_maintenance_budget": plot_doc.monthly_maintenance_budget,
			"maintenance_balance": plot_doc.monthly_maintenance_budget - total_spent,
		}
	else:
		return {"monthly_maintenance_budget": 0, "maintenance_balance": 0}


# Function to calculate total cost based on child tables
def calculate_total_cost(doc, method):
	total_cost = sum(
		(row.total_price or 0)
		for table in [doc.equipment_table, doc.material_table, doc.labor_table]
		if table
		for row in table
	)
	doc.db_set("total_cost", total_cost, update_modified=False)


# Function to update the Work Child table in the Plot Doctype
def update_work_child(doc, method):
	work_child_data = {
		"work_id": doc.name,
		"work_name": doc.work_type_name,
		"work_date": doc.work_date,
		"status": {0: "Draft", 1: "Submitted", 2: "Cancelled"}.get(doc.docstatus, "Unknown"),
		"total_cost": doc.total_cost,
		"parent": doc.plot,
		"parentfield": "work_details",
		"parenttype": "Plot",
	}
	if frappe.db.exists("Work Child", {"parent": doc.plot, "work_id": doc.name}):
		frappe.db.set_value("Work Child", {"parent": doc.plot, "work_id": doc.name}, work_child_data)
	else:
		frappe.get_doc({"doctype": "Work Child", **work_child_data}).insert()
