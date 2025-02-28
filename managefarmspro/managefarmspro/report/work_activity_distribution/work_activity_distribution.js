// Copyright (c) 2025, Khalandar Sihan and contributors
// For license information, please see license.txt

frappe.query_reports["Work Activity Distribution"] = {
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
    {
      fieldname: "min_count",
      label: __("Minimum Count"),
      fieldtype: "Int",
      default: 1,
      min: 1,
      width: "80",
    },
    {
      fieldname: "chart_type",
      label: __("Chart Type"),
      fieldtype: "Select",
      options: "Pie\nBar\nPercentage",
      default: "Pie",
      width: "80",
    },
  ],

  onload: function (report) {
    // Add custom buttons for chart visualization options
    report.page.add_inner_button(__("View by Cost"), function () {
      toggleChartMetric(report, "cost");
    });

    report.page.add_inner_button(__("View by Count"), function () {
      toggleChartMetric(report, "count");
    });

    report.page.add_inner_button(__("View Top 5"), function () {
      showTopActivities(report, 5);
    });

    report.page.add_inner_button(__("View Top 10"), function () {
      showTopActivities(report, 10);
    });

    report.page.add_inner_button(__("Activity Cost Summary"), function () {
      showActivityCostSummary(report);
    });

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

// Toggle between count and cost metrics in the chart
function toggleChartMetric(report, metric) {
  if (!report.data || !report.data.length) {
    frappe.msgprint(__("No data available to display"));
    return;
  }

  let data = report.data;
  let labels = data.map((d) => d.work_name);
  let values = [];
  let chartTitle = "";
  let valueFormatter = null;

  if (metric === "count") {
    values = data.map((d) => d.work_count);
    chartTitle = "Work Activity Distribution by Count";
  } else {
    values = data.map((d) => d.total_cost);
    chartTitle = "Work Activity Distribution by Cost";
    valueFormatter = (value) => frappe.format(value, { fieldtype: "Currency" });
  }

  // Get current chart type
  let chartType = frappe.query_report.get_filter_value("chart_type") || "Pie";
  let chartTypeForRender = chartType.toLowerCase();

  if (chartType === "Percentage") {
    chartTypeForRender = "pie";
  }

  // Define chart colors
  let colors = [
    "#FF5733",
    "#33FF57",
    "#3357FF",
    "#F3FF33",
    "#FF33F3",
    "#33FFF3",
    "#FF8033",
    "#8033FF",
    "#5733FF",
    "#33FFF3",
    "#FFAF33",
    "#33FFAF",
  ];

  // Create the chart data
  let chartData = {
    labels: labels,
    datasets: [
      {
        name: metric === "count" ? "Count" : "Cost",
        values: values,
      },
    ],
  };

  // Render the chart
  frappe.query_report.render_chart({
    type: chartTypeForRender,
    title: chartTitle,
    data: chartData,
    colors: colors,
    height: 300,
    tooltipOptions: {
      formatTooltipY: valueFormatter,
    },
  });

  frappe.msgprint(__(`Now showing activity distribution by ${metric}`));
}

// Show only top N activities in the chart
function showTopActivities(report, n) {
  if (!report.data || !report.data.length) {
    frappe.msgprint(__("No data available to display"));
    return;
  }

  let data = report.data.slice(0, n);
  let labels = data.map((d) => d.work_name);
  let countValues = data.map((d) => d.work_count);
  let costValues = data.map((d) => d.total_cost);

  // Get current chart type
  let chartType = frappe.query_report.get_filter_value("chart_type") || "Pie";
  let chartTypeForRender = chartType.toLowerCase();

  if (chartType === "Percentage") {
    chartTypeForRender = "pie";
  }

  // Define chart colors
  let colors = [
    "#FF5733",
    "#33FF57",
    "#3357FF",
    "#F3FF33",
    "#FF33F3",
    "#33FFF3",
    "#FF8033",
    "#8033FF",
    "#5733FF",
    "#33FFF3",
    "#FFAF33",
    "#33FFAF",
  ].slice(0, n);

  // Create chart data for dual axis chart
  let chartData = {
    labels: labels,
    datasets: [
      {
        name: "Count",
        values: countValues,
        chartType: "bar",
      },
      {
        name: "Cost",
        values: costValues,
        chartType: "line",
      },
    ],
  };

  // Render the chart
  frappe.query_report.render_chart({
    type: "axis-mixed",
    title: `Top ${n} Activities by Count and Cost`,
    data: chartData,
    colors: ["#FF5722", "#4CAF50"],
    height: 300,
    axisOptions: {
      yAxes: [
        {
          formatTooltipY: (d) => d + " activities",
        },
        {
          formatTooltipY: (d) => frappe.format(d, { fieldtype: "Currency" }),
        },
      ],
    },
  });

  frappe.msgprint(__(`Showing top ${n} activities by count and cost`));
}

// Show a summary of activity costs
function showActivityCostSummary(report) {
  if (!report.data || !report.data.length) {
    frappe.msgprint(__("No data available for summary"));
    return;
  }

  let data = report.data;
  let totalCount = data.reduce((sum, d) => sum + d.work_count, 0);
  let totalCost = data.reduce((sum, d) => sum + d.total_cost, 0);
  let avgCostPerActivity = totalCost / totalCount;

  // Find the most expensive and most frequent activities
  let mostExpensive = data.reduce((prev, current) =>
    prev.avg_cost > current.avg_cost ? prev : current
  );

  let mostFrequent = data.reduce((prev, current) =>
    prev.work_count > current.work_count ? prev : current
  );

  let message = `
    <div style="text-align: center; padding: 15px;">
      <h3>Activity Cost Summary</h3>
      
      <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
        <div style="text-align: left; width: 60%;">Total Activities:</div>
        <div style="text-align: right; width: 40%;">${totalCount}</div>
      </div>
      
      <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
        <div style="text-align: left; width: 60%;">Total Cost:</div>
        <div style="text-align: right; width: 40%;">${frappe.format(totalCost, {
          fieldtype: "Currency",
        })}</div>
      </div>
      
      <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
        <div style="text-align: left; width: 60%;">Average Cost per Activity:</div>
        <div style="text-align: right; width: 40%;">${frappe.format(
          avgCostPerActivity,
          {
            fieldtype: "Currency",
          }
        )}</div>
      </div>
      
      <h4 style="margin-top: 20px;">Key Insights</h4>
      
      <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
        <div style="text-align: left; width: 60%;">Most Frequent Activity:</div>
        <div style="text-align: right; width: 40%;">${
          mostFrequent.work_name
        } (${mostFrequent.work_count})</div>
      </div>
      
      <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
        <div style="text-align: left; width: 60%;">Most Expensive Activity (avg):</div>
        <div style="text-align: right; width: 40%;">${
          mostExpensive.work_name
        } (${frappe.format(mostExpensive.avg_cost, {
    fieldtype: "Currency",
  })})</div>
      </div>
    </div>
  `;

  frappe.msgprint({
    title: __("Activity Cost Analysis"),
    indicator: "blue",
    message: message,
    wide: true,
  });
}
