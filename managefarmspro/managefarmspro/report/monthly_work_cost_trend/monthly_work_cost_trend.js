// Copyright (c) 2025, Khalandar Sihan and contributors
// For license information, please see license.txt

// frappe.query_reports["Monthly Work Cost Trend"] = {
//   filters: [
//     {
//       fieldname: "from_date",
//       label: __("From Date"),
//       fieldtype: "Date",
//       default: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
//       reqd: 1,
//     },
//     {
//       fieldname: "to_date",
//       label: __("To Date"),
//       fieldtype: "Date",
//       default: frappe.datetime.get_today(),
//       reqd: 1,
//     },
//     {
//       fieldname: "cluster",
//       label: __("Cluster"),
//       fieldtype: "Link",
//       options: "Cluster",
//     },
//     {
//       fieldname: "plot",
//       label: __("Plot"),
//       fieldtype: "Link",
//       options: "Plot",
//     },
//     {
//       fieldname: "customer",
//       label: __("Customer"),
//       fieldtype: "Link",
//       options: "Customer",
//     },
//   ],
// };

// Copyright (c) 2025, Khalandar Sihan and contributors
// For license information, please see license.txt

// Copyright (c) 2025, Khalandar Sihan and contributors
// For license information, please see license.txt

frappe.query_reports["Monthly Work Cost Trend"] = {
  filters: [
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      default: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
      reqd: 1,
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      default: frappe.datetime.get_today(),
      reqd: 1,
    },
    {
      fieldname: "cluster",
      label: __("Cluster"),
      fieldtype: "Link",
      options: "Cluster",
      on_change: function () {
        let cluster = frappe.query_report.get_filter_value("cluster");

        if (!cluster) {
          // If cluster is cleared, also clear plot and customer
          frappe.query_report.set_filter_value("plot", "");
          frappe.query_report.set_filter_value("customer", "");
        } else {
          // When cluster changes, clear dependent filters but don't refresh yet
          frappe.query_report.set_filter_value("plot", "");
          frappe.query_report.set_filter_value("customer", "");

          // Force refresh of the customer dropdown options to reflect the new cluster
          setTimeout(function () {
            // This trick forces the customer field to re-evaluate its get_query function
            frappe.query_report.set_filter_value("customer", "");
          }, 100);
        }

        // Always refresh after changing filters
        frappe.query_report.refresh();
      },
    },
    {
      fieldname: "plot",
      label: __("Plot"),
      fieldtype: "Link",
      options: "Plot",
      get_query: function () {
        let cluster = frappe.query_report.get_filter_value("cluster");
        if (cluster) {
          return {
            filters: {
              cluster: cluster,
            },
          };
        }
      },
      on_change: function () {
        let plot = frappe.query_report.get_filter_value("plot");

        if (!plot) {
          // If plot is cleared, also clear customer and refresh
          frappe.query_report.set_filter_value("customer", "");
          frappe.query_report.refresh();
        } else {
          // If a plot is selected, automatically fetch and set the customer
          frappe.call({
            method:
              "managefarmspro.managefarmspro.report.monthly_work_cost_trend.monthly_work_cost_trend.get_customer_for_plot",
            args: {
              doctype: "Customer",
              txt: "",
              searchfield: "name",
              start: 0,
              page_len: 1,
              filters: JSON.stringify({ plot: plot }),
            },
            callback: function (r) {
              // If customer data was returned, set it as the customer filter value
              if (r.message && r.message.length > 0) {
                frappe.query_report.set_filter_value(
                  "customer",
                  r.message[0][0]
                );
              } else {
                // Clear customer if none found for this plot
                frappe.query_report.set_filter_value("customer", "");
              }
              // Refresh the report after setting/clearing the customer
              frappe.query_report.refresh();
            },
          });
        }
      },
    },
    {
      fieldname: "customer",
      label: __("Customer"),
      fieldtype: "Link",
      options: "Customer",
      get_query: function () {
        let plot = frappe.query_report.get_filter_value("plot");
        let cluster = frappe.query_report.get_filter_value("cluster");

        if (plot) {
          // If plot is selected, filter customer based on that plot
          return {
            query:
              "managefarmspro.managefarmspro.report.monthly_work_cost_trend.monthly_work_cost_trend.get_customer_for_plot",
            filters: {
              plot: plot,
            },
          };
        } else if (cluster) {
          // If only cluster is selected (no plot), filter customers based on cluster
          return {
            query:
              "managefarmspro.managefarmspro.report.monthly_work_cost_trend.monthly_work_cost_trend.get_customers_for_cluster",
            filters: {
              cluster: cluster,
            },
          };
        }
      },
      on_change: function () {
        // Refresh the report when customer changes
        frappe.query_report.refresh();
      },
    },
  ],

  onload: function (report) {
    // Hide the Actions button
    setTimeout(function () {
      // Try multiple selectors to catch the Actions button
      $(".actions-btn-group").hide();
      $('.btn-group:contains("Actions")').hide();
      $('button:contains("Actions")').hide();
      $('.page-actions button:contains("Actions")').hide();
      $('.standard-actions button:contains("Actions")').hide();
      $('.custom-actions button:contains("Actions")').hide();

      // If there's a div with class containing 'actions'
      $('div[class*="actions"]:contains("Actions")').hide();

      // Remove it from DOM if hiding doesn't work
      $('.page-actions button:contains("Actions")').remove();
    }, 1000);
  },
};
