// Copyright (c) 2024, FigAi GenAi Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on("Plot", {
  refresh: function (frm) {
    // Setup real-time updates for the form
    setupRealtimeUpdates(frm);

    // Format the monthly maintenance budget with currency symbol
    let value = frm.doc.monthly_maintenance_budget || 0;
    let formatted_value = format_currency(
      value,
      frappe.defaults.get_default("currency")
    );
    $(frm.fields_dict.monthly_maintenance_budget.input).val(formatted_value);
  },

  monthly_maintenance_budget: function (frm) {
    // Format even if value is zero
    let value = frm.doc.monthly_maintenance_budget || 0;
    let formatted_value = format_currency(
      value,
      frappe.defaults.get_default("currency")
    );
    $(frm.fields_dict.monthly_maintenance_budget.input).val(formatted_value);
  },

  onload: function (frm) {
    // Initial setup when form loads
    setupRealtimeUpdates(frm);
  },

  plot_number: function (frm) {
    // Fetch the full name from the customer_name field
    let full_name = frm.doc.customer_name || "Customer_Name";
    // Replace spaces with underscores for the plot name
    let formatted_full_name = full_name.replace(/\s+/g, "_");

    // Check if plot number is entered
    if (frm.doc.plot_number) {
      frm.set_value(
        "plot_name",
        `PLOT_${frm.doc.plot_number}_${formatted_full_name}`
      );
    } else {
      frm.set_value("plot_name", `PLOT_${formatted_full_name}`);
    }
  },

  customer_name: function (frm) {
    // Re-trigger the plot_number event to update plot_name when customer_name changes
    frm.trigger("plot_number");
  },
});

function setupRealtimeUpdates(frm) {
  // Remove any existing socket event listeners to prevent duplicates
  frappe.realtime.off("plot_updated");

  // Listen for plot updates
  frappe.realtime.on("plot_updated", function (data) {
    // Check if the update is for the current plot
    if (data.plot_name === frm.doc.name) {
      // Refresh form fields
      frm.reload_doc();

      // Optional: Show a notification
      frappe.show_alert(
        {
          message: __("Plot details updated"),
          indicator: "green",
        },
        3
      );
    }
  });
}
