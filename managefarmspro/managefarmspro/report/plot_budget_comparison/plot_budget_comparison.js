// Copyright (c) 2025, Khalandar Sihan and contributors
// For license information, please see license.txt

frappe.query_reports["Plot Budget Comparison"] = {
  filters: [
    {
      fieldname: "cluster",
      label: __("Cluster"),
      fieldtype: "Link",
      options: "Cluster",
      width: "80",
    },
    {
      fieldname: "plot_location",
      label: __("Location"),
      fieldtype: "Link",
      options: "Plot Location",
      width: "80",
    },
    {
      fieldname: "limit",
      label: __("Number of Plots"),
      fieldtype: "Int",
      default: 10,
      min: 5,
      max: 50,
      width: "80",
    },
    {
      fieldname: "sort_by",
      label: __("Sort By"),
      fieldtype: "Select",
      options:
        "Budget: High to Low\nBudget: Low to High\nSpent: High to Low\nSpent: Low to High\nBalance: High to Low\nBalance: Low to High",
      default: "Budget: High to Low",
      width: "120",
    },
  ],

  formatter: function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);

    if (column.fieldname == "balance") {
      if (data.balance < 0) {
        value = "<span style='color: red'>" + value + "</span>";
      } else if (data.balance < data.monthly_maintenance_budget * 0.2) {
        value = "<span style='color: orange'>" + value + "</span>";
      } else {
        value = "<span style='color: green'>" + value + "</span>";
      }
    }

    if (column.fieldname == "total_amount_spent") {
      if (data.total_amount_spent > data.monthly_maintenance_budget) {
        value = "<span style='color: red'>" + value + "</span>";
      }
    }

    return value;
  },

  onload: function (report) {
    report.page.add_inner_button(__("View as Percentage"), function () {
      updateChartToPercentage(report);
    });

    report.page.add_inner_button(__("Add Balance to Chart"), function () {
      addBalanceToChart(report);
    });

    report.page.add_inner_button(__("Export as PNG"), function () {
      exportChartAsPNG(report);
    });
  },
};

// These functions use Frappe's own chart API instead of trying to access the chart object directly
function updateChartToPercentage(report) {
  if (!report.data || !report.data.length) {
    frappe.msgprint(__("No data available to display"));
    return;
  }

  let data = report.data;

  // Calculate percentages
  let labels = data.map((d) => d.plot_name);
  let percentages = data.map((d) => {
    return parseFloat(
      ((d.total_amount_spent / d.monthly_maintenance_budget) * 100).toFixed(1)
    );
  });

  // Create a new chart configuration
  let chart_data = {
    labels: labels,
    datasets: [
      {
        name: __("Spent %"),
        values: percentages,
      },
    ],
  };

  let chart_options = {
    height: 280,
    colors: ["#FF5722"],
    axisOptions: {
      yAxisMode: "tick",
      xIsSeries: true,
    },
    tooltipOptions: {
      formatTooltipY: (d) => d + "%",
    },
    markers: [
      {
        label: __("100% Budget"),
        value: 100,
        options: { labelPos: "right" },
      },
    ],
  };

  // Use Frappe's method to render the chart
  frappe.query_report.render_chart({
    type: "bar",
    data: chart_data,
    ...chart_options,
  });

  frappe.msgprint(__("Showing budget utilization as percentages"));
}

function addBalanceToChart(report) {
  if (!report.data || !report.data.length) {
    frappe.msgprint(__("No data available to display"));
    return;
  }

  let data = report.data;

  // Create the chart data with the original datasets plus balance
  let chart_data = {
    labels: data.map((d) => d.plot_name),
    datasets: [
      {
        name: __("Budget"),
        values: data.map((d) => d.monthly_maintenance_budget),
      },
      {
        name: __("Spent"),
        values: data.map((d) => d.total_amount_spent),
      },
      {
        name: __("Balance"),
        values: data.map((d) => d.balance),
        chartType: "line",
      },
    ],
  };

  // Render the chart with the additional dataset
  frappe.query_report.render_chart({
    type: "axis-mixed",
    data: chart_data,
    height: 280,
    colors: ["#4CAF50", "#FF5722", "#2196F3"],
  });

  frappe.msgprint(__("Added balance line to chart"));
}

// Add buttons to the report
frappe.query_reports["Plot Budget Comparison"].onload = function (report) {
  report.page.add_inner_button(__("View as Percentage"), function () {
    updateChartToPercentage(report);
  });

  report.page.add_inner_button(__("Show Balance Line"), function () {
    addBalanceToChart(report);
  });

  // Add Budget Utilization Summary button directly
  report.page.add_inner_button(__("Budget Utilization Summary"), function () {
    showBudgetUtilizationSummary(report);
  });

  // Hide the Actions button that comes by default
  setTimeout(function () {
    $('.btn:contains("Actions")').hide();
  }, 300);
};

// Function to show budget utilization summary
function showBudgetUtilizationSummary(report) {
  if (!report.data || !report.data.length) {
    frappe.msgprint(__("No data available for summary"));
    return;
  }

  let data = report.data;
  let total_budget = 0;
  let total_spent = 0;

  data.forEach((d) => {
    total_budget += d.monthly_maintenance_budget;
    total_spent += d.total_amount_spent;
  });

  let utilization = ((total_spent / total_budget) * 100).toFixed(2);
  let message = `
		<div style="text-align: center; padding: 15px;">
			<h3>Budget Utilization Summary</h3>
			<div style="font-size: 24px; margin: 20px 0;">
				<span style="color: ${
          utilization > 100 ? "red" : utilization > 80 ? "orange" : "green"
        }">
					${utilization}%
				</span>
			</div>
			<div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
				<div style="text-align: left; width: 50%;">Total Budget:</div>
				<div style="text-align: right; width: 50%;">${frappe.format(total_budget, {
          fieldtype: "Currency",
        })}</div>
			</div>
			<div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
				<div style="text-align: left; width: 50%;">Total Spent:</div>
				<div style="text-align: right; width: 50%;">${frappe.format(total_spent, {
          fieldtype: "Currency",
        })}</div>
			</div>
			<div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
				<div style="text-align: left; width: 50%;">Remaining:</div>
				<div style="text-align: right; width: 50%;">${frappe.format(
          total_budget - total_spent,
          { fieldtype: "Currency" }
        )}</div>
			</div>
		</div>
	`;

  frappe.msgprint({
    title: __("Budget Utilization"),
    indicator:
      utilization > 100 ? "red" : utilization > 80 ? "orange" : "green",
    message: message,
  });
}
