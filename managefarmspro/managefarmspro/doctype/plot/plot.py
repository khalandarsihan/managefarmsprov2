import frappe
from frappe.model.document import Document
from frappe.utils import get_first_day, get_last_day, getdate


class Plot(Document):
	def onload(self):
		"""Updates total_amount_spent on form load for the current month"""
		self.update_current_month_spending()

	def update_current_month_spending(self):
		current_date = getdate()
		month_start = get_first_day(current_date)
		month_end = get_last_day(current_date)

		# Get total spent from submitted works for current month
		# Including supervision charge in the calculation
		total_spent = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(total_cost + (total_cost * %s / 100)), 0)
			FROM tabWork
			WHERE plot = %s
			AND docstatus = 1
			AND work_date BETWEEN %s AND %s
		""",
			(self.supervision_charges or 0, self.name, month_start, month_end),
		)[0][0]

		# Update the total_amount_spent
		self.db_set("total_amount_spent", total_spent, update_modified=False)

		# If monthly maintenance budget exists, update the maintenance balance
		if self.monthly_maintenance_budget:
			self.db_set(
				"maintenance_balance", self.monthly_maintenance_budget - total_spent, update_modified=False
			)

	def validate(self):
		# Sync maintenance_balance when monthly_maintenance_budget changes
		if self.has_value_changed("monthly_maintenance_budget"):
			self.maintenance_balance = self.monthly_maintenance_budget

		# Only proceed with maintenance checks if budget is set
		if self.monthly_maintenance_budget:
			self.check_monthly_reset()

	def before_insert(self):
		if self.monthly_maintenance_budget:
			# Initialize maintenance balance with budget amount for new plots
			self.maintenance_balance = self.monthly_maintenance_budget
			self.total_amount_spent = 0
			self.last_maintenance_reset = get_first_day(getdate())
			# self.db_update()
			# frappe.db.commit()

	def check_monthly_reset(self):
		if not self.monthly_maintenance_budget:
			return

		current_date = getdate()
		month_start = get_first_day(current_date)
		last_reset_date = self.get("last_maintenance_reset") or month_start

		if getdate(last_reset_date) < month_start:
			# First reset values for new month
			self.db_set("maintenance_balance", self.monthly_maintenance_budget, update_modified=False)
			self.db_set("total_amount_spent", 0, update_modified=False)
			self.db_set("last_maintenance_reset", month_start, update_modified=False)

			# Then update with any spending in current month
			self.update_current_month_spending()

	def before_save(self):
		# Capture the old cluster value before it's modified during the update
		self.previous_cluster_name = frappe.db.get_value("Plot", self.name, "cluster_name", cache=False)

	def on_update(self):
		# Handle updates to the Plot and corresponding Cluster
		if self.previous_cluster_name and self.previous_cluster_name != self.cluster_name:
			self.remove_from_previous_cluster(self.previous_cluster_name)

		# self.update_owner_plot_list()
		self.update_customer_custom_plot_details()
		self.update_cluster_plots()

		# Fetch work data dynamically, assuming it's passed in self
		if hasattr(self, "work_details"):
			for work in self.work_details:
				self.update_plot_work_details(work)
				self.update_cluster_work_details(work)

	def remove_from_previous_cluster(self, previous_cluster_name):
		try:
			previous_cluster_doc = frappe.get_doc("Cluster", previous_cluster_name)

			# Remove the plot from the previous cluster's child table
			previous_cluster_doc.plots = [
				plot for plot in previous_cluster_doc.plots if plot.plot != self.name
			]
			previous_cluster_doc.save()

		except frappe.DoesNotExistError:
			frappe.msgprint(f"Error: Previous cluster {previous_cluster_name} does not exist.")
			frappe.log_error(
				f"Previous Cluster {previous_cluster_name} not found for Plot {self.name}",
				"Remove from Old Cluster Error",
			)

	def update_customer_custom_plot_details(self):
		# Update the list of plots for the corresponding Customer
		customer_name = self.customer_name
		if customer_name:
			try:
				customer_doc = frappe.get_doc("Customer", customer_name)
				exists = False
				for plot in customer_doc.custom_plot_details:
					if plot.plot == self.name:
						plot.plot_name = self.plot_name
						plot.plot_area = self.area
						plot.plot_cluster = self.cluster
						exists = True
						break

				if not exists:
					customer_doc.append(
						"custom_plot_details",
						{
							"plot": self.name,
							"plot_name": self.plot_name,
							"plot_area": self.area,
							"cluster": self.cluster,
						},
					)
				customer_doc.save()

			except frappe.DoesNotExistError:
				frappe.log_error(
					f"Customer {customer_name} not found while creating/updating Plot {self.name}",
					"Populate Plot List Error",
				)

	def update_cluster_plots(self):
		# Update the Plots section of the Cluster Doctype
		cluster_name = self.cluster_name
		if cluster_name:
			try:
				cluster_doc = frappe.get_doc("Cluster", cluster_name)
				exists = False
				for plot in cluster_doc.plot_details:
					if plot.plot == self.name:
						plot.plot_name = self.plot_name
						plot.plot_area = self.area
						plot.units = self.units
						exists = True
						break

				if not exists:
					cluster_doc.append(
						"plot_details",
						{
							"plot": self.name,
							"plot_name": self.plot_name,
							"plot_area": self.area,
							"units": self.units,
						},
					)

				cluster_doc.save()

			except frappe.DoesNotExistError:
				frappe.msgprint(f"Error: New cluster {cluster_name} does not exist.")
				frappe.log_error(
					f"Cluster {cluster_name} not found while creating/updating Plot {self.name}",
					"Populate Plots Error",
				)

	def update_plot_work_details(self, work_data):
		# This method updates the Work details in the Plot's child table
		exists = False
		for work in self.work_details:  # Assuming work_details is the child table in Plot
			if work.work_id == work_data.work_id:
				# If the work entry already exists in the plot, update it
				work.work_name = work_data.work_name
				work.work_date = work_data.work_date
				work.status = work_data.status
				work.total_cost = work_data.total_cost
				exists = True
				break

		if not exists:
			# Add a new row to the Plot's work child table
			self.append(
				"work_details",
				{
					"work_id": work_data.work_id,
					"work_name": work_data.work_name,
					"work_date": work_data.work_date,
					"status": work_data.status,
					"total_cost": work_data.total_cost,
				},
			)

	def update_cluster_work_details(self, work_data):
		# Update the Work details in the Cluster's child table
		cluster_name = self.cluster_name
		if cluster_name:
			try:
				cluster_doc = frappe.get_doc("Cluster", cluster_name)

				exists = False
				for cluster_work in cluster_doc.work_details:
					if cluster_work.work_id == work_data.work_id:
						# If the work entry already exists in the cluster, update it
						cluster_work.work_name = work_data.work_name
						cluster_work.work_date = work_data.work_date
						cluster_work.status = work_data.status
						cluster_work.total_cost = work_data.total_cost
						exists = True
						break

				if not exists:
					# Add a new row to the Cluster's work child table
					cluster_doc.append(
						"work_details",
						{
							"work_id": work_data.work_id,
							"work_name": work_data.work_name,
							"work_date": work_data.work_date,
							"status": work_data.status,
							"total_cost": work_data.total_cost,
						},
					)
				# Save the Cluster document
				cluster_doc.save()

			except frappe.DoesNotExistError:
				frappe.msgprint(f"Error: Cluster {cluster_name} does not exist.")
				frappe.log_error(
					f"Cluster {cluster_name} not found while updating work details for Plot {self.name}",
					"Update Work Details Error",
				)