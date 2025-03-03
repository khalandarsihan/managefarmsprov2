app_name = "managefarmspro"
app_title = "ManageFarmsPro"
app_publisher = "Khalandar Sihan"
app_description = "Farm Management App"
app_email = "khasihanai@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "managefarmspro",
# 		"logo": "/assets/managefarmspro/logo.png",
# 		"title": "ManageFarmsPro",
# 		"route": "/managefarmspro",
# 		"has_permission": "managefarmspro.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/managefarmspro/css/managefarmspro.css"
# app_include_js = "/assets/managefarmspro/js/managefarmspro.js"
app_include_js = [
    "/assets/managefarmspro/js/customer_list.js",
    "/assets/managefarmspro/js/customer_form.js",
    "/assets/managefarmspro/js/sales_invoice_form.js"
]

# include js, css files in header of web template
# web_include_css = "/assets/managefarmspro/css/managefarmspro.css"
# web_include_js = "/assets/managefarmspro/js/managefarmspro.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "managefarmspro/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_js = {
#     "Customer": [
#         "/public/js/customer_list.js",
#         "/public/js/customer_form.js"
#     ]
# }

doctype_js = {
    "Customer": [
        "/public/js/customer_list.js",
        "/public/js/customer_form.js"
    ],
    "Sales Invoice": [
        "/public/js/sales_invoice_form.js"  # Add this section
    ]
}


# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "managefarmspro/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "managefarmspro.utils.jinja_methods",
# 	"filters": "managefarmspro.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "managefarmspro.install.before_install"
# after_install = "managefarmspro.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "managefarmspro.uninstall.before_uninstall"
# after_uninstall = "managefarmspro.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "managefarmspro.utils.before_app_install"
# after_app_install = "managefarmspro.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "managefarmspro.utils.before_app_uninstall"
# after_app_uninstall = "managefarmspro.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "managefarmspro.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

doc_events = {
    "Customer": {
        "refresh": "managefarmspro.customer_customizations.on_customer_refresh"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"managefarmspro.tasks.all"
# 	],
# 	"daily": [
# 		"managefarmspro.tasks.daily"
# 	],
# 	"hourly": [
# 		"managefarmspro.tasks.hourly"
# 	],
# 	"weekly": [
# 		"managefarmspro.tasks.weekly"
# 	],
# 	"monthly": [
# 		"managefarmspro.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "managefarmspro.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "managefarmspro.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "managefarmspro.task.get_dashboard_data"
# }

# override_doctype_dashboards = {
# 	"Customer": "managefarmspro.overrides.customer_dashboard.get_dashboard_data"
# }

override_doctype_dashboards = {
	"Customer": "managefarmspro.overrides.customer_dashboard.get_dashboard_data",
	"Sales Invoice": "managefarmspro.overrides.sales_invoice_dashboard.get_dashboard_data"
}


# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["managefarmspro.utils.before_request"]
# after_request = ["managefarmspro.utils.after_request"]

# Job Events
# ----------
# before_job = ["managefarmspro.utils.before_job"]
# after_job = ["managefarmspro.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"managefarmspro.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            ["dt", "in", ["Customer", "Sales Invoice", "Sales Invoice Item"]]
        ]
    }
]

# fixtures = [
#     # Your existing fixtures
#     {
#         "dt": "Custom Field",
#         "filters": [
#             ["dt", "in", ["Customer", "Sales Invoice", "Sales Invoice Item"]]
#         ]
#     },
#     # Update workspace filter
#     {
#         "dt": "Workspace",
#         "filters": [
#             ["name", "=", "ManageFarmsPro"]
#         ]
#     },
#     # Update dashboard filter
#     {
#         "dt": "Dashboard",
#         "filters": [
#             ["module", "=", "ManageFarmsPro"],
#             ["is_standard", "=", 1]  # Only non-standard dashboards
#         ]
#     },
#     # Update dashboard chart filter
#     {
#         "dt": "Dashboard Chart",
#         "filters": [
#             ["module", "=", "ManageFarmsPro"],
#             ["is_standard", "=", 1]  # Only non-standard charts
#         ]
#     },
#     # Update number card filter
#     {
#         "dt": "Number Card",
#         "filters": [
#             ["module", "=", "ManageFarmsPro"],
#             ["is_standard", "=", 1]  # Only non-standard cards
#         ]
#     }
# ]

# fixtures = [
#     # Core fixtures for custom fields
#     {
#         "dt": "Custom Field",
#         "filters": [
#             ["dt", "in", ["Customer", "Sales Invoice", "Sales Invoice Item"]]
#         ]
#     },
#     # Make sure to include ALL workspace components
#     {
#         "dt": "Workspace",
#         "filters": [
#             ["name", "=", "ManageFarmsPro"]
#         ]
#     },
#     # Dashboard
#     {
#         "dt": "Dashboard",
#         "filters": [
#             ["name", "=", "ManageFarmsPro"]  # Change to filter by name instead of module
#         ]
#     },
#     # Dashboard charts - ensure we get all of them
#     {
#         "dt": "Dashboard Chart",
#         "filters": [
#             ["module", "=", "Managefarmspro"]
#         ]
#     },
#     # Number cards
#     {
#         "dt": "Number Card",
#         "filters": [
#             ["module", "=", "Managefarmspro"]
#         ]
#     },
#     # Include links between these components
#     {
#         "dt": "Dashboard Chart Link",
#         "filters": [
#             ["parent", "=", "ManageFarmsPro"]
#         ]
#     },
#     {
#         "dt": "Number Card Link",
#         "filters": [
#             ["parent", "=", "ManageFarmsPro"]
#         ]
#     }
# ]
