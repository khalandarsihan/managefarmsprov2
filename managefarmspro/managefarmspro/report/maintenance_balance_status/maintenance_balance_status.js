// Copyright (c) 2025, Khalandar Sihan and contributors
// For license information, please see license.txt

frappe.query_reports["Maintenance Balance Status"] = {
  filters: [
    {
      fieldname: "cluster",
      label: __("Cluster"),
      fieldtype: "Link",
      options: "Cluster",
      on_change: function () {
        let cluster = frappe.query_report.get_filter_value("cluster");
        if (!cluster) {
          frappe.query_report.set_filter_value("plot_location", "");
        }
        frappe.query_report.refresh();
      },
    },
    {
      fieldname: "plot_location",
      label: __("Location"),
      fieldtype: "Link",
      options: "Plot Location",
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
    },
    {
      fieldname: "customer",
      label: __("Customer"),
      fieldtype: "Link",
      options: "Customer",
    },
    {
      fieldname: "balance_threshold",
      label: __("Warning Threshold %"),
      fieldtype: "Percent",
      default: 20,
      description: __("Balance percentage below which to show warning"),
    },
    {
      fieldname: "sort_by",
      label: __("Sort By"),
      fieldtype: "Select",
      options:
        "Balance %: Low to High\nBalance %: High to Low\nCluster\nCustomer\nLocation",
      default: "Balance %: Low to High",
    },
  ],

  formatter: function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);

    if (column.fieldname == "balance_percentage") {
      if (data.balance_percentage < 0) {
        value =
          "<span style='color: white; background-color: #FF5252; padding: 4px 8px; border-radius: 4px; display: inline-block; width: 100%; text-align: center;'>" +
          value +
          "</span>";
      } else if (data.balance_percentage < data.warning_threshold) {
        value =
          "<span style='color: white; background-color: #FFC107; padding: 4px 8px; border-radius: 4px; display: inline-block; width: 100%; text-align: center;'>" +
          value +
          "</span>";
      } else {
        value =
          "<span style='color: white; background-color: #4CAF50; padding: 4px 8px; border-radius: 4px; display: inline-block; width: 100%; text-align: center;'>" +
          value +
          "</span>";
      }
    }

    if (column.fieldname == "maintenance_balance") {
      if (data.balance_percentage < 0) {
        value =
          "<span style='color: #FF5252; font-weight: bold;'>" +
          value +
          "</span>";
      } else if (data.balance_percentage < data.warning_threshold) {
        value =
          "<span style='color: #FFC107; font-weight: bold;'>" +
          value +
          "</span>";
      } else {
        value = "<span style='color: #4CAF50;'>" + value + "</span>";
      }
    }

    if (column.fieldname == "last_activity") {
      // Calculate the difference in days
      const lastActivityDate = data.last_activity
        ? new Date(data.last_activity)
        : null;
      if (lastActivityDate) {
        const today = new Date();
        const diffTime = Math.abs(today - lastActivityDate);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays > 60) {
          value = "<span style='color: #FF5252;'>" + value + "</span>";
        } else if (diffDays > 30) {
          value = "<span style='color: #FFC107;'>" + value + "</span>";
        }
      }
    }

    return value;
  },

  onload: function (report) {
    // Add custom buttons for visualization options
    report.page.add_inner_button(__("View as Heatmap"), function () {
      showHeatmap(report);
    });

    report.page.add_inner_button(__("View by Cluster"), function () {
      showClusterView(report);
    });

    report.page.add_inner_button(__("Risk Assessment"), function () {
      showRiskAssessment(report);
    });

    // Hide the Actions button
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
      $('.page-actions button:contains("Actions")').remove();
    }, 1000);
  },
};

// Function to show data as a color-coded heatmap
function showHeatmap(report) {
  if (!report.data || !report.data.length) {
    frappe.msgprint(__("No data available to display"));
    return;
  }

  // Sort data by balance percentage (ascending)
  let data = [...report.data].sort(
    (a, b) => a.balance_percentage - b.balance_percentage
  );

  // Create a grid layout for the heatmap
  let columns = 5; // Number of columns in the grid
  let rows = Math.ceil(data.length / columns);

  // Calculate cell dimensions
  let cellWidth = 100 / columns;

  // Create the heatmap grid
  let heatmapHtml = `
	  <div style="text-align: center; padding: 20px;">
		<h3>${__("Plot Maintenance Balance Heatmap")}</h3>
		<p>${__(
      "Color indicates balance status: Red (Deficit), Yellow (Warning), Green (Good)"
    )}</p>
		<div style="display: flex; flex-wrap: wrap; margin-top: 20px;">
	`;

  // Add cells to the grid
  data.forEach((plot) => {
    let cellColor = "#4CAF50"; // Green (good)

    if (plot.balance_percentage < 0) {
      cellColor = "#FF5252"; // Red (deficit)
    } else if (plot.balance_percentage < plot.warning_threshold) {
      cellColor = "#FFC107"; // Yellow (warning)
    }

    heatmapHtml += `
		<div style="width: ${cellWidth}%; padding: 5px; box-sizing: border-box;">
		  <div style="background-color: ${cellColor}; border-radius: 4px; padding: 10px; height: 100px; display: flex; flex-direction: column; justify-content: center; color: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
			<div style="font-weight: bold; font-size: 14px; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${plot.plot_name}">${plot.plot_name}</div>
			<div style="font-size: 12px;">${plot.cluster}</div>
			<div style="font-size: 16px; margin-top: 5px;">${plot.balance_percentage}%</div>
		  </div>
		</div>
	  `;
  });

  heatmapHtml += `
		</div>
		<div style="display: flex; justify-content: center; margin-top: 20px;">
		  <div style="display: flex; align-items: center; margin: 0 15px;">
			<div style="width: 20px; height: 20px; background-color: #FF5252; border-radius: 3px; margin-right: 5px;"></div>
			<span>${__("Deficit")}</span>
		  </div>
		  <div style="display: flex; align-items: center; margin: 0 15px;">
			<div style="width: 20px; height: 20px; background-color: #FFC107; border-radius: 3px; margin-right: 5px;"></div>
			<span>${__("Warning")}</span>
		  </div>
		  <div style="display: flex; align-items: center; margin: 0 15px;">
			<div style="width: 20px; height: 20px; background-color: #4CAF50; border-radius: 3px; margin-right: 5px;"></div>
			<span>${__("Good")}</span>
		  </div>
		</div>
	  </div>
	`;

  frappe.msgprint({
    title: __("Maintenance Balance Heatmap"),
    indicator: "blue",
    message: heatmapHtml,
    wide: true,
  });
}

// Function to show data grouped by cluster
function showClusterView(report) {
  if (!report.data || !report.data.length) {
    frappe.msgprint(__("No data available to display"));
    return;
  }

  // Group data by cluster
  let clusterGroups = {};
  report.data.forEach((plot) => {
    if (!clusterGroups[plot.cluster]) {
      clusterGroups[plot.cluster] = {
        plots: [],
        total_budget: 0,
        total_spent: 0,
        total_balance: 0,
      };
    }
    clusterGroups[plot.cluster].plots.push(plot);
    clusterGroups[plot.cluster].total_budget += plot.monthly_maintenance_budget;
    clusterGroups[plot.cluster].total_spent += plot.total_spent;
    clusterGroups[plot.cluster].total_balance += plot.maintenance_balance;
  });

  // Prepare data for the chart
  let labels = Object.keys(clusterGroups);
  let balanceData = labels.map(
    (cluster) => clusterGroups[cluster].total_balance
  );
  let balanceColors = balanceData.map((balance) =>
    balance < 0 ? "#FF5252" : "#4CAF50"
  );

  // Calculate overall statistics
  let totalPlots = report.data.length;
  let plotsInDeficit = report.data.filter(
    (plot) => plot.balance_percentage < 0
  ).length;
  let plotsInWarning = report.data.filter(
    (plot) =>
      plot.balance_percentage >= 0 &&
      plot.balance_percentage < plot.warning_threshold
  ).length;
  let plotsInGood = report.data.filter(
    (plot) => plot.balance_percentage >= plot.warning_threshold
  ).length;

  let warningThreshold =
    report.data.length > 0 ? report.data[0].warning_threshold : 20;

  // Create the cluster view
  let clusterViewHtml = `
	  <div style="padding: 20px;">
		<h3 style="text-align: center;">${__("Maintenance Balance by Cluster")}</h3>
		
		<div style="display: flex; justify-content: space-around; margin: 20px 0; text-align: center;">
		  <div style="background-color: #f8f8f8; padding: 15px; border-radius: 5px; width: 30%;">
			<div style="color: #FF5252; font-size: 24px; font-weight: bold;">${plotsInDeficit}</div>
			<div>${__("Plots in Deficit")}</div>
		  </div>
		  <div style="background-color: #f8f8f8; padding: 15px; border-radius: 5px; width: 30%;">
			<div style="color: #FFC107; font-size: 24px; font-weight: bold;">${plotsInWarning}</div>
			<div>${__("Plots Below")} ${warningThreshold}%</div>
		  </div>
		  <div style="background-color: #f8f8f8; padding: 15px; border-radius: 5px; width: 30%;">
			<div style="color: #4CAF50; font-size: 24px; font-weight: bold;">${plotsInGood}</div>
			<div>${__("Plots in Good Standing")}</div>
		  </div>
		</div>
		
		<div id="cluster_balance_chart" style="height: 250px; margin-bottom: 20px;"></div>
		
		<table class="table table-bordered">
		  <thead>
			<tr>
			  <th>${__("Cluster")}</th>
			  <th>${__("Total Plots")}</th>
			  <th>${__("In Deficit")}</th>
			  <th>${__("In Warning")}</th>
			  <th>${__("Budget")}</th>
			  <th>${__("Spent")}</th>
			  <th>${__("Balance")}</th>
			</tr>
		  </thead>
		  <tbody>
	`;

  labels.forEach((cluster) => {
    let clusterData = clusterGroups[cluster];
    let plotsInCluster = clusterData.plots.length;
    let clusterPlotsInDeficit = clusterData.plots.filter(
      (plot) => plot.balance_percentage < 0
    ).length;
    let clusterPlotsInWarning = clusterData.plots.filter(
      (plot) =>
        plot.balance_percentage >= 0 &&
        plot.balance_percentage < plot.warning_threshold
    ).length;
    let balanceColor =
      clusterData.total_balance < 0
        ? "#FF5252"
        : (clusterData.total_balance / clusterData.total_budget) * 100 <
          warningThreshold
        ? "#FFC107"
        : "#4CAF50";

    clusterViewHtml += `
		<tr>
		  <td><strong>${cluster}</strong></td>
		  <td>${plotsInCluster}</td>
		  <td style="color: #FF5252;">${clusterPlotsInDeficit}</td>
		  <td style="color: #FFC107;">${clusterPlotsInWarning}</td>
		  <td>${frappe.format(clusterData.total_budget, { fieldtype: "Currency" })}</td>
		  <td>${frappe.format(clusterData.total_spent, { fieldtype: "Currency" })}</td>
		  <td style="color: ${balanceColor}; font-weight: bold;">${frappe.format(
      clusterData.total_balance,
      { fieldtype: "Currency" }
    )}</td>
		</tr>
	  `;
  });

  clusterViewHtml += `
		  </tbody>
		</table>
	  </div>
	`;

  frappe.msgprint({
    title: __("Cluster View"),
    indicator: "blue",
    message: clusterViewHtml,
    wide: true,
  });

  // Render the chart after the dialog is shown
  setTimeout(() => {
    if (document.getElementById("cluster_balance_chart")) {
      new frappe.Chart("#cluster_balance_chart", {
        data: {
          labels: labels,
          datasets: [
            {
              name: __("Balance"),
              values: balanceData,
              chartType: "bar",
            },
          ],
        },
        type: "bar",
        colors: balanceColors,
        axisOptions: {
          xIsSeries: true,
        },
        tooltipOptions: {
          formatTooltipY: (value) =>
            frappe.format(value, { fieldtype: "Currency" }),
        },
      });
    }
  }, 100);
}

// Function to show risk assessment
// function showRiskAssessment(report) {
//   if (!report.data || !report.data.length) {
//     frappe.msgprint(__("No data available for risk assessment"));
//     return;
//   }

//   // Categorize plots by risk level
//   let highRiskPlots = report.data.filter((plot) => plot.balance_percentage < 0);
//   let mediumRiskPlots = report.data.filter(
//     (plot) =>
//       plot.balance_percentage >= 0 &&
//       plot.balance_percentage < plot.warning_threshold
//   );
//   let lowRiskPlots = report.data.filter(
//     (plot) => plot.balance_percentage >= plot.warning_threshold
//   );

//   // Calculate risk metrics
//   let totalBudget = report.data.reduce(
//     (sum, plot) => sum + plot.monthly_maintenance_budget,
//     0
//   );
//   let totalDeficit = highRiskPlots.reduce(
//     (sum, plot) => sum + plot.maintenance_balance,
//     0
//   );
//   let totalPlotsAtRisk = highRiskPlots.length + mediumRiskPlots.length;
//   let percentageAtRisk = (
//     (totalPlotsAtRisk / report.data.length) *
//     100
//   ).toFixed(1);

//   // Calculate forecast for plots running out of budget soon
//   let atRiskSoon = report.data.filter(
//     (plot) =>
//       plot.balance_percentage >= plot.warning_threshold &&
//       plot.balance_percentage < plot.warning_threshold * 1.5
//   ).length;

//   // Create the risk assessment view
//   let riskHtml = `
// 	  <div style="padding: 20px;">
// 		<h3 style="text-align: center;">${__("Maintenance Budget Risk Assessment")}</h3>

// 		<div style="display: flex; justify-content: space-around; margin: 20px 0; text-align: center;">
// 		  <div style="background-color: #ffebee; padding: 15px; border-radius: 5px; width: 30%;">
// 			<div style="color: #FF5252; font-size: 24px; font-weight: bold;">${
//         highRiskPlots.length
//       }</div>
// 			<div>${__("High Risk (Deficit)")}</div>
// 		  </div>
// 		  <div style="background-color: #fff8e1; padding: 15px; border-radius: 5px; width: 30%;">
// 			<div style="color: #FFC107; font-size: 24px; font-weight: bold;">${
//         mediumRiskPlots.length
//       }</div>
// 			<div>${__("Medium Risk (Warning)")}</div>
// 		  </div>
// 		  <div style="background-color: #e8f5e9; padding: 15px; border-radius: 5px; width: 30%;">
// 			<div style="color: #4CAF50; font-size: 24px; font-weight: bold;">${
//         lowRiskPlots.length
//       }</div>
// 			<div>${__("Low Risk (Good)")}</div>
// 		  </div>
// 		</div>

// 		<div style="background-color: #f8f8f8; padding: 20px; border-radius: 5px; margin: 20px 0;">
// 		  <h4>${__("Risk Overview")}</h4>
// 		  <ul>
// 			<li>${__(
//         "Total plots at risk"
//       )}: <strong>${totalPlotsAtRisk}</strong> (${percentageAtRisk}% ${__(
//     "of all plots"
//   )})</li>
// 			<li>${__("Total budget deficit")}: <strong>${frappe.format(
//     Math.abs(totalDeficit),
//     { fieldtype: "Currency" }
//   )}</strong></li>
// 			<li>${__("Additional plots at risk soon")}: <strong>${atRiskSoon}</strong></li>
// 		  </ul>
// 		</div>

// 		<div id="risk_distribution_chart" style="height: 250px; margin-bottom: 20px;"></div>

// 		<div style="margin-top: 20px;">
// 		  <h4>${__("High Risk Plots")}</h4>
// 		  ${
//         highRiskPlots.length > 0
//           ? `
// 			<table class="table table-bordered">
// 			  <thead>
// 				<tr>
// 				  <th>${__("Plot")}</th>
// 				  <th>${__("Cluster")}</th>
// 				  <th>${__("Customer")}</th>
// 				  <th>${__("Budget")}</th>
// 				  <th>${__("Spent")}</th>
// 				  <th>${__("Balance")}</th>
// 				  <th>${__("Balance %")}</th>
// 				</tr>
// 			  </thead>
// 			  <tbody>
// 				${highRiskPlots
//           .map(
//             (plot) => `
// 				  <tr>
// 					<td><strong>${plot.plot_name}</strong></td>
// 					<td>${plot.cluster}</td>
// 					<td>${plot.customer_name || ""}</td>
// 					<td>${frappe.format(plot.monthly_maintenance_budget, {
//             fieldtype: "Currency",
//           })}</td>
// 					<td>${frappe.format(plot.total_spent, { fieldtype: "Currency" })}</td>
// 					<td style="color: #FF5252; font-weight: bold;">${frappe.format(
//             plot.maintenance_balance,
//             { fieldtype: "Currency" }
//           )}</td>
// 					<td style="color: #FF5252; font-weight: bold;">${plot.balance_percentage}%</td>
// 				  </tr>
// 				`
//           )
//           .join("")}
// 			  </tbody>
// 			</table>
// 		  `
//           : `<p>${__("No high-risk plots found.")}</p>`
//       }
// 		</div>
// 	  </div>
// 	`;

//   frappe.msgprint({
//     title: __("Risk Assessment"),
//     indicator: "red",
//     message: riskHtml,
//     wide: true,
//   });

//   // Render the chart after the dialog is shown
//   setTimeout(() => {
//     if (document.getElementById("risk_distribution_chart")) {
//       new frappe.Chart("#risk_distribution_chart", {
//         data: {
//           labels: [__("High Risk"), __("Medium Risk"), __("Low Risk")],
//           datasets: [
//             {
//               values: [
//                 highRiskPlots.length,
//                 mediumRiskPlots.length,
//                 lowRiskPlots.length,
//               ],
//             },
//           ],
//         },
//         type: "percentage",
//         colors: ["#FF5252", "#FFC107", "#4CAF50"],
//         height: 220,
//         tooltipOptions: {
//           formatTooltipY: (value) => value + " " + __("plots"),
//         },
//       });
//     }
//   }, 100);
// }

// Function to show risk assessment with highly simplified table
function showRiskAssessment(report) {
  if (!report.data || !report.data.length) {
    frappe.msgprint(__("No data available for risk assessment"));
    return;
  }

  // Categorize plots by risk level
  let highRiskPlots = report.data.filter((plot) => plot.balance_percentage < 0);
  let mediumRiskPlots = report.data.filter(
    (plot) =>
      plot.balance_percentage >= 0 &&
      plot.balance_percentage < plot.warning_threshold
  );
  let lowRiskPlots = report.data.filter(
    (plot) => plot.balance_percentage >= plot.warning_threshold
  );

  // Calculate risk metrics
  let totalBudget = report.data.reduce(
    (sum, plot) => sum + plot.monthly_maintenance_budget,
    0
  );
  let totalDeficit = highRiskPlots.reduce(
    (sum, plot) => sum + plot.maintenance_balance,
    0
  );
  let totalPlotsAtRisk = highRiskPlots.length + mediumRiskPlots.length;
  let percentageAtRisk = (
    (totalPlotsAtRisk / report.data.length) *
    100
  ).toFixed(1);

  // Calculate forecast for plots running out of budget soon
  let atRiskSoon = report.data.filter(
    (plot) =>
      plot.balance_percentage >= plot.warning_threshold &&
      plot.balance_percentage < plot.warning_threshold * 1.5
  ).length;

  // Prepare high risk plots table rows in a simplified format
  let highRiskTableRows = "";

  if (highRiskPlots.length > 0) {
    highRiskPlots.forEach((plot) => {
      // Extremely truncated plot and cluster names to fit small screens
      const plotShortName =
        plot.plot_name.split("_").pop() || plot.plot_name.substring(0, 8);
      const clusterShort = plot.cluster ? plot.cluster.substring(0, 6) : "";

      highRiskTableRows += `
		  <tr>
			<td title="${
        plot.plot_name
      }" style="max-width: 70px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"><strong>${plotShortName}</strong></td>
			<td title="${
        plot.cluster || ""
      }" style="max-width: 50px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${clusterShort}</td>
			<td style="text-align: right; padding-right: 5px;">${frappe.format(
        plot.monthly_maintenance_budget,
        { fieldtype: "Currency", decimals: 0 }
      )}</td>
			<td style="text-align: right; padding-right: 5px;">${frappe.format(
        plot.total_spent,
        { fieldtype: "Currency", decimals: 0 }
      )}</td>
			<td style="color: #FF5252; font-weight: bold; text-align: right;">${plot.balance_percentage.toFixed(
        1
      )}%</td>
		  </tr>
		`;
    });
  }

  // Create the risk assessment view with minimal table
  let riskHtml = `
	  <div style="padding: 10px; max-width: 100%;">
		<h3 style="text-align: center;">${__("Maintenance Budget Risk Assessment")}</h3>
		
		<div style="display: flex; justify-content: space-around; margin: 15px 0; text-align: center;">
		  <div style="background-color: #ffebee; padding: 10px; border-radius: 5px; width: 30%;">
			<div style="color: #FF5252; font-size: 24px; font-weight: bold;">${
        highRiskPlots.length
      }</div>
			<div>${__("High Risk")}</div>
		  </div>
		  <div style="background-color: #fff8e1; padding: 10px; border-radius: 5px; width: 30%;">
			<div style="color: #FFC107; font-size: 24px; font-weight: bold;">${
        mediumRiskPlots.length
      }</div>
			<div>${__("Medium Risk")}</div>
		  </div>
		  <div style="background-color: #e8f5e9; padding: 10px; border-radius: 5px; width: 30%;">
			<div style="color: #4CAF50; font-size: 24px; font-weight: bold;">${
        lowRiskPlots.length
      }</div>
			<div>${__("Low Risk")}</div>
		  </div>
		</div>
		
		<div style="background-color: #f8f8f8; padding: 15px; border-radius: 5px; margin: 15px 0;">
		  <h4>${__("Risk Overview")}</h4>
		  <ul style="padding-left: 20px; margin: 5px 0;">
			<li>${__(
        "Total plots at risk"
      )}: <strong>${totalPlotsAtRisk}</strong> (${percentageAtRisk}% ${__(
    "of all plots"
  )})</li>
			<li>${__("Total budget deficit")}: <strong>${frappe.format(
    Math.abs(totalDeficit),
    { fieldtype: "Currency" }
  )}</strong></li>
			<li>${__("Additional plots at risk soon")}: <strong>${atRiskSoon}</strong></li>
		  </ul>
		</div>
		
		<div id="risk_distribution_chart" style="height: 180px; margin-bottom: 15px;"></div>
		
		<div style="margin-top: 15px;">
		  <h4>${__("High Risk Plots")}</h4>
		  ${
        highRiskPlots.length > 0
          ? `
			<div style="margin-top: 10px;">
			  <table class="table table-bordered" style="width: 100%; table-layout: fixed; margin-bottom: 0; font-size: 12px;">
				<thead>
				  <tr>
					<th style="width: 20%;">${__("Plot")}</th>
					<th style="width: 15%;">${__("Cluster")}</th>
					<th style="width: 20%;">${__("Budget")}</th>
					<th style="width: 20%;">${__("Spent")}</th>
					<th style="width: 15%;">${__("Bal. %")}</th>
				  </tr>
				</thead>
				<tbody>
				  ${highRiskTableRows}
				</tbody>
			  </table>
			</div>
		  `
          : `<p>${__("No high-risk plots found.")}</p>`
      }
		</div>
	  </div>
	`;

  frappe.msgprint({
    title: __("Risk Assessment"),
    indicator: "red",
    message: riskHtml,
    wide: true,
  });

  // Render the chart after the dialog is shown
  setTimeout(() => {
    if (document.getElementById("risk_distribution_chart")) {
      new frappe.Chart("#risk_distribution_chart", {
        data: {
          labels: [__("High Risk"), __("Medium Risk"), __("Low Risk")],
          datasets: [
            {
              values: [
                highRiskPlots.length,
                mediumRiskPlots.length,
                lowRiskPlots.length,
              ],
            },
          ],
        },
        type: "percentage",
        colors: ["#FF5252", "#FFC107", "#4CAF50"],
        height: 180,
        tooltipOptions: {
          formatTooltipY: (value) => value + " " + __("plots"),
        },
      });
    }
  }, 100);
}
