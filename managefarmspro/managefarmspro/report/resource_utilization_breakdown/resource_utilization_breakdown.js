// Copyright (c) 2025, Khalandar Sihan and contributors
// For license information, please see license.txt

frappe.query_reports["Resource Utilization Breakdown"] = {
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
      fieldname: "work_name",
      label: __("Work Type"),
      fieldtype: "Link",
      options: "Work Item",
    },
    {
      fieldname: "group_by",
      label: __("Group By"),
      fieldtype: "Select",
      options: "Month\nQuarter\nYear\nWork Type\nPlot\nCluster",
      default: "Month",
    },
    {
      fieldname: "chart_type",
      label: __("Chart Type"),
      fieldtype: "Select",
      options: "Bar\nLine\nPie\nPercentage\nStacked",
      default: "Stacked",
    },
  ],

  formatter: function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);

    if (
      [
        "labor_percentage",
        "equipment_percentage",
        "material_percentage",
        "supervision_percentage",
      ].includes(column.fieldname)
    ) {
      // Add color based on percentage value
      const percentage = parseFloat(data[column.fieldname]);

      if (percentage > 50) {
        value = `<span style="color: red; font-weight: bold;">${value}</span>`;
      } else if (percentage > 30) {
        value = `<span style="color: orange;">${value}</span>`;
      }
    }

    return value;
  },

  onload: function (report) {
    // Add custom buttons for visualization options
    report.page.add_inner_button(__("View as Absolute Values"), function () {
      toggleChartView(report, "absolute");
    });

    report.page.add_inner_button(__("View as Percentages"), function () {
      toggleChartView(report, "percentage");
    });

    report.page.add_inner_button(__("Monthly Trend"), function () {
      showMonthlyTrend(report);
    });

    report.page.add_inner_button(__("Resource Summary"), function () {
      showResourceSummary(report);
    });

    // report.page.add_inner_button(__("Export Chart"), function () {
    //   exportChart(report);
    // });

    // Hide the Actions button that comes by default
    setTimeout(function () {
      // Try multiple selectors to catch the Actions button
      //   $(".actions-btn-group").hide();
      //   $('.btn-group:contains("Actions")').hide();
      //   $('button:contains("Actions")').hide();
      //   $('.page-actions button:contains("Actions")').hide();
      //   $('.standard-actions button:contains("Actions")').hide();
      //   $('.custom-actions button:contains("Actions")').hide();
      // If there's a div with class containing 'actions'
      //   $('div[class*="actions"]:contains("Actions")').hide();
      // Remove it from DOM if hiding doesn't work
      //   $('.page-actions button:contains("Actions")').remove();
    }, 1000);
  },
};

// Toggle between absolute values and percentages in the chart
function toggleChartView(report, viewType) {
  if (!report.data || !report.data.length) {
    frappe.msgprint(__("No data available to display"));
    return;
  }

  let data = report.data;
  let labels = [];
  let laborValues = [];
  let materialValues = [];
  let equipmentValues = [];
  let supervisionValues = [];
  let chartTitle = "";

  // Extract labels and values based on group_by field
  let groupBy = frappe.query_report.get_filter_value("group_by") || "Month";

  data.forEach((d) => {
    labels.push(d[groupBy.toLowerCase()] || d.period);

    if (viewType === "percentage") {
      laborValues.push(d.labor_percentage || 0);
      materialValues.push(d.material_percentage || 0);
      equipmentValues.push(d.equipment_percentage || 0);
      supervisionValues.push(d.supervision_percentage || 0);
      chartTitle = "Resource Utilization (Percentage Breakdown)";
    } else {
      laborValues.push(d.labor_cost || 0);
      materialValues.push(d.material_cost || 0);
      equipmentValues.push(d.equipment_cost || 0);
      supervisionValues.push(d.supervision_cost || 0);
      chartTitle = "Resource Utilization (Absolute Values)";
    }
  });

  // Get current chart type
  let chartType =
    frappe.query_report.get_filter_value("chart_type") || "Stacked";
  let chartTypeForRender = chartType.toLowerCase();

  if (chartType === "Percentage" || chartType === "Stacked") {
    chartTypeForRender = "bar";
  }

  // Define chart colors
  let colors = ["#5EC962", "#7B6CFF", "#FFA00A", "#00BCD4"];

  // Create datasets
  let datasets = [];

  if (chartType === "Stacked" || chartType === "Bar" || chartType === "Line") {
    datasets = [
      {
        name: "Labor",
        values: laborValues,
        chartType: chartType === "Line" ? "line" : "bar",
      },
      {
        name: "Material",
        values: materialValues,
        chartType: chartType === "Line" ? "line" : "bar",
      },
      {
        name: "Equipment",
        values: equipmentValues,
        chartType: chartType === "Line" ? "line" : "bar",
      },
      {
        name: "Supervision",
        values: supervisionValues,
        chartType: chartType === "Line" ? "line" : "bar",
      },
    ];
  } else {
    // For pie charts, calculate the total for each resource type
    const totalLabor = laborValues.reduce((sum, val) => sum + val, 0);
    const totalMaterial = materialValues.reduce((sum, val) => sum + val, 0);
    const totalEquipment = equipmentValues.reduce((sum, val) => sum + val, 0);
    const totalSupervision = supervisionValues.reduce(
      (sum, val) => sum + val,
      0
    );

    labels = ["Labor", "Material", "Equipment", "Supervision"];
    datasets = [
      {
        values: [totalLabor, totalMaterial, totalEquipment, totalSupervision],
      },
    ];
  }

  // Create chart data
  let chartData = {
    labels: labels,
    datasets: datasets,
  };

  // Chart options
  let chartOptions = {
    height: 300,
    colors: colors,
  };

  // Add special formatting for percentage view
  if (viewType === "percentage") {
    chartOptions.tooltipOptions = {
      formatTooltipY: (d) => d.toFixed(1) + "%",
    };
    chartOptions.axisOptions = {
      yAxisMode: "tick",
      yAxisMax: 100,
    };
  } else {
    chartOptions.tooltipOptions = {
      formatTooltipY: (d) => frappe.format(d, { fieldtype: "Currency" }),
    };
  }

  // Special options for stacked bar chart
  if (chartType === "Stacked") {
    chartOptions.stacked = 1;
  }

  // Render the chart
  frappe.query_report.render_chart({
    type: chartTypeForRender,
    title: chartTitle,
    data: chartData,
    ...chartOptions,
  });

  frappe.msgprint(
    __(
      `Now showing resource utilization as ${
        viewType === "percentage" ? "percentages" : "absolute values"
      }`
    )
  );
}

// Show monthly trend of resource utilization
function showMonthlyTrend(report) {
  if (!report.data || !report.data.length) {
    frappe.msgprint(__("No data available to display"));
    return;
  }

  // Force group by month if not already
  if (frappe.query_report.get_filter_value("group_by") !== "Month") {
    frappe.query_report.set_filter_value("group_by", "Month");
    frappe.query_report.refresh();
    return;
  }

  let data = report.data;
  let labels = [];
  let totalValues = [];
  let laborRatios = [];
  let materialRatios = [];
  let equipmentRatios = [];

  // Extract data for the trend chart
  data.forEach((d) => {
    labels.push(d.month || d.period);
    totalValues.push(d.total_cost || 0);
    laborRatios.push(d.labor_percentage || 0);
    materialRatios.push(d.material_percentage || 0);
    equipmentRatios.push(d.equipment_percentage || 0);
  });

  // Create chart data
  let chartData = {
    labels: labels,
    datasets: [
      {
        name: "Total Cost",
        values: totalValues,
        chartType: "bar",
      },
      {
        name: "Labor %",
        values: laborRatios,
        chartType: "line",
      },
      {
        name: "Material %",
        values: materialRatios,
        chartType: "line",
      },
      {
        name: "Equipment %",
        values: equipmentRatios,
        chartType: "line",
      },
    ],
  };

  // Render the chart
  frappe.query_report.render_chart({
    type: "axis-mixed",
    title: "Monthly Resource Utilization Trend",
    data: chartData,
    height: 300,
    colors: ["#FF5858", "#5EC962", "#7B6CFF", "#FFA00A"],
    axisOptions: {
      xIsSeries: 1,
    },
    tooltipOptions: {
      formatTooltipY: (d, i, dataset) => {
        if (dataset.name === "Total Cost") {
          return frappe.format(d, { fieldtype: "Currency" });
        } else {
          return d.toFixed(1) + "%";
        }
      },
    },
  });

  frappe.msgprint(__("Showing monthly trend of resource utilization"));
}

// Show resource utilization summary
function showResourceSummary(report) {
  if (!report.data || !report.data.length) {
    frappe.msgprint(__("No data available for summary"));
    return;
  }

  let data = report.data;

  // Calculate totals
  let totalCost = 0;
  let totalLabor = 0;
  let totalMaterial = 0;
  let totalEquipment = 0;
  let totalSupervision = 0;

  data.forEach((d) => {
    totalCost += d.total_cost || 0;
    totalLabor += d.labor_cost || 0;
    totalMaterial += d.material_cost || 0;
    totalEquipment += d.equipment_cost || 0;
    totalSupervision += d.supervision_cost || 0;
  });

  // Calculate percentages
  const laborPercentage = ((totalLabor / totalCost) * 100).toFixed(2);
  const materialPercentage = ((totalMaterial / totalCost) * 100).toFixed(2);
  const equipmentPercentage = ((totalEquipment / totalCost) * 100).toFixed(2);
  const supervisionPercentage = ((totalSupervision / totalCost) * 100).toFixed(
    2
  );

  // Find the highest resource utilization
  const resources = [
    { name: "Labor", cost: totalLabor, percentage: laborPercentage },
    { name: "Material", cost: totalMaterial, percentage: materialPercentage },
    {
      name: "Equipment",
      cost: totalEquipment,
      percentage: equipmentPercentage,
    },
    {
      name: "Supervision",
      cost: totalSupervision,
      percentage: supervisionPercentage,
    },
  ];

  const highestResource = resources.reduce((prev, current) =>
    prev.cost > current.cost ? prev : current
  );

  // Create a message with an embedded chart
  const message = `
	  <div style="text-align: center; padding: 15px;">
		<h3>Resource Utilization Summary</h3>
		
		<div style="margin: 20px 0;">
		  <div id="resource_summary_chart" style="height: 200px;"></div>
		</div>
		
		<div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
		  <div style="text-align: left; width: 50%;">Total Cost:</div>
		  <div style="text-align: right; width: 50%;">${frappe.format(totalCost, {
        fieldtype: "Currency",
      })}</div>
		</div>
		
		<div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
		  <div style="text-align: left; width: 50%;">Labor Cost (${laborPercentage}%):</div>
		  <div style="text-align: right; width: 50%;">${frappe.format(totalLabor, {
        fieldtype: "Currency",
      })}</div>
		</div>
		
		<div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
		  <div style="text-align: left; width: 50%;">Material Cost (${materialPercentage}%):</div>
		  <div style="text-align: right; width: 50%;">${frappe.format(totalMaterial, {
        fieldtype: "Currency",
      })}</div>
		</div>
		
		<div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
		  <div style="text-align: left; width: 50%;">Equipment Cost (${equipmentPercentage}%):</div>
		  <div style="text-align: right; width: 50%;">${frappe.format(totalEquipment, {
        fieldtype: "Currency",
      })}</div>
		</div>
		
		<div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
		  <div style="text-align: left; width: 50%;">Supervision Cost (${supervisionPercentage}%):</div>
		  <div style="text-align: right; width: 50%;">${frappe.format(
        totalSupervision,
        { fieldtype: "Currency" }
      )}</div>
		</div>
		
		<div style="background-color: #f8f8f8; padding: 10px; border-radius: 5px;">
		  <strong>Key Insight:</strong> ${
        highestResource.name
      } represents the highest cost category at ${
    highestResource.percentage
  }% of total costs.
		</div>
	  </div>
	`;

  frappe.msgprint({
    title: __("Resource Utilization Summary"),
    indicator: "blue",
    message: message,
    wide: true,
  });

  // Render a donut chart inside the message
  setTimeout(() => {
    if (document.getElementById("resource_summary_chart")) {
      new frappe.Chart("#resource_summary_chart", {
        title: "Resource Distribution",
        data: {
          labels: ["Labor", "Material", "Equipment", "Supervision"],
          datasets: [
            {
              values: [
                parseFloat(laborPercentage),
                parseFloat(materialPercentage),
                parseFloat(equipmentPercentage),
                parseFloat(supervisionPercentage),
              ],
            },
          ],
        },
        type: "donut",
        colors: ["#5EC962", "#7B6CFF", "#FFA00A", "#00BCD4"],
        tooltipOptions: {
          formatTooltipY: (d) => d.toFixed(1) + "%",
        },
      });
    }
  }, 100);
}

// Function to export chart as PNG (placeholder - actual implementation would depend on Frappe's capabilities)
function exportChart(report) {
  frappe.msgprint(
    __(
      "Chart export feature will download the current chart view as a PNG file."
    )
  );

  // In a real implementation, this would use Frappe's chart API to export the chart
  setTimeout(() => {
    // This is just a placeholder for the actual export functionality
    frappe.msgprint(__("Chart exported successfully!"));
  }, 1000);
}
