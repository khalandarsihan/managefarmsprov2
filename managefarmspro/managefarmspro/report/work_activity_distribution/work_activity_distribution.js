// Copyright (c) 2025, Khalandar Sihan and contributors
// For license information, please see license.txt

frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Work Activity Distribution"] = {
  method:
    "managefarmspro.managefarmspro.dashboard_chart.work_activity_distribution.work_activity_distribution.get",
  filters: [
    {
      fieldname: "cluster",
      label: __("Cluster"),
      fieldtype: "Link",
      options: "Cluster",
    },
    {
      fieldname: "plot",
      label: __("Plot"),
      fieldtype: "Link",
      options: "Plot",
      get_query: function () {
        var cluster = frappe.dashboard_utils.get_filter_value("cluster");
        if (cluster) {
          return {
            filters: {
              cluster: cluster,
            },
          };
        }
      },
    },
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      default: frappe.datetime.get_today(),
    },
  ],
};
