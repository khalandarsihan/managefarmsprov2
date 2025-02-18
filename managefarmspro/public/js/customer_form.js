// managefarmspro/managefarmspro/public/js/customer_customizations.js

frappe.provide("managefarmspro.customer");

// List view settings
frappe.listview_settings["Customer"] = {
  hide_name_column: true,
  hide_name_filter: true,
};

// Define the toggle function outside
function toggle_partners_tab(frm) {
  // If customer_type is Partnership, show the Partners tab
  if (frm.doc.customer_type === "Partnership") {
    $('[data-fieldname="custom_partners"]').show();
  } else {
    // Otherwise, hide the Partners tab
    $('[data-fieldname="custom_partners"]').hide();
  }
}

// Form customizations
frappe.ui.form.on("Customer", {
  setup: function (frm) {
    // Remove quick entry fields for contact and address
    if (frm.meta.quick_entry) {
      frm.meta.fields = frm.meta.fields.filter(
        (field) =>
          ![
            "address_contacts",
            "contact_and_address_tab",
            "customer_primary_contact",
            "customer_primary_address",
          ].includes(field.fieldname)
      );
    }
  },

  refresh: function (frm) {
    // Hide standard buttons
    frm.page.clear_custom_actions();
    frm.page.remove_inner_button("Create");
    frm.page.remove_inner_button("Actions");

    // Call the function when the form is refreshed
    toggle_partners_tab(frm);

    // Align connections horizontally
    frappe.after_ajax(() => {
      managefarmspro.customer.align_connections();
    });
  },

  customer_type: function (frm) {
    // Call the function whenever customer_type is changed
    toggle_partners_tab(frm);
  },
});

// Utility functions
managefarmspro.customer = {
  align_connections: function () {
    const connectionsColumn = document.querySelector(
      ".form-dashboard-section .col-md-4"
    );
    if (connectionsColumn) {
      // Reset existing classes and add new layout
      connectionsColumn.className = "col-md-12";

      // Apply styles
      Object.assign(connectionsColumn.style, {
        display: "flex",
        flexWrap: "nowrap",
        alignItems: "center",
        justifyContent: "flex-start",
        flexDirection: "row",
      });

      // Style connection items
      connectionsColumn.querySelectorAll(".document-link").forEach((item) => {
        Object.assign(item.style, {
          marginRight: "15px",
          flex: "0 0 auto",
        });
      });
    }
  },
};
