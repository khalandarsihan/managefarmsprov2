frappe.ui.form.on("Sales Invoice", {
  refresh(frm) {
    setTimeout(() => {
      // Hide the entire 'Create' button container
      $('div[data-label="Create"]').hide();
      // Optionally: Hide the 'View' button container if needed
      $('div[data-label="View"]').hide();
    }, 500); // Small timeout to ensure the buttons are rendered first
  },

  onload_post_render: function (frm) {
    // Use jQuery to hide the Download button based on its class
    $("button.grid-download").hide();
  },

  after_save: function (frm) {
    // Automatically refresh the form to reflect the newly created invoice
    frappe.show_alert({
      message: __("New Sales Invoice created successfully!"),
      indicator: "green",
    });
    location.reload();
  },
});
