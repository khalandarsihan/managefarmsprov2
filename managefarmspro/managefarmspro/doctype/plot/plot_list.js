frappe.listview_settings["Plot"] = {
  hide_name_column: true,
  hide_name_filter: true,
  onload: function (listview) {
    // Hide the 'Add Plot' button
    listview.page.btn_primary.hide();
  },
  formatters: {
    maintenance_balance: function (value) {
      // Convert value to display with Rupee symbol
      const formattedValue = `₹${Math.abs(value).toLocaleString("en-IN")}`;

      if (value < 0) {
        return `<span style="color: red">-${formattedValue}</span>`;
      }
      return formattedValue;
    },
  },
};
